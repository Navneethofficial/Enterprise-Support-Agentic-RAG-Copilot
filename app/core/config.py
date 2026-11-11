
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):

    # Application
    app_name: str = "Enterprise IT Support Agentic RAG Copilot"
    app_env: str = "development"

    # API Keys
    openai_api_key: str = ""
    groq_api_key: str = ""
    tavily_api_key: str = ""
    pinecone_api_key: str = ""

    # Pinecone Configuration
    pinecone_index_name: str = "fde-it-support-rag"
    pinecone_namespace: str = "company-it-kb"

    # Hugging Face Embeddings
    embedding_model: str = (
        "sentence-transformers/all-MiniLM-L6-v2"
    )

    # Groq LLM
    groq_model: str = "openai/gpt-oss-20b"

    # Legacy OpenAI configuration (not used by updated workflow)
    openai_model: str = "gpt-4o-mini"

    # RAG Configuration
    top_k: int = 4
    max_retries: int = 1

    # Application Settings
    admin_api_key: str = "change-me"

    # Storage Paths
    audit_db_path: str = str(BASE_DIR / "data" / "audit.db")
    upload_dir: str = str(BASE_DIR / "uploads")
    sample_kb_dir: str = str(BASE_DIR / "data" / "sample_kb")

    # Environment Configuration
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
