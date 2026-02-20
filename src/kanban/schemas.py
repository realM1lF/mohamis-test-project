"""
Pydantic schemas for Kanban Board
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


# Enums
class TicketStatus(str, Enum):
    BACKLOG = "backlog"
    IN_PROGRESS = "in_progress"
    CLARIFICATION = "clarification"
    TESTING = "testing"
    DONE = "done"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Comment schemas
class CommentBase(BaseModel):
    content: str = Field(..., min_length=1)


class CommentCreate(CommentBase):
    author: str = Field(..., min_length=1)


class CommentResponse(CommentBase):
    id: str
    ticket_id: str
    author: str
    created_at: datetime

    class Config:
        from_attributes = True


# Ticket schemas
class TicketBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    customer: str = Field(..., min_length=1)
    repository: str = Field(..., min_length=1)
    priority: TicketPriority = TicketPriority.MEDIUM


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    status: Optional[TicketStatus] = None
    agent: Optional[str] = None
    priority: Optional[TicketPriority] = None


class TicketAssign(BaseModel):
    agent: Optional[str] = None


class TicketResponse(TicketBase):
    id: str
    status: TicketStatus
    agent: Optional[str]
    created_at: datetime
    updated_at: datetime
    comments_count: int = 0

    class Config:
        from_attributes = True


class TicketDetailResponse(TicketResponse):
    comments: List[CommentResponse] = []


# Filter schemas
class TicketFilter(BaseModel):
    status: Optional[TicketStatus] = None
    agent: Optional[str] = None
    customer: Optional[str] = None
    repository: Optional[str] = None
    priority: Optional[TicketPriority] = None


# Webhook schemas
class WebhookTicketCreated(BaseModel):
    id: str
    title: str
    customer: str
    repository: str
    priority: TicketPriority
    created_at: datetime


# Queue response
class AgentQueueResponse(BaseModel):
    agent_id: str
    tickets: List[TicketResponse]
    count: int
