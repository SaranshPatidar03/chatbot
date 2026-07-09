"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for API, data stores, LLM, and RAG."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # Application
    app_name: str = Field(default="Knowledge Chatbot", alias="APP_NAME")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development", alias="APP_ENV"
    )
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    app_api_prefix: str = Field(default="/api/v1", alias="APP_API_PREFIX")
    app_version: str = "0.1.0"
    frontend_url: str = Field(default="http://localhost:5173", alias="FRONTEND_URL")
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        alias="CORS_ORIGINS",
    )
    secret_key: str = Field(
        default="change-me-to-a-long-random-secret-in-production",
        alias="SECRET_KEY",
    )
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://chatbot:chatbot_secret@localhost:5432/chatbot",
        alias="DATABASE_URL",
    )
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="chatbot", alias="POSTGRES_USER")
    postgres_password: str = Field(default="chatbot_secret", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="chatbot", alias="POSTGRES_DB")

    # Redis / workers
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    arq_redis_url: str = Field(default="redis://localhost:6379/0", alias="ARQ_REDIS_URL")

    # Vector store
    chroma_host: str = Field(default="localhost", alias="CHROMA_HOST")
    chroma_port: int = Field(default=8001, alias="CHROMA_PORT")
    chroma_persist_dir: str = Field(default="./storage/chroma", alias="CHROMA_PERSIST_DIR")

    # Storage
    storage_path: str = Field(default="./storage/uploads", alias="STORAGE_PATH")
    temp_path: str = Field(default="./storage/temp", alias="TEMP_PATH")
    max_upload_size_mb: int = Field(default=50, alias="MAX_UPLOAD_SIZE_MB")
    allowed_extensions: str = Field(
        default=(
            "pdf,docx,txt,csv,md,markdown,ppt,pptx,xls,xlsx,json,html,htm,"
            "png,jpg,jpeg,webp,tiff,zip"
        ),
        alias="ALLOWED_EXTENSIONS",
    )

    # OpenAI
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_default_model: str = Field(default="gpt-4o-mini", alias="OPENAI_DEFAULT_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL"
    )

    # Ollama
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_default_model: str = Field(default="llama3", alias="OLLAMA_DEFAULT_MODEL")
    ollama_embedding_model: str = Field(
        default="nomic-embed-text", alias="OLLAMA_EMBEDDING_MODEL"
    )

    default_llm_provider: Literal["openai", "ollama"] = Field(
        default="ollama", alias="DEFAULT_LLM_PROVIDER"
    )
    default_embedding_provider: Literal["openai", "ollama"] = Field(
        default="ollama", alias="DEFAULT_EMBEDDING_PROVIDER"
    )

    # RAG
    rag_top_k: int = Field(default=8, alias="RAG_TOP_K")
    rag_mmr_lambda: float = Field(default=0.5, alias="RAG_MMR_LAMBDA")
    rag_similarity_threshold: float = Field(default=0.35, alias="RAG_SIMILARITY_THRESHOLD")
    rag_chunk_size: int = Field(default=1000, alias="RAG_CHUNK_SIZE")
    rag_chunk_overlap: int = Field(default=200, alias="RAG_CHUNK_OVERLAP")
    rag_hybrid_alpha: float = Field(default=0.7, alias="RAG_HYBRID_ALPHA")
    embedding_batch_size: int = Field(default=32, alias="EMBEDDING_BATCH_SIZE")
    rag_allow_general_knowledge: bool = Field(
        default=False, alias="RAG_ALLOW_GENERAL_KNOWLEDGE"
    )

    # Email
    smtp_host: str = Field(default="localhost", alias="SMTP_HOST")
    smtp_port: int = Field(default=1025, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_from: str = Field(default="noreply@chatbot.local", alias="SMTP_FROM")
    smtp_tls: bool = Field(default=False, alias="SMTP_TLS")
    password_reset_token_expire_minutes: int = Field(
        default=60, alias="PASSWORD_RESET_TOKEN_EXPIRE_MINUTES"
    )

    # Rate limiting
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS")

    # OCR
    tesseract_cmd: str = Field(default="tesseract", alias="TESSERACT_CMD")

    # Admin bootstrap — first signup with this email becomes platform_admin
    initial_admin_email: str = Field(default="", alias="INITIAL_ADMIN_EMAIL")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def strip_cors(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_extension_set(self) -> set[str]:
        return {
            ext.strip().lower().lstrip(".")
            for ext in self.allowed_extensions.split(",")
            if ext.strip()
        }

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def grounded_refusal_message(self) -> str:
        return "I could not find this information in the provided knowledge base."

    @property
    def default_system_prompt(self) -> str:
        return (
            "You are an AI assistant.\n"
            "Answer ONLY using retrieved context.\n"
            "Never fabricate information.\n"
            "If information does not exist: say that you cannot find it.\n"
            "Always cite sources.\n"
            "Be concise but complete."
        )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
