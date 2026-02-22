"""
SQLAlchemy models for Kanban Board
"""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class TicketStatus(str, PyEnum):
    BACKLOG = "backlog"           # Neu eingetroffen
    IN_PROGRESS = "in_progress"   # Agent bearbeitet
    CLARIFICATION = "clarification"  # Rückfrage gestellt
    TESTING = "testing"           # Zum Testen bereit
    DONE = "done"                 # Fertig


class TicketPriority(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.BACKLOG, nullable=False)
    customer = Column(String, nullable=False, index=True)
    repository = Column(String, nullable=False, index=True)
    agent = Column(String, nullable=True, index=True)
    active_branch = Column(String, nullable=True)
    active_pr_url = Column(String, nullable=True)
    active_pr_number = Column(String, nullable=True)
    agent_working_since = Column(DateTime, nullable=True)
    priority = Column(Enum(TicketPriority), default=TicketPriority.MEDIUM, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    comments = relationship("Comment", back_populates="ticket", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(String, primary_key=True, index=True)
    ticket_id = Column(String, ForeignKey("tickets.id"), nullable=False, index=True)
    author = Column(String, nullable=False)  # "customer" or agent-id
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ticket = relationship("Ticket", back_populates="comments")


def ensure_kanban_schema(engine):
    """Apply lightweight schema migrations for SQLite deployments.

    Adds missing columns to keep existing local DB files compatible.
    """
    with engine.begin() as conn:
        table_exists = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='tickets'")
        ).fetchone()
        if not table_exists:
            return

        result = conn.execute(text("PRAGMA table_info(tickets)"))
        existing_columns = {row[1] for row in result.fetchall()}
        if "active_branch" not in existing_columns:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN active_branch TEXT"))
        if "active_pr_url" not in existing_columns:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN active_pr_url TEXT"))
        if "active_pr_number" not in existing_columns:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN active_pr_number TEXT"))
        if "agent_working_since" not in existing_columns:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN agent_working_since DATETIME"))
