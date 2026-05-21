def build_ai_prompt(event_type: str, payload: dict):

    base_context = f"""
You are Bushmarket AI Notification Engine.

System Context:
- Cooperative buying platform
- Escrow-based financial system
- Bulk procurement and delivery tracking

Event: {event_type}
Payload: {payload}

Generate a short, human-like notification message for users.
Keep it concise, actionable, and emotionally engaging.
"""

    return base_context