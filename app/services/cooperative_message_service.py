class CooperativeMessageService:

    def __init__(self, cooperative_service):
        self.cooperative_service = cooperative_service

    async def send_to_members(
        self,
        db,
        cooperative_id: str,
        sender_user_id: str,
        title: str,
        message: str,
        inbox_model,
        notification_model
    ):
        cooperative = await self.cooperative_service.get_by_id(
            db,
            cooperative_id
        )

        if not cooperative:
            raise HTTPException(
                status_code=404,
                detail="Cooperative not found"
            )

        sent_count = 0

        for member in cooperative.members:

            if member.user_id == sender_user_id:
                continue

            db.add(inbox_model(
                cooperative_id=cooperative_id,
                sender_user_id=sender_user_id,
                recipient_user_id=member.user_id,
                title=title,
                message=message
            ))

            db.add(notification_model(
                user_id=member.user_id,
                title=title,
                message=message,
                notification_type="cooperative_message"
            ))

            sent_count += 1

        await db.commit()

        return sent_count