from datetime import datetime

from app.core.config import settings
from app.services.streaming.base_stream_provider import (
    BaseStreamProvider
)


class AgoraProvider(BaseStreamProvider):

    async def create_channel(
        self,
        channel_name: str
    ):

        return {
            "channel": channel_name,
            "provider": "agora"
        }

    async def generate_token(
        self,
        channel_name: str,
        user_id: str
    ):

        # Generate Agora RTC token here

        return {
            "provider": "agora",
            "channel": channel_name,
            "token": "AGORA_TOKEN"
        }

    async def start_broadcast(
        self,
        channel_name: str
    ):

        return {
            "status": "started",
            "channel": channel_name
        }

    async def end_broadcast(
        self,
        channel_name: str
    ):

        return {
            "status": "ended",
            "channel": channel_name
        }