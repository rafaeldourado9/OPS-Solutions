/**
 * Express routes — WAHA-compatible REST API.
 *
 * Implements the same endpoints that the Python agent framework expects:
 *   POST /api/sendText        — Send a text message
 *   POST /api/sendFile        — Send a file (image, audio, video, document)
 *   POST /api/sendVoice       — Send a voice message (PTT)
 *   POST /api/startTyping     — Show typing indicator
 *   POST /api/stopTyping      — Stop typing indicator
 *   GET  /api/messages        — Fetch messages (limited, for media re-download)
 */

const express = require("express");

function createRoutes(wa, logger) {
  const router = express.Router();

  // POST /api/sendText — Send a text message
  router.post("/sendText", async (req, res) => {
    const { chatId, text } = req.body;
    if (!chatId || !text) {
      return res.status(400).json({ error: "chatId and text required" });
    }
    try {
      await wa.sendText(chatId, text);
      res.json({ status: "sent", chatId });
    } catch (err) {
      logger.error({ err: err.message, chatId }, "sendText failed");
      res.status(500).json({ error: err.message });
    }
  });

  // POST /api/sendFile — Send a file (WAHA-compatible format)
  // Body: { chatId, file: { mimetype, filename, data (base64) }, caption, session }
  router.post("/sendFile", async (req, res) => {
    const { chatId, file, caption } = req.body;
    if (!chatId || !file?.data) {
      return res.status(400).json({ error: "chatId and file.data required" });
    }

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

  // POST /api/sendVoice — Send a voice message (PTT)
  // Body: { chatId, file: { data (base64), mimetype }, session }
  // Also accepts: { chatId, audio (base64), mimetype }
  router.post("/sendVoice", async (req, res) => {
    const { chatId } = req.body;
    if (!chatId) {
      return res.status(400).json({ error: "chatId required" });
    }

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

  // POST /api/sendImage — Send an image (convenience endpoint)
  router.post("/sendImage", async (req, res) => {
    const { chatId, file, caption } = req.body;
    if (!chatId || !file?.data) {
      return res.status(400).json({ error: "chatId and file.data required" });
    }
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

  // POST /api/sendVideo — Send a video (convenience endpoint)
  router.post("/sendVideo", async (req, res) => {
    const { chatId, file, caption } = req.body;
    if (!chatId || !file?.data) {
      return res.status(400).json({ error: "chatId and file.data required" });
    }
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

  // POST /api/startTyping — Show typing indicator
  router.post("/startTyping", async (req, res) => {
    const { chatId } = req.body;
    if (!chatId) {
      return res.status(400).json({ error: "chatId required" });
    }
    try {
      await wa.startTyping(chatId);
      res.json({ status: "ok" });
    } catch (err) {
      res.json({ status: "ok" }); // Non-critical
    }
  });

  // POST /api/stopTyping — Stop typing indicator
  router.post("/stopTyping", async (req, res) => {
    const { chatId } = req.body;
    if (!chatId) {
      return res.status(400).json({ error: "chatId required" });
    }
    try {
      await wa.stopTyping(chatId);
      res.json({ status: "ok" });
    } catch (err) {
      res.json({ status: "ok" }); // Non-critical
    }
  });

  // POST /api/startRecording — Show "recording audio" indicator
  router.post("/startRecording", async (req, res) => {
    const { chatId } = req.body;
    if (!chatId) {
      return res.status(400).json({ error: "chatId required" });
    }
    try {
      await wa.startRecording(chatId);
      res.json({ status: "ok" });
    } catch (err) {
      res.json({ status: "ok" }); // Non-critical
    }
  });

  // POST /api/stopRecording — Stop "recording audio" indicator
  router.post("/stopRecording", async (req, res) => {
    const { chatId } = req.body;
    if (!chatId) {
      return res.status(400).json({ error: "chatId required" });
    }
    try {
      await wa.stopRecording(chatId);
      res.json({ status: "ok" });
    } catch (err) {
      res.json({ status: "ok" }); // Non-critical
    }
  });

  // GET /api/messages — Limited message retrieval (for media re-download compatibility)
  // This endpoint exists for WAHA compatibility but media is already embedded in webhooks
  router.get("/messages", async (req, res) => {
    // Our gateway embeds media directly in webhook payloads,
    // so this endpoint is rarely needed. Return empty for compatibility.
    res.json([]);
  });

  return router;
}

module.exports = { createRoutes };
