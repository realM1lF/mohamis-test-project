"""
SQLAlchemy models for Kanban Board
"""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text, text, Integer, Boolean
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
    
    # Neue Spalten fuer Human Approval (Phase 1)
    human_approved = Column(Boolean, nullable=True)  # True = 👍, False = 👎, None = pending
    human_feedback = Column(Text, nullable=True)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    testing_notes = Column(Text, nullable=True)

    comments = relationship("Comment", back_populates="ticket", cascade="all, delete-orphan")
    iterations = relationship("TicketIteration", back_populates="ticket", cascade="all, delete-orphan")
    learnings = relationship("LearningRecord", back_populates="ticket", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(String, primary_key=True, index=True)
    ticket_id = Column(String, ForeignKey("tickets.id"), nullable=False, index=True)
    author = Column(String, nullable=False)  # "customer" or agent-id
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    ticket = relationship("Ticket", back_populates="comments")


class TicketIteration(Base):
    """Speichert jede ORPA-Iteration fuer besseres Learning."""
    __tablename__ = "ticket_iterations"

    id = Column(String, primary_key=True, index=True)
    ticket_id = Column(String, ForeignKey("tickets.id"), nullable=False, index=True)
    iteration_number = Column(Integer, nullable=False)
    orpa_state = Column(String, nullable=False)  # "observing", "reasoning", "planning", "acting"
    
    # Was wollte der Agent tun?
    intended_action = Column(Text, nullable=True)
    tools_planned = Column(Text, nullable=True)  # JSON-Array
    
    # Was wurde ausgefuehrt?
    tools_executed = Column(Text, nullable=True)  # JSON-Array mit Ergebnissen
    execution_success = Column(Boolean, default=False)
    execution_output = Column(Text, nullable=True)
    
    # War es erfolgreich?
    error_occurred = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    error_type = Column(String, nullable=True)  # "tool_failure", "validation_error", "wrong_approach"
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    ticket = relationship("Ticket", back_populates="iterations")


class LearningRecord(Base):
    """Erweitertes Learning mit Reflection und Failed Attempts."""
    __tablename__ = "learning_records"

    id = Column(String, primary_key=True, index=True)
    ticket_id = Column(String, ForeignKey("tickets.id"), nullable=False, index=True)
    customer_id = Column(String, nullable=False, index=True)
    agent_id = Column(String, nullable=False, index=True)
    
    # Klassifizierung
    learning_type = Column(String, nullable=False)  # "success", "correction", "lesson", "anti_pattern"
    
    # Inhalt
    problem = Column(Text, nullable=False)
    attempted_solution = Column(Text, nullable=True)  # Was wurde zuerst versucht?
    final_solution = Column(Text, nullable=False)  # Was hat funktioniert?
    
    # Reflection (neu)
    reflection = Column(Text, nullable=True)  # Was hat der Agent gelernt?
    key_takeaway = Column(Text, nullable=True)  # Kurze Zusammenfassung
    
    # Failed Attempts Referenz
    iteration_ids = Column(Text, nullable=True)  # JSON-Array von Iteration-IDs
    
    # Metadaten
    success = Column(Boolean, nullable=False)
    iterations_count = Column(Integer, nullable=True)
    tools_used = Column(Text, nullable=True)  # JSON-Array
    human_feedback = Column(Text, nullable=True)  # "Gut gemacht" oder "Fehlerhaft"
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    ticket = relationship("Ticket", back_populates="learnings")


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
        
        # Neue Spalten fuer Learning System (Phase 1)
        if "human_approved" not in existing_columns:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN human_approved BOOLEAN"))
        if "human_feedback" not in existing_columns:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN human_feedback TEXT"))
        if "approved_by" not in existing_columns:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN approved_by TEXT"))
        if "approved_at" not in existing_columns:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN approved_at DATETIME"))
        if "testing_notes" not in existing_columns:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN testing_notes TEXT"))
