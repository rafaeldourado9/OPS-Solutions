/**
 * WhatsApp client wrapper using Baileys.
 *
 * Handles:
 * - QR code authentication with session persistence
 * - Incoming message processing and webhook forwarding
 * - Media download from incoming messages (embedded as base64)
 * - Outbound message sending (text, image, audio, video, documents)
 * - Typing indicators (presence updates)
 * - Auto-reconnect on disconnect
 */

const {
  default: makeWASocket,
  useMultiFileAuthState,
  makeCacheableSignalKeyStore,
  fetchLatestBaileysVersion,
  DisconnectReason,
  downloadMediaMessage,
  getContentType,
  proto,
} = require("@whiskeysockets/baileys");
const path = require("path");
const fs = require("fs");
const qrcode = require("qrcode-terminal");

// QR_TTL_MS — QR codes expire after ~60s
const QR_TTL_MS = 60000;

/**
 * Create and return a WhatsApp client instance.
 *
 * @param {Object} opts
 * @param {string} opts.sessionName
 * @param {string} opts.authDir
 * @param {string} opts.webhookUrl
 * @param {Object} opts.logger - pino logger
 */
async function createWhatsAppClient({ sessionName, authDir, webhookUrl, logger }) {
  const authPath = path.join(authDir, sessionName);
  if (!fs.existsSync(authPath)) {
    fs.mkdirSync(authPath, { recursive: true });
  }

  let sock = null;
  let connected = false;
  let phoneNumber = null;
  let reconnectAttempts = 0;
  const MAX_RECONNECT_DELAY = 60000;

  // Per-session QR state
  let _currentQr = null;
  let _qrReceivedAt = null;

  // Media buffer: store downloaded media bytes for recent messages
  // Key: message ID, Value: { data: Buffer, mimetype: string, filename: string }
  const mediaCache = new Map();
  const MEDIA_CACHE_TTL = 5 * 60 * 1000; // 5 minutes

  function cleanMediaCache() {
    const now = Date.now();
    for (const [key, val] of mediaCache) {
      if (now - val.timestamp > MEDIA_CACHE_TTL) {
        mediaCache.delete(key);
      }
    }
  }
  setInterval(cleanMediaCache, 60 * 1000);

  async function connect() {
    const { state, saveCreds } = await useMultiFileAuthState(authPath);
    const { version } = await fetchLatestBaileysVersion();
    const baileysLogger = require("pino")({ level: "silent" });

    logger.info({ version }, "Using WA version");

    sock = makeWASocket({
      auth: {
        creds: state.creds,
        keys: makeCacheableSignalKeyStore(state.keys, baileysLogger),
      },
      version,
      logger: baileysLogger,
      browser: ["Ubuntu", "Chrome", "20.0.04"],
      markOnlineOnConnect: true,
      syncFullHistory: false,
      connectTimeoutMs: 60000,
    });

    sock.ev.on("creds.update", saveCreds);

    sock.ev.on("connection.update", (update) => {
      const { connection, lastDisconnect, qr } = update;

      if (qr) {
        _currentQr = qr;
        _qrReceivedAt = Date.now();
        logger.info("QR Code received — scan with WhatsApp:");
        qrcode.generate(qr, { small: true });
      }

      if (connection === "close") {
        connected = false;
        const statusCode =
          lastDisconnect?.error?.output?.statusCode || 0;
        const shouldReconnect = statusCode !== DisconnectReason.loggedOut;

        logger.warn(
          { statusCode, shouldReconnect },
          "Connection closed"
        );

        if (shouldReconnect) {
          reconnectAttempts++;
          const delay = Math.min(3000 * Math.pow(2, reconnectAttempts - 1), MAX_RECONNECT_DELAY);
          logger.info({ delay, attempt: reconnectAttempts }, "Reconnecting...");
          setTimeout(() => connect(), delay);
        } else {
          logger.error("Logged out — delete auth folder and restart to re-authenticate");
        }
      }

      if (connection === "open") {
        connected = true;
        reconnectAttempts = 0;
        phoneNumber = sock.user?.id?.split(":")[0] || null;
        _currentQr = null;
        _qrReceivedAt = null;
        logger.info({ phone: phoneNumber }, "WhatsApp connected!");
      }
    });

    // Handle incoming messages
    sock.ev.on("messages.upsert", async ({ messages, type }) => {
      if (type !== "notify") return;

      for (const msg of messages) {
        try {
          await handleIncomingMessage(msg);
        } catch (err) {
          logger.error({ err, msgId: msg.key?.id }, "Error handling incoming message");
        }
      }
    });
  }

  async function handleIncomingMessage(msg) {
    const key = msg.key;
    if (!key?.remoteJid) return;

    // Build WAHA-compatible payload
    const chatId = key.remoteJid;
    const fromMe = key.fromMe || false;
    const msgId = key.id || "";

    // Detect message content type
    const contentType = getContentType(msg.message);
    if (!contentType) return;

    const content = msg.message[contentType];

    // Extract text body
    let body = "";
    let caption = "";
    let hasMedia = false;
    let mediaData = null;
    let mimetype = "";
    let filename = "";
    let msgType = "chat";

    switch (contentType) {
      case "conversation":
        body = msg.message.conversation || "";
        msgType = "chat";
        break;

      case "extendedTextMessage":
        body = content?.text || "";
        msgType = "chat";
        break;

      case "imageMessage":
        hasMedia = true;
        mimetype = content?.mimetype || "image/jpeg";
        caption = content?.caption || "";
        body = caption;
        msgType = "image";
        break;

      case "videoMessage":
        hasMedia = true;
        mimetype = content?.mimetype || "video/mp4";
        caption = content?.caption || "";
        body = caption;
        msgType = "video";
        break;

      case "audioMessage":
        hasMedia = true;
        mimetype = content?.mimetype || "audio/ogg; codecs=opus";
        msgType = content?.ptt ? "ptt" : "audio";
        break;

      case "documentMessage":
        hasMedia = true;
        mimetype = content?.mimetype || "application/octet-stream";
        filename = content?.fileName || "document";
        caption = content?.caption || "";
        body = caption;
        msgType = "document";
        break;

      case "stickerMessage":
        hasMedia = true;
        mimetype = content?.mimetype || "image/webp";
        msgType = "sticker";
        break;

      case "contactMessage":
      case "contactsArrayMessage":
        body = content?.displayName || "[Contact]";
        msgType = "chat";
        break;

      case "locationMessage":
        body = `[Location: ${content?.degreesLatitude}, ${content?.degreesLongitude}]`;
        msgType = "chat";
        break;

      default:
        // Try to extract text from unknown types
        if (typeof content === "string") {
          body = content;
        } else if (content?.text) {
          body = content.text;
        } else if (content?.caption) {
          body = content.caption;
        }
        break;
    }

    // Download media if present
    if (hasMedia && msg.message) {
      try {
        const buffer = await downloadMediaMessage(
          msg,
          "buffer",
          {},
          {
            logger: require("pino")({ level: "silent" }),
            reuploadRequest: sock.updateMediaMessage,
          }
        );
        if (buffer && buffer.length > 0) {
          mediaData = buffer.toString("base64");
          // Cache for later retrieval
          mediaCache.set(msgId, {
            data: buffer,
            mimetype,
            filename,
            timestamp: Date.now(),
          });
        }
      } catch (err) {
        logger.warn({ err: err.message, msgId }, "Failed to download media");
      }
    }

    // Build WAHA-compatible webhook payload
    const webhookPayload = {
      event: "message",
      session: sessionName,
      payload: {
        id: msgId,
        from: chatId,
        chatId: chatId,
        fromMe: fromMe,
        body: body,
        hasMedia: hasMedia,
        type: msgType,
        timestamp: msg.messageTimestamp
          ? parseInt(msg.messageTimestamp.toString())
          : Math.floor(Date.now() / 1000),
        ...(hasMedia && {
          caption: caption,
          media: {
            mimetype: mimetype,
            filename: filename || undefined,
            ...(mediaData && { data: mediaData }),
          },
        }),
      },
    };

    // Send to webhook
    try {
      const resp = await fetch(webhookUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(webhookPayload),
        signal: AbortSignal.timeout(10000),
      });
      if (!resp.ok) {
        logger.warn(
          { status: resp.status, msgId },
          "Webhook returned non-OK status"
        );
      }
    } catch (err) {
      logger.error({ err: err.message, msgId }, "Failed to send webhook");
    }
  }

  // --- Public API methods ---

  async function sendText(chatId, text) {
    if (!sock || !connected) throw new Error("Not connected");
    await sock.sendMessage(chatId, { text });
  }

  async function sendImage(chatId, imageBuffer, mimetype, filename, caption) {
    if (!sock || !connected) throw new Error("Not connected");
    await sock.sendMessage(chatId, {
      image: imageBuffer,
      mimetype: mimetype || "image/jpeg",
      caption: caption || undefined,
      fileName: filename || undefined,
    });
  }

  async function sendAudio(chatId, audioBuffer, mimetype, ptt = false) {
    if (!sock || !connected) throw new Error("Not connected");
    await sock.sendMessage(chatId, {
      audio: audioBuffer,
      mimetype: mimetype || "audio/mpeg",
      ptt: ptt,
    });
  }

  async function sendVideo(chatId, videoBuffer, mimetype, caption) {
    if (!sock || !connected) throw new Error("Not connected");
    await sock.sendMessage(chatId, {
      video: videoBuffer,
      mimetype: mimetype || "video/mp4",
      caption: caption || undefined,
    });
  }

  async function sendDocument(chatId, docBuffer, mimetype, filename, caption) {
    if (!sock || !connected) throw new Error("Not connected");
    await sock.sendMessage(chatId, {
      document: docBuffer,
      mimetype: mimetype || "application/octet-stream",
      fileName: filename || "document",
      caption: caption || undefined,
    });
  }

  async function sendFile(chatId, fileBuffer, mimetype, filename, caption) {
    // Route to appropriate sender based on MIME type
    const mime = (mimetype || "").toLowerCase();
    if (mime.startsWith("image/")) {
      return sendImage(chatId, fileBuffer, mimetype, filename, caption);
    }
    if (mime.startsWith("video/")) {
      return sendVideo(chatId, fileBuffer, mimetype, filename, caption);
    }
    if (mime.startsWith("audio/") || mime === "application/ogg") {
      const isPtt = mime.includes("ogg") || mime.includes("opus");
      return sendAudio(chatId, fileBuffer, mimetype, isPtt);
    }
    // Default: send as document
    return sendDocument(chatId, fileBuffer, mimetype, filename, caption);
  }

  async function sendVoice(chatId, audioBuffer, mimetype) {
    // Always send as PTT (push-to-talk) voice message
    if (!sock || !connected) throw new Error("Not connected");
    await sock.sendMessage(chatId, {
      audio: audioBuffer,
      mimetype: mimetype || "audio/ogg; codecs=opus",
      ptt: true,
    });
  }

  async function startTyping(chatId) {
    if (!sock || !connected) return;
    try {
      await sock.sendPresenceUpdate("composing", chatId);
    } catch (err) {
      logger.debug({ err: err.message }, "Failed to send composing presence");
    }
  }

  async function stopTyping(chatId) {
    if (!sock || !connected) return;
    try {
      await sock.sendPresenceUpdate("paused", chatId);
    } catch (err) {
      logger.debug({ err: err.message }, "Failed to send paused presence");
    }
  }

  async function startRecording(chatId) {
    if (!sock || !connected) return;
    try {
      await sock.sendPresenceUpdate("recording", chatId);
    } catch (err) {
      logger.debug({ err: err.message }, "Failed to send recording presence");
    }
  }

  async function stopRecording(chatId) {
    if (!sock || !connected) return;
    try {
      await sock.sendPresenceUpdate("paused", chatId);
    } catch (err) {
      logger.debug({ err: err.message }, "Failed to send paused presence");
    }
  }

  function getStatus() {
    return { connected, phone: phoneNumber };
  }

  function getQr() {
    // Return null if expired
    if (_currentQr && _qrReceivedAt && Date.now() - _qrReceivedAt > QR_TTL_MS) {
      _currentQr = null;
      _qrReceivedAt = null;
    }
    return { qr: _currentQr, receivedAt: _qrReceivedAt };
  }

  async function reconnect() {
    logger.info("Manual reconnect requested");
    reconnectAttempts = 0; // Reset backoff for fast reconnect
    _currentQr = null;
    _qrReceivedAt = null;
    connected = false;
    try {
      sock?.ws?.close();
    } catch (err) {
      logger.debug({ err: err.message }, "Socket close on reconnect");
    }
  }

  async function logout() {
    logger.info("Logout requested — clearing session");
    connected = false;
    phoneNumber = null;
    _currentQr = null;
    _qrReceivedAt = null;
    try {
      await sock?.logout();
    } catch (err) {
      logger.debug({ err: err.message }, "Baileys logout error (expected on logout)");
    }
    // Clear auth folder so next start shows a fresh QR
    try {
      fs.rmSync(authPath, { recursive: true, force: true });
      fs.mkdirSync(authPath, { recursive: true });
    } catch (err) {
      logger.warn({ err: err.message }, "Failed to clear auth folder");
    }
    // Reconnect to show QR
    reconnectAttempts = 0;
    setTimeout(() => connect(), 1000);
  }

  function getMediaFromCache(msgId) {
    return mediaCache.get(msgId) || null;
  }

  // Start connection
  await connect();

  return {
    sendText,
    sendImage,
    sendAudio,
    sendVideo,
    sendDocument,
    sendFile,
    sendVoice,
    startTyping,
    stopTyping,
    startRecording,
    stopRecording,
    getStatus,
    getQr,
    reconnect,
    logout,
    getMediaFromCache,
  };
}

module.exports = { createWhatsAppClient };
