import os
import logging
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session, text
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
)

logger = logging.getLogger(__name__)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def run_migrations():
    """Add missing columns to existing tables for backward compatibility."""
    migrations = [
        ("chat_messages", "session_id", "INTEGER"),
        ("chat_messages", "task_data", "TEXT"),
        ("chat_messages", "action_taken", "TEXT"),
    ]
    with engine.connect() as conn:
        for table, column, col_type in migrations:
            # Use information_schema (works on PostgreSQL)
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = :table AND column_name = :column"
            ), {"table": table, "column": column}).fetchone()
            if result is None:
                conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {col_type}'))
                logger.info(f"Migration: added {column} to {table}")
        conn.commit()


def get_session():
    with Session(engine) as session:
        yield session
