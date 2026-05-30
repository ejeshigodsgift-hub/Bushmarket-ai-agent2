from fastapi import HTTPException


class TaskStateMachine:

    # ====================================================
    # TASK STATE TRANSITIONS
    # ====================================================
    TRANSITIONS = {
        "assigned": ["in_progress", "cancelled"],
        "in_progress": ["completed", "failed", "cancelled"],
        "failed": ["assigned"],
        "completed": [],
        "cancelled": []
    }

    # ====================================================
    # VALIDATE STATE TRANSITION
    # ====================================================
    @classmethod
    def validate_transition(
        cls,
        current_status: str,
        new_status: str
    ) -> bool:

        if not current_status or not new_status:
            raise HTTPException(
                status_code=400,
                detail="Task status cannot be empty"
            )

        current_status = current_status.lower()
        new_status = new_status.lower()

        allowed_transitions = cls.TRANSITIONS.get(current_status)

        if allowed_transitions is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown task status: '{current_status}'"
            )

        if new_status not in allowed_transitions:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Invalid transition from '{current_status}' "
                    f"to '{new_status}'"
                )
            )

        return True