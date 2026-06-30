

import pytest

from app.services.auth_service import AuthService

auth_service = AuthService()


@pytest.mark.asyncio
async def test_signup_success(
    db_session
):
    user = await auth_service.signup(
        db=db_session,
        data={
            "full_name": "John Doe",
            "email": "john@test.com",
            "password": "secret123"
        }
    )

    assert user.email == "john@test.com"


@pytest.mark.asyncio
async def test_signup_duplicate_email(
    db_session
):
    await auth_service.signup(
        db=db_session,
        data={
            "full_name": "John Doe",
            "email": "john@test.com",
            "password": "secret123"
        }
    )

    result = await auth_service.signup(
        db=db_session,
        data={
            "full_name": "John Doe",
            "email": "john@test.com",
            "password": "secret123"
        }
    )

    assert result is None


@pytest.mark.asyncio
async def test_login_success(
    db_session,
    user
):
    result = await auth_service.login(
        db=db_session,
        identifier=user.email,
        password="password",
        request_meta={}
    )

    assert result["user"].id == user.id



@pytest.mark.asyncio
async def test_login_invalid_password(
    db_session,
    user
):
    result = await auth_service.login(
        db=db_session,
        identifier=user.email,
        password="wrong-password",
        request_meta={}
    )

    assert result is None



