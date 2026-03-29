/**
 * WhatsApp Gateway — Multi-session gateway using Baileys.
 *
 * Drop-in replacement for WAHA with full media support.
 * Supports multiple WhatsApp sessions managed via REST API.
 *
 * Environment variables:
 *   WEBHOOK_URL    — URL to POST incoming messages (default: http://localhost:8000/webhook)
 *   PORT           — HTTP server port (default: 3000)
 *   SESSION_NAME   — Default session name (default: "default")
 *   AUTH_DIR       — Directory to persist auth state (default: ./auth)
 *   API_KEY        — Optional API key for X-Api-Key header validation
 */

const express = require("express");
const pino = require("pino");
const { SessionManager } = require("./sessionManager");
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

  // Create session manager and boot default session
  const sm = new SessionManager({
    authDir: AUTH_DIR,
    webhookUrl: WEBHOOK_URL,
    logger,
  });

  await sm.createSession(SESSION_NAME);

  // Mount routes (pass session manager instead of single client)
  const routes = createRoutes(sm, logger);
  app.use("/api", routes);

  // Health check — reports status of all sessions
  app.get("/health", (req, res) => {
    const sessions = sm.listSessions();
    const anyConnected = sessions.some((s) => s.connected);
    res.json({
      status: anyConnected ? "ok" : "connecting",
      sessions,
      session: SESSION_NAME, // backwards compat
      phone: sessions.find((s) => s.connected)?.phone || null,
      uptime: process.uptime(),
    });
  });

  app.listen(PORT, () => {
    logger.info(`WhatsApp Gateway running on port ${PORT}`);
    logger.info(`Webhook URL: ${WEBHOOK_URL}`);
    logger.info(`Default session: ${SESSION_NAME}`);
  });
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
