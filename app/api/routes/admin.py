from fastapi import APIRouter, Request

router = APIRouter(prefix="/admin")


@router.get("/dashboard")
def admin_dashboard(request: Request):

    user = request.state.user

    if not user:
        return {"error": "Unauthorized"}

    return {
        "message": "Admin dashboard"
    }