class CooperativeMessageService:

    async def send_to_members(
        self,
        db,
        cooperative_id: str,
        sender_user_id: str,
        title: str,
        message: str
    ):

        cooperative = await cooperative_service.get_by_id(
            db,
            cooperative_id
        )

        if not cooperative:
            raise HTTPException(
                status_code=404,
                detail="Cooperative not found"
            )

        members = cooperative.members

        sent_count = 0

        for member in members:

            if member.user_id == sender_user_id:
                continue

            inbox = CooperativeInboxMessage(
                cooperative_id=cooperative_id,
                sender_user_id=sender_user_id,
                recipient_user_id=member.user_id,
                title=title,
                message=message
            )

            db.add(inbox)

            notification = Notification(
                user_id=member.user_id,
                title=title,
                message=message,
                notification_type="cooperative_message"
            )

            db.add(notification)

            sent_count += 1

        await db.commit()

        return sent_count