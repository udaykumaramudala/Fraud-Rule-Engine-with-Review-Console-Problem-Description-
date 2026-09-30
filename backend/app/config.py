import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "Fraud Rule Engine & Review Console"
    ENV: str = os.getenv("ENV", "development")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/fraud_engine.db")
    API_KEY: Optional[str] = os.getenv("API_KEY", None)
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    
    # Risk Evaluation Thresholds
    HIGH_RISK_THRESHOLD: float = float(os.getenv("HIGH_RISK_THRESHOLD", "60.0"))
    CRITICAL_RISK_THRESHOLD: float = float(os.getenv("CRITICAL_RISK_THRESHOLD", "80.0"))
    
    # AWS Settings (SES & SNS)
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID", None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY", None)
    AWS_SESSION_TOKEN: Optional[str] = os.getenv("AWS_SESSION_TOKEN", None)
    
    # AWS SES (Email)
    SES_SENDER_EMAIL: str = os.getenv("SES_SENDER_EMAIL", "fraud-alerts@example.com")
    SES_ALERT_RECIPIENT: str = os.getenv("SES_ALERT_RECIPIENT", "security-team@example.com")
    
    # AWS SNS (SMS / Topic)
    SNS_TOPIC_ARN: Optional[str] = os.getenv("SNS_TOPIC_ARN", None)
    SNS_PHONE_NUMBER: Optional[str] = os.getenv("SNS_PHONE_NUMBER", None)
    
    # Force Mock notification even if AWS keys exist (useful for testing)
    FORCE_MOCK_NOTIFICATIONS: bool = os.getenv("FORCE_MOCK_NOTIFICATIONS", "false").lower() in ("true", "1")
    REQUIRE_LIVE_NOTIFICATIONS: bool = os.getenv("REQUIRE_LIVE_NOTIFICATIONS", "false").lower() in ("true", "1")

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()
