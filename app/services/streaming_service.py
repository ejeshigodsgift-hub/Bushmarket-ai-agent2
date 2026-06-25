from app.services.streaming.stream_provider_factory import (
    get_stream_provider
)


class StreamingService:

    def __init__(self):
        self.provider = get_stream_provider()

    async def create_channel(
        self,
        channel_name: str
    ):
        return await self.provider.create_channel(
            channel_name
        )

    async def generate_token(
        self,
        channel_name: str,
        user_id: str
    ):
        return await self.provider.generate_token(
            channel_name,
            user_id
        )

    async def start_broadcast(
        self,
        channel_name: str
    ):
        return await self.provider.start_broadcast(
            channel_name
        )

    async def end_broadcast(
        self,
        channel_name: str
    ):
        return await self.provider.end_broadcast(
            channel_name
        )


streaming_service = StreamingService()