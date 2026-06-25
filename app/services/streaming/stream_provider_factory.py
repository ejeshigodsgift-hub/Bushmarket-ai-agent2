from app.core.config import settings

from app.services.streaming.agora_provider import (
    AgoraProvider
)

from app.services.streaming.livekit_provider import (
    LiveKitProvider
)


def get_stream_provider():

    if settings.STREAM_PROVIDER == "livekit":
        return LiveKitProvider()

    return AgoraProvider()