from abc import ABC, abstractmethod


class BaseStreamProvider(ABC):

    @abstractmethod
    async def create_channel(
        self,
        channel_name: str
    ):
        pass

    @abstractmethod
    async def generate_token(
        self,
        channel_name: str,
        user_id: str
    ):
        pass

    @abstractmethod
    async def start_broadcast(
        self,
        channel_name: str
    ):
        pass

    @abstractmethod
    async def end_broadcast(
        self,
        channel_name: str
    ):
        pass