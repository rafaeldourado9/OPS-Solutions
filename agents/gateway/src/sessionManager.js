/**
 * Session Manager — manages multiple WhatsApp sessions (Baileys instances).
 *
 * Each session has its own socket, auth folder, QR code, and media cache.
 * Sessions are identified by a unique name string.
 */

const { createWhatsAppClient } = require("./whatsapp");

class SessionManager {
  /**
   * @param {Object} opts
   * @param {string} opts.authDir   - Base directory for auth state
   * @param {string} opts.webhookUrl - Webhook URL for incoming messages
   * @param {Object} opts.logger    - pino logger
   */
  constructor({ authDir, webhookUrl, logger }) {
    this._authDir = authDir;
    this._webhookUrl = webhookUrl;
    this._logger = logger;
    /** @type {Map<string, Awaited<ReturnType<typeof createWhatsAppClient>>>} */
    this._sessions = new Map();
  }

  /**
   * Create and start a new session.
   * @param {string} name - Unique session name
   * @returns {Promise<Object>} The session client instance
   */
  async createSession(name) {
    if (this._sessions.has(name)) {
      this._logger.warn({ session: name }, "Session already exists");
      return this._sessions.get(name);
    }

    this._logger.info({ session: name }, "Creating WhatsApp session");
    const client = await createWhatsAppClient({
      sessionName: name,
      authDir: this._authDir,
      webhookUrl: this._webhookUrl,
      logger: this._logger.child({ session: name }),
    });

    this._sessions.set(name, client);
    return client;
  }

  /**
   * Remove a session — logout and destroy.
   * @param {string} name
   */
  async removeSession(name) {
    const client = this._sessions.get(name);
    if (!client) {
      this._logger.warn({ session: name }, "Session not found for removal");
      return;
    }

    this._logger.info({ session: name }, "Removing WhatsApp session");
    try {
      await client.logout();
    } catch (err) {
      this._logger.debug({ err: err.message, session: name }, "Logout error during removal");
    }
    this._sessions.delete(name);
  }

  /**
   * Get a session by name.
   * @param {string} name
   * @returns {Object|null}
   */
  getSession(name) {
    return this._sessions.get(name) || null;
  }

  /**
   * Get a session by name, falling back to the first active session.
   * @param {string} [name]
   * @returns {Object|null}
   */
  getOrDefault(name) {
    if (name && this._sessions.has(name)) {
      return this._sessions.get(name);
    }
    // Fall back to first connected session, then first session at all
    for (const [, client] of this._sessions) {
      const { connected } = client.getStatus();
      if (connected) return client;
    }
    // No connected session — return first one
    const first = this._sessions.values().next();
    return first.done ? null : first.value;
  }

  /**
   * List all sessions with their status.
   * @returns {Array<{name: string, connected: boolean, phone: string|null}>}
   */
  listSessions() {
    const result = [];
    for (const [name, client] of this._sessions) {
      const { connected, phone } = client.getStatus();
      result.push({ name, connected, phone });
    }
    return result;
  }

  /**
   * Check if a session exists.
   * @param {string} name
   * @returns {boolean}
   */
  hasSession(name) {
    return this._sessions.has(name);
  }

  /**
   * Number of active sessions.
   * @returns {number}
   */
  get size() {
    return this._sessions.size;
  }
}

module.exports = { SessionManager };
