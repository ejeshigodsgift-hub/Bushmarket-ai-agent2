from fastapi import HTTPException


class TaskStateMachine:

    TRANSITIONS = {
        "assigned": [
            "in_progress",
            "cancelled"
        ],

        "in_progress": [
            "completed",
            "failed",
            "cancelled"
        ],

        "failed": [
            "assigned"
        ],

        "completed": [],
        "cancelled": []
    }

    @classmethod
    def validate_transition(
        cls,
        current_status: str,
        new_status: str
    ):

        allowed = cls.TRANSITIONS.get(
            current_status,
            []
        )

        if new_status not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid transition from '{current_status}' to '{new_status}'"
            )