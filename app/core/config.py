from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseModel):
    APP_NAME: str = os.getenv("APP_NAME")
    ENV: str = os.getenv("ENV")

    DATABASE_URL: str = os.getenv("DATABASE_URL")

    REDIS_URL: str = os.getenv("REDIS_URL")

    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    KAFKA_CLIENT_ID: str = os.getenv("KAFKA_CLIENT_ID")

    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    COOKIE_NAME: str = os.getenv("COOKIE_NAME")


settings = Settings()