@pytest.mark.asyncio
async def test_webhook_duplicate_payment(
    db_session
):
    result = await payment_webhook_service.handle_payment_success(
        db=db_session,
        payment_reference="abc123",
        gateway="paystack",
        amount=1000,
        user_id="user1"
    )

    second = await payment_webhook_service.handle_payment_success(
        db=db_session,
        payment_reference="abc123",
        gateway="paystack",
        amount=1000,
        user_id="user1"
    )

    assert second["status"] == "already_processed"


@pytest.mark.asyncio
async def test_payment_amount_mismatch(
    db_session,
    payment_intent
):
    with pytest.raises(HTTPException):
        await payment_webhook_service.handle_payment_success(
            db=db_session,
            payment_reference=payment_intent.reference,
            gateway="paystack",
            amount=99999,
            user_id=payment_intent.user_id
        )


@pytest.mark.asyncio
async def test_missing_payment_intent(
    db_session
):
    with pytest.raises(HTTPException):
        await payment_webhook_service.handle_payment_success(
            db=db_session,
            payment_reference="missing",
            gateway="paystack",
            amount=100,
            user_id="user1"
        )


