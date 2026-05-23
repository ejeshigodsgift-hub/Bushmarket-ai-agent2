from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


engine = create_engine(
    settings.DATABASE_URL,

    pool_pre_ping=True,
    pool_size=20,
    max_overflow=40,

    pool_recycle=1800,

    future=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():

    db = SessionLocal()

    try:
        yield db
        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()