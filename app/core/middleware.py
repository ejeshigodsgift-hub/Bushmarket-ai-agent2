from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.session_service import SessionService
from app.core.config import settings


class SessionAuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        session_token = request.cookies.get(settings.COOKIE_NAME)

        request.state.user = None

        if session_token:
            session_service = SessionService()
            session = session_service.get_session(session_token)

            if session:
                request.state.user = session

        response = await call_next(request)
        return response