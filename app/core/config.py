from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseModel):

    # =========================
    # APP
    # =========================
    APP_NAME: str = os.getenv("APP_NAME", "Bushmarket")
    ENV: str = os.getenv("ENV", "development")

    # =========================
    # DATABASE
    # =========================
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    # =========================
    # REDIS
    # =========================
    REDIS_URL: str = os.getenv("REDIS_URL")

    # =========================
    # KAFKA
    # =========================
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    KAFKA_CLIENT_ID: str = os.getenv("KAFKA_CLIENT_ID")

    # =========================
    # SECURITY
    # =========================
    SECRET_KEY: str = os.getenv("SECRET_KEY")

    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    )

    REFRESH_TOKEN_EXPIRE_DAYS: int = int(
        os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)
    )

    SESSION_EXPIRE_SECONDS: int = int(
        os.getenv("SESSION_EXPIRE_SECONDS", 86400)
    )

    COOKIE_NAME: str = os.getenv(
        "COOKIE_NAME",
        "bushmarket_session"
    )

    COOKIE_SECURE: bool = os.getenv(
        "COOKIE_SECURE",
        "True"
    ) == "True"

    COOKIE_SAMESITE: str = os.getenv(
        "COOKIE_SAMESITE",
        "lax"
    )

    CSRF_COOKIE_NAME: str = "csrf_token"

    # =========================
    # RATE LIMITING
    # =========================
    LOGIN_RATE_LIMIT: int = int(
        os.getenv("LOGIN_RATE_LIMIT", 5)
    )

    LOGIN_RATE_LIMIT_WINDOW: int = int(
        os.getenv("LOGIN_RATE_LIMIT_WINDOW", 60)
    )

    # =========================
    # INTERNAL SERVICES
    # =========================
    INTERNAL_JWT_EXPIRE_MINUTES: int = 30

    # =========================
    # KAFKA TOPICS
    # =========================
    TASK_CREATED_TOPIC: str = "agent.task.created"
    TASK_UPDATED_TOPIC: str = "agent.task.updated"


settings = Settings()