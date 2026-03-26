/**
 * WhatsApp Gateway — Custom gateway using Baileys.
 *
 * Drop-in replacement for WAHA with full media support (audio, video, images, documents).
 * Exposes the same REST API endpoints so the Python agent framework works without changes.
 *
 * Environment variables:
 *   WEBHOOK_URL    — URL to POST incoming messages (default: http://localhost:8000/webhook)
 *   PORT           — HTTP server port (default: 3000)
 *   SESSION_NAME   — WhatsApp session name (default: "default")
 *   AUTH_DIR       — Directory to persist auth state (default: ./auth)
 *   API_KEY        — Optional API key for X-Api-Key header validation
 */

const express = require("express");
const pino = require("pino");
const { createWhatsAppClient } = require("./whatsapp");
const { createRoutes } = require("./routes");

const logger = pino({ level: process.env.LOG_LEVEL || "info" });

const PORT = parseInt(process.env.PORT || "3000", 10);
const WEBHOOK_URL = process.env.WEBHOOK_URL || "http://localhost:8000/webhook";
const SESSION_NAME = process.env.SESSION_NAME || "default";
const AUTH_DIR = process.env.AUTH_DIR || "./auth";
const API_KEY = process.env.API_KEY || "";

async function main() {
  const app = express();
  app.use(express.json({ limit: "100mb" }));

  // Optional API key validation
  if (API_KEY) {
    app.use((req, res, next) => {
      if (req.path === "/health") return next();
      const key = req.headers["x-api-key"] || "";
      if (key !== API_KEY) {
        return res.status(401).json({ error: "Invalid API key" });
      }
      next();
    });
  }

  // Create WhatsApp client
  const wa = await createWhatsAppClient({
    sessionName: SESSION_NAME,
    authDir: AUTH_DIR,
    webhookUrl: WEBHOOK_URL,
    logger,
  });

  // Mount WAHA-compatible routes
  const routes = createRoutes(wa, logger);
  app.use("/api", routes);

  // Health check
  app.get("/health", (req, res) => {
    const status = wa.getStatus();
    res.json({
      status: status.connected ? "ok" : "connecting",
      session: SESSION_NAME,
      phone: status.phone || null,
      uptime: process.uptime(),
    });
  });

  app.listen(PORT, () => {
    logger.info(`WhatsApp Gateway running on port ${PORT}`);
    logger.info(`Webhook URL: ${WEBHOOK_URL}`);
    logger.info(`Session: ${SESSION_NAME}`);
  });
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
