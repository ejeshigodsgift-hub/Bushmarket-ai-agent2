from datetime import datetime, timezone

from sqlalchemy import select, desc
from sqlalchemy import delete

from app.db.models.ai_conversation import AIConversation
from app.db.models.ai_message import AIMessage
from app.db.models.ai_shopping_session import AIShoppingSession


class AILogger:

    # =====================================================
    # CONVERSATIONS
    # =====================================================

    async def get_or_create_conversation(
        self,
        db,
        user_id: str
    ):

        stmt = (
            select(AIConversation)
            .where(AIConversation.user_id == user_id)
            .order_by(desc(AIConversation.created_at))
            .limit(1)
        )

        result = await db.execute(stmt)

        conversation = result.scalar_one_or_none()

        if conversation:
            return conversation

        conversation = AIConversation(
            user_id=user_id
        )

        db.add(conversation)

        await db.flush()

        return conversation

    async def get_conversation_messages(
        self,
        db,
        conversation_id: str,
        limit: int = 50
    ):

        stmt = (
            select(AIMessage)
            .where(
                AIMessage.conversation_id == conversation_id
            )
            .order_by(desc(AIMessage.created_at))
            .limit(limit)
        )

        result = await db.execute(stmt)

        return result.scalars().all()



    async def get_conversation(
        self,
        db,
        conversation_id: str
    ):

        stmt = (
            select(AIConversation)
            .where(
                AIConversation.id == conversation_id
            )
        )

        result = await db.execute(stmt)

        return result.scalar_one_or_none()



    async def get_user_conversations(
        self,
        db,
        user_id: str,
        limit: int = 20
    ):

        stmt = (
            select(AIConversation)
            .where(
                AIConversation.user_id == user_id
            )
            .order_by(
            desc(AIConversation.created_at)
            )
            .limit(limit)
        )

        result = await db.execute(stmt)

        return result.scalars().all()



    async def delete_conversation(
        self,
        db,
        conversation_id: str
    ):

        stmt = (
            delete(AIConversation)
            .where(
                AIConversation.id == conversation_id
            )
        )

        await db.execute(stmt)

        await db.flush()

        return True


    async def clear_user_history(
        self,
        db,
        user_id: str
    ):

        stmt = (
            delete(AIConversation)
            .where(
                AIConversation.user_id == user_id
            )
        )

        await db.execute(stmt)

        await db.flush()

        return True

    # =====================================================
    # MESSAGE LOGGING
    # =====================================================

    async def log_message(
        self,
        db,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict | None = None
    ):

        message = AIMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_metadata=metadata or {},
            created_at=datetime.now(timezone.utc)
        )

        db.add(message)

        await db.flush()

        return message

    async def log_user_message(
        self,
        db,
        user_id: str,
        message: str,
        metadata: dict | None = None
    ):

        conversation = await self.get_or_create_conversation(
            db=db,
            user_id=user_id
        )

        await self.log_message(
            db=db,
            conversation_id=conversation.id,
            role="user",
            content=message,
            metadata=metadata
        )

        return conversation.id

    async def log_assistant_message(
        self,
        db,
        conversation_id: str,
        message: str,
        metadata: dict | None = None
    ):

        return await self.log_message(
            db=db,
            conversation_id=conversation_id,
            role="assistant",
            content=message,
            metadata=metadata
        )

    async def log_system_message(
        self,
        db,
        conversation_id: str,
        message: str,
        metadata: dict | None = None
    ):

        return await self.log_message(
            db=db,
            conversation_id=conversation_id,
            role="system",
            content=message,
            metadata=metadata
        )

    # =====================================================
    # SHOPPING SESSION
    # =====================================================

    async def get_latest_shopping_session(
        self,
        db,
        user_id: str,
        conversation_id: str
    ):

        stmt = (
            select(AIShoppingSession)
            .where(
                AIShoppingSession.user_id == user_id,
                AIShoppingSession.conversation_id == conversation_id
            )
            .order_by(
                desc(AIShoppingSession.created_at)
            )
            .limit(1)
        )

        result = await db.execute(stmt)

        return result.scalar_one_or_none()

    async def create_shopping_session(
        self,
        db,
        user_id: str,
        conversation_id: str,
        status: str,
        listing_id: str | None = None,
        quantity: int | None = None,
        metadata: dict | None = None
    ):

        session = AIShoppingSession(
            user_id=user_id,
            conversation_id=conversation_id,
            selected_listing_id=listing_id,
            quantity=quantity,
            status=status,
            metadata=metadata or {}
        )

        db.add(session)

        await db.flush()

        return session

    async def update_shopping_session(
        self,
        db,
        session: AIShoppingSession,
        status: str | None = None,
        listing_id: str | None = None,
        quantity: int | None = None,
        metadata: dict | None = None
    ):

        if status is not None:
            session.status = status

        if listing_id is not None:
            session.selected_listing_id = listing_id

        if quantity is not None:
            session.quantity = quantity

        if metadata is not None:
            session.metadata = metadata

        db.add(session)

        await db.flush()

        return session

    # =====================================================
    # SYSTEM ACTIONS
    # =====================================================

    async def log_system_action(
        self,
        db,
        user_id: str,
        conversation_id: str,
        action: str,
        data: dict,
        metadata: dict | None = None
    ):

        session = AIShoppingSession(
            user_id=user_id,
            conversation_id=conversation_id,
            selected_listing_id=data.get("listing_id"),
            quantity=data.get("quantity"),
            status=action,
            metadata={
                **data,
                **(metadata or {})
            }
        )

        db.add(session)

        await db.flush()

        return session

    # =====================================================
    # BEHAVIOR SIGNALS
    # =====================================================

    async def log_behavior_signal(
        self,
        db,
        user_id: str,
        conversation_id: str,
        event: str,
        listing_id: str | None = None,
        session_id: str | None = None,
        metadata: dict | None = None
    ):

        signal = AIShoppingSession(
            user_id=user_id,
            conversation_id=conversation_id,
            selected_listing_id=listing_id,
            quantity=1,
            status=event,
            metadata={
                "session_id": session_id,
                **(metadata or {})
            }
        )

        db.add(signal)

        await db.flush()

        return signal


ai_logger = AILogger()