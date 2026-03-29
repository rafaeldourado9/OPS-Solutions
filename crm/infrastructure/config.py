from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    crm_database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5433/crm"

    # Redis
    redis_url: str = "redis://localhost:6379/1"

    # Auth
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 480  # 8 hours

    # Agents integration
    agents_api_url: str = "http://localhost:8000"
    agents_dir: str = "../agents/agents"

    # WhatsApp Gateway
    gateway_url: str = "http://localhost:3000"
    gateway_api_key: str = ""

    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"

    # MinIO
    minio_url: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "crm-files"
    minio_secure: bool = False

    # Qdrant (read-only, for RAG listing)
    qdrant_url: str = "http://localhost:6333"

    # LLM (Gemini) — used for AI-powered template field analysis
    gemini_api_key: str = ""
    gemini_analyzer_model: str = "gemini-2.0-flash"

    # Email (SMTP)
    smtp_host: str = "smtp-relay.brevo.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_tls: bool = True
    email_from: str = "OPS Solutions <suporte@ops.solutions.com>"

    # App public URL (used in password reset emails)
    app_url: str = "http://localhost:3001"

    # Mercado Pago
    mercadopago_access_token: str = ""
    mercadopago_webhook_secret: str = ""
    mp_starter_price: float = 297.0
    mp_pro_price: float = 497.0

    # Server
    host: str = "0.0.0.0"
    port: int = 8001
    log_level: str = "INFO"
    log_json: bool = False

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}


settings = Settings()
