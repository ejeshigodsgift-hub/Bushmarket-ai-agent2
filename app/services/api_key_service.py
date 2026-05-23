from sqlalchemy.orm import Session
from app.db.models.api_key import APIKey
from app.core.security import hash_api_key


class APIKeyService:

    def validate_api_key(self, db: Session, raw_key: str):

        hashed = hash_api_key(raw_key)

        key = (
            db.query(APIKey)
            .filter(
                APIKey.key_hash == hashed,
                APIKey.is_active == True
            )
            .first()
        )

        return key