import hashlib


def generate_event_hash(reference: str, amount: str, timestamp: str) -> str:
    """
    Creates immutable audit integrity hash
    """
    raw = f"{reference}|{amount}|{timestamp}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()