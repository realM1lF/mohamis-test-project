"""
SQLAlchemy models for Kanban Board
"""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text
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
