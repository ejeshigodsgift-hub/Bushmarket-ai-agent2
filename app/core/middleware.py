from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.services.session_service import SessionService


class SessionAuthMiddleware(BaseHTTPMiddleware):

    def __init__(self, app):
        super().__init__(app)
        self.session_service = SessionService()

    async def dispatch(self, request: Request, call_next):

        request.state.user = None

        session_token = request.cookies.get(
            settings.COOKIE_NAME
        )

        if session_token:

            # extract request metadata (for fingerprint validation)
            ip = request.client.host
            user_agent = request.headers.get("user-agent")

            db_session = await self.session_service.get_session(
                db=request.state.db,  # injected async DB dependency
                token=session_token,
                ip=ip,
                user_agent=user_agent
            )

            if db_session:

                request.state.user = {
                    "id": db_session.user_id,
                    "email": getattr(db_session.user, "email", None),
                    "session_id": db_session.id,
                    "roles": [
                        role.role
                        for role in db_session.user.roles
                    ]
                }

        response = await call_next(request)

        return response