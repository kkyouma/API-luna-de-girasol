"""Management of database with SQLModel and Turso."""

import logging
import os
import time
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine, text  # noqa: F401

# =============== CONFIG ===============

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# =============== AUTH ===============

load_dotenv()

TURSO_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

if not TURSO_URL or not TURSO_AUTH_TOKEN:
    raise ValueError("Missing TURSO_DATABASE_URL or TURSO_AUTH_TOKEN")

# DATABASE_URL = f"libsql:///{TURSO_URL.removeprefix('libsql://').removeprefix('https://')}?authToken={TURSO_AUTH_TOKEN}"


# ============ SESSION MANAGEMENT =============

engine = create_engine(
    f"sqlite+{TURSO_URL}?secure=true",
    echo=False,
    connect_args={
        "auth_token": TURSO_AUTH_TOKEN,  # Needed for Turso/libsql
    },
)


def get_session():
    with Session(engine) as session:
        yield session


@contextmanager
def get_session_context():
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            logger.exception("Session error")
            session.rollback()
            logger.info("Rollback done")
            raise


@contextmanager
def transaction_context(session: Session):
    try:
        yield session
        session.commit()
        logger.debug("Transaction completed")
    except Exception:
        session.rollback()
        logger.exception("Transaction reverted")
        raise


# ============ HEALTH CHECK ===============


def test_connection() -> bool:
    """Test Data Base connection."""
    try:
        with get_session_context() as session:
            result = session.exec(text("SELECT 1"))
            logger.info(f"Connection success: {result}")
            return True
    except Exception:
        logger.exception("Error in connection test")
        return False


def health() -> bool:
    return test_connection()


def main():
    for i in range(3):
        start_time = time.perf_counter()

        health()

        end_time = time.perf_counter()
        total_time = end_time - start_time
        print(f"Run {i} Connection time: {total_time:.4f} seconds")


if __name__ == "__main__":
    main()
