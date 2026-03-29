/**
 * Express routes — Multi-session WAHA-compatible REST API.
 *
 * All send/control routes accept a `session` param (body or query).
 * If no session specified, uses the first active session (backwards compatible).
 *
 * Session management endpoints:
 *   GET    /api/sessions         — List all sessions
 *   POST   /api/sessions         — Create a new session
 *   DELETE /api/sessions/:name   — Remove a session
 *
 * Per-session endpoints (use ?session=xxx or body.session):
 *   POST /api/sendText, /api/sendFile, /api/sendVoice, etc.
 *   GET  /api/qr, /api/status
 *   POST /api/restart, /api/logout
 */

const express = require("express");

function createRoutes(sm, logger) {
  const router = express.Router();

  // Helper: resolve session client from request
  function getClient(req) {
    const name = req.body?.session || req.query?.session || null;
    return sm.getOrDefault(name);
  }

  function getClientStrict(req) {
    const name = req.body?.session || req.query?.session;
    if (!name) return { client: null, error: "session param required" };
    const client = sm.getSession(name);
    if (!client) return { client: null, error: `Session '${name}' not found` };
    return { client, error: null };
  }

  // ── Session Management ──────────────────────────────────────────────────

  // GET /api/sessions — List all sessions
  router.get("/sessions", (req, res) => {
    res.json(sm.listSessions());
  });

  // POST /api/sessions — Create a new session { name }
  router.post("/sessions", async (req, res) => {
    const { name } = req.body;
    if (!name) {
      return res.status(400).json({ error: "name required" });
    }
    if (sm.hasSession(name)) {
      return res.status(409).json({ error: "Session already exists", name });
    }
    try {
      await sm.createSession(name);
      res.status(201).json({ status: "created", name });
    } catch (err) {
      logger.error({ err: err.message, session: name }, "Failed to create session");
      res.status(500).json({ error: err.message });
    }
  });

  // DELETE /api/sessions/:name — Remove a session
  router.delete("/sessions/:name", async (req, res) => {
    const { name } = req.params;
    if (!sm.hasSession(name)) {
      return res.status(404).json({ error: "Session not found", name });
    }
    try {
      await sm.removeSession(name);
      res.json({ status: "removed", name });
    } catch (err) {
      logger.error({ err: err.message, session: name }, "Failed to remove session");
      res.status(500).json({ error: err.message });
    }
  });

  // ── Per-session QR / Status / Control ───────────────────────────────────

  // GET /api/qr?session=xxx — QR code for a specific session
  router.get("/qr", (req, res) => {
    const wa = getClient(req);
    if (!wa) return res.json({ qr: null, status: "no_session", phone: null, receivedAt: null });

    const { connected, phone } = wa.getStatus();
    if (connected) {
      return res.json({ qr: null, status: "connected", phone, receivedAt: null });
    }
    const { qr, receivedAt } = wa.getQr();
    if (qr) {
      return res.json({ qr, status: "qr_ready", phone: null, receivedAt });
    }
    res.json({ qr: null, status: "connecting", phone: null, receivedAt: null });
  });

  // GET /api/status?session=xxx — Status of a specific session
  router.get("/status", (req, res) => {
    const name = req.query.session;
    if (name) {
      const client = sm.getSession(name);
      if (!client) return res.json({ status: "not_found", session: name });
      const { connected, phone } = client.getStatus();
      return res.json({ status: connected ? "connected" : "disconnected", phone, session: name });
    }
    // No session specified — return all
    res.json(sm.listSessions());
  });

  // POST /api/restart?session=xxx — Restart a specific session
  router.post("/restart", async (req, res) => {
    const wa = getClient(req);
    if (!wa) return res.status(404).json({ error: "Session not found" });
    try {
      await wa.reconnect();
      res.json({ status: "restarting" });
    } catch (err) {
      logger.error({ err: err.message }, "Restart failed");
      res.status(500).json({ error: err.message });
    }
  });

  // POST /api/logout?session=xxx — Logout a specific session
  router.post("/logout", async (req, res) => {
    const wa = getClient(req);
    if (!wa) return res.status(404).json({ error: "Session not found" });
    try {
      await wa.logout();
      res.json({ status: "logged_out" });
    } catch (err) {
      logger.error({ err: err.message }, "Logout failed");
      res.status(500).json({ error: err.message });
    }
  });

  // ── Message Sending (backwards compatible) ──────────────────────────────

  // POST /api/sendText
  router.post("/sendText", async (req, res) => {
    const { chatId, text } = req.body;
    if (!chatId || !text) {
      return res.status(400).json({ error: "chatId and text required" });
    }
    const wa = getClient(req);
    if (!wa) return res.status(503).json({ error: "No active session" });
    try {
      await wa.sendText(chatId, text);
      res.json({ status: "sent", chatId });
    } catch (err) {
      logger.error({ err: err.message, chatId }, "sendText failed");
      res.status(500).json({ error: err.message });
    }
  });

  // POST /api/sendFile
  router.post("/sendFile", async (req, res) => {
    const { chatId, file, caption } = req.body;
    if (!chatId || !file?.data) {
      return res.status(400).json({ error: "chatId and file.data required" });
    }
    const wa = getClient(req);
    if (!wa) return res.status(503).json({ error: "No active session" });

    const buffer = Buffer.from(file.data, "base64");
    const mimetype = file.mimetype || "application/octet-stream";
    const filename = file.filename || "file";

    try {
      await wa.sendFile(chatId, buffer, mimetype, filename, caption || "");
      res.json({ status: "sent", chatId, mimetype, size: buffer.length });
    } catch (err) {
      logger.error({ err: err.message, chatId, mimetype }, "sendFile failed");
      res.status(500).json({ error: err.message });
    }
  });

  // POST /api/sendVoice
  router.post("/sendVoice", async (req, res) => {
    const { chatId } = req.body;
    if (!chatId) {
      return res.status(400).json({ error: "chatId required" });
    }
    const wa = getClient(req);
    if (!wa) return res.status(503).json({ error: "No active session" });

    let buffer, mimetype;
    if (req.body.file?.data) {
      buffer = Buffer.from(req.body.file.data, "base64");
      mimetype = req.body.file.mimetype || "audio/ogg; codecs=opus";
    } else if (req.body.audio) {
      buffer = Buffer.from(req.body.audio, "base64");
      mimetype = req.body.mimetype || "audio/ogg; codecs=opus";
    } else {
      return res.status(400).json({ error: "file.data or audio required" });
    }

    try {
      await wa.sendVoice(chatId, buffer, mimetype);
      res.json({ status: "sent", chatId, type: "voice", size: buffer.length });
    } catch (err) {
      logger.error({ err: err.message, chatId }, "sendVoice failed");
      res.status(500).json({ error: err.message });
    }
  });

  // POST /api/sendImage
  router.post("/sendImage", async (req, res) => {
    const { chatId, file, caption } = req.body;
    if (!chatId || !file?.data) {
      return res.status(400).json({ error: "chatId and file.data required" });
    }
    const wa = getClient(req);
    if (!wa) return res.status(503).json({ error: "No active session" });
    const buffer = Buffer.from(file.data, "base64");
    const mimetype = file.mimetype || "image/jpeg";
    const filename = file.filename || "image.jpg";

    try {
      await wa.sendImage(chatId, buffer, mimetype, filename, caption || "");
      res.json({ status: "sent", chatId, type: "image" });
    } catch (err) {
      logger.error({ err: err.message, chatId }, "sendImage failed");
      res.status(500).json({ error: err.message });
    }
  });

  // POST /api/sendVideo
  router.post("/sendVideo", async (req, res) => {
    const { chatId, file, caption } = req.body;
    if (!chatId || !file?.data) {
      return res.status(400).json({ error: "chatId and file.data required" });
    }
    const wa = getClient(req);
    if (!wa) return res.status(503).json({ error: "No active session" });
    const buffer = Buffer.from(file.data, "base64");
    const mimetype = file.mimetype || "video/mp4";

    try {
      await wa.sendVideo(chatId, buffer, mimetype, caption || "");
      res.json({ status: "sent", chatId, type: "video" });
    } catch (err) {
      logger.error({ err: err.message, chatId }, "sendVideo failed");
      res.status(500).json({ error: err.message });
    }
  });

  // POST /api/startTyping
  router.post("/startTyping", async (req, res) => {
    const { chatId } = req.body;
    if (!chatId) return res.status(400).json({ error: "chatId required" });
    const wa = getClient(req);
    if (!wa) return res.json({ status: "ok" });
    try { await wa.startTyping(chatId); } catch {}
    res.json({ status: "ok" });
  });

  // POST /api/stopTyping
  router.post("/stopTyping", async (req, res) => {
    const { chatId } = req.body;
    if (!chatId) return res.status(400).json({ error: "chatId required" });
    const wa = getClient(req);
    if (!wa) return res.json({ status: "ok" });
    try { await wa.stopTyping(chatId); } catch {}
    res.json({ status: "ok" });
  });

  // POST /api/startRecording
  router.post("/startRecording", async (req, res) => {
    const { chatId } = req.body;
    if (!chatId) return res.status(400).json({ error: "chatId required" });
    const wa = getClient(req);
    if (!wa) return res.json({ status: "ok" });
    try { await wa.startRecording(chatId); } catch {}
    res.json({ status: "ok" });
  });

  // POST /api/stopRecording
  router.post("/stopRecording", async (req, res) => {
    const { chatId } = req.body;
    if (!chatId) return res.status(400).json({ error: "chatId required" });
    const wa = getClient(req);
    if (!wa) return res.json({ status: "ok" });
    try { await wa.stopRecording(chatId); } catch {}
    res.json({ status: "ok" });
  });

  // GET /api/messages — Compatibility stub
  router.get("/messages", async (req, res) => {
    res.json([]);
  });

  return router;
}

module.exports = { createRoutes };
