# app/unit_of_work/uow.py

from sqlalchemy.ext.asyncio import AsyncSession

class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc:
            await self.session.rollback()
        else:
            await self.session.commit()

    async def add(self, obj):
        self.session.add(obj)

    async def flush(self):
        await self.session.flush()