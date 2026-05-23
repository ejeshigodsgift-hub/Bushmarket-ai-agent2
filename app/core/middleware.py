from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

from app.db.session import SessionLocal

from app.services.session_service import SessionService


class SessionAuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self,
        request: Request,
        call_next
    ):

        request.state.user = None

        session_token = request.cookies.get(
            settings.COOKIE_NAME
        )

        if session_token:

            db = SessionLocal()

            try:

                session_service = SessionService()

                db_session = session_service.get_session(
                    db=db,
                    token=session_token
                )

                if db_session:

                    request.state.user = {
                        "id": db_session.user.id,
                        "email": db_session.user.email,
                        "session_id": db_session.id,
                        "roles": [
                            role.role
                            for role in db_session.user.roles
                        ]
                    }

            finally:
                db.close()

        response = await call_next(request)

        return response