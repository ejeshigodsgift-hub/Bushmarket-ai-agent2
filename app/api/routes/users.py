from fastapi import APIRouter, Request


router = APIRouter(prefix="/users")


@router.get("/me")
def get_profile(request: Request):

    if not request.state.user:
        return {
            "authenticated": False
        }

    return {
        "authenticated": True,
        "user": request.state.user
    }