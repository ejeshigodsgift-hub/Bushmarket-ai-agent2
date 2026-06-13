class CooperativeStateEngine:

    VALID_TRANSITIONS = CooperativeStateService.VALID_TRANSITIONS

    @staticmethod
    def validate_transition(current: str, new: str):
        allowed = CooperativeStateEngine.VALID_TRANSITIONS.get(current, [])

        if new not in allowed:
            raise HTTPException(400, f"Invalid transition {current} → {new}")

    @staticmethod
    def transition(coop, new_state: str):
        CooperativeStateEngine.validate_transition(coop.status, new_state)
        coop.status = new_state