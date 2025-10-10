"""Centralized configuration management for Project Agent."""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with validation and type safety."""
    
    # GCP Configuration
    gcp_project: str = os.getenv("GCP_PROJECT", "transparent-agent-test")
    region: str = os.getenv("REGION", "us-central1")
    allowed_domain: str = os.getenv("ALLOWED_DOMAIN", "transparent.partners")
    
    # Storage Buckets
    gcs_doc_bucket: str = os.getenv("GCS_DOC_BUCKET", "ta-test-docs-dev")
    gcs_thumb_bucket: str = os.getenv("GCS_THUMB_BUCKET", "ta-test-thumbs-dev")
    
    # Database
    firestore_db: str = os.getenv("FIRESTORE_DB", "(default)")
    
    # AI Services
    vector_index: str = os.getenv("VECTOR_INDEX", "project-agent-dev")
    doc_ai_processor: Optional[str] = os.getenv("DOC_AI_PROCESSOR")
    
    # Authentication
    google_oauth_client_id: Optional[str] = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    google_oauth_client_secret: Optional[str] = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    admin_emails: str = os.getenv("ADMIN_EMAILS", "")
    
    # Pub/Sub
    pubsub_topic_ingestion: str = os.getenv("PUBSUB_TOPIC_INGESTION", "project-agent-ingestion")
    pubsub_subscription_ingestion: str = os.getenv("PUBSUB_SUBSCRIPTION_INGESTION", "project-agent-ingestion-sub")
    
    # Service Account
    service_account_email: Optional[str] = os.getenv("SERVICE_ACCOUNT_EMAIL")
    
    # API Configuration
    api_rate_limit: int = int(os.getenv("API_RATE_LIMIT", "100"))
    api_timeout: int = int(os.getenv("API_TIMEOUT", "30"))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    structured_logging: bool = os.getenv("STRUCTURED_LOGGING", "true").lower() == "true"
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # CORS
    cors_origins: list = [
        "http://localhost:3000",
        "https://transparent-agent-test.web.app",
        f"https://project-agent-web-{os.getenv('GCP_PROJECT', 'transparent-agent-test')}.{os.getenv('REGION', 'us-central1')}.run.app"
    ]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    def get_admin_emails(self) -> list[str]:
        """Get list of admin emails."""
        if not self.admin_emails:
            return []
        return [email.strip() for email in self.admin_emails.split(",") if email.strip()]
    
    class Config:
        """Pydantic config."""
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()

