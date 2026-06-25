from app.services.streaming.base_stream_provider import (
    BaseStreamProvider
)


class LiveKitProvider(BaseStreamProvider):

    async def create_channel(
        self,
        channel_name: str
    ):

        return {
            "channel": channel_name,
            "provider": "livekit"
        }

    async def generate_token(
        self,
        channel_name: str,
        user_id: str
    ):

        return {
            "provider": "livekit",
            "channel": channel_name,
            "token": "LIVEKIT_TOKEN"
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