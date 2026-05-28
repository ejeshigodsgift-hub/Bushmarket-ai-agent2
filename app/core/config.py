from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # =========================================
    # APP
    # =========================================
    APP_NAME: str = "Bushmarket"

    ENV: str = "development"

    # =========================================
    # DATABASE
    # =========================================
    DATABASE_URL: str

    # =========================================
    # REDIS
    # =========================================
    REDIS_URL: str

    # =========================================
    # KAFKA
    # =========================================
    KAFKA_BOOTSTRAP_SERVERS: str

    KAFKA_CLIENT_ID: str

    KAFKA_AGENT_TASK_TOPIC: str = (
        "agent.task.created"
    )

    KAFKA_AGENT_UPDATE_TOPIC: str = (
        "agent.task.updated"
    )

    # =========================================
    # SECURITY
    # =========================================
    SECRET_KEY: str

    JWT_ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    INTERNAL_JWT_EXPIRE_MINUTES: int = 30

    # =========================================
    # SESSION
    # =========================================
    SESSION_EXPIRE_SECONDS: int = 86400

    COOKIE_NAME: str = "bushmarket_session"

    COOKIE_SECURE: bool = False

    COOKIE_SAMESITE: str = "lax"

    COOKIE_DOMAIN: str = "localhost"

    # =========================================
    # CSRF
    # =========================================
    CSRF_COOKIE_NAME: str = "csrf_token"

    CSRF_HEADER_NAME: str = "x-csrf-token"

    # =========================================
    # RATE LIMITING
    # =========================================
    LOGIN_RATE_LIMIT: int = 5

    LOGIN_RATE_LIMIT_WINDOW: int = 60

    class Config:
        env_file = ".env"


settings = Settings()