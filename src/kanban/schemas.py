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
    active_branch: Optional[str] = None
    active_pr_url: Optional[str] = None
    active_pr_number: Optional[str] = None
    agent_working_since: Optional[datetime] = None
    priority: Optional[TicketPriority] = None


class TicketAssign(BaseModel):
    agent: Optional[str] = None


class TicketResponse(TicketBase):
    id: str
    status: TicketStatus
    agent: Optional[str]
    active_branch: Optional[str] = None
    active_pr_url: Optional[str] = None
    active_pr_number: Optional[str] = None
    agent_working_since: Optional[datetime] = None
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


# Chat schemas
class ChatMessageRequest(BaseModel):
    agent_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    reply: str
    session_id: str



# === Phase 1: Learning System Enhancement Schemas ===

class TicketApproval(BaseModel):
    """Schema fuer menschlichen Approval."""
    approved: bool  # True = 👍, False = 👎
    feedback: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    request_reflection: bool = True


class ChangeRequest(BaseModel):
    """Schema fuer Aenderungsanfragen."""
    feedback: str
    priority: str = "normal"  # "low", "normal", "high"
    back_to_status: str = "in_progress"


class IterationRecord(BaseModel):
    """Schema fuer Ticket-Iterationen."""
    id: str
    ticket_id: str
    iteration_number: int
    orpa_state: str  # "observing", "reasoning", "planning", "acting"
    intended_action: Optional[str] = None
    tools_planned: List[str] = []
    tools_executed: List[dict] = []
    execution_success: bool
    error_occurred: bool = False
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class LearningRecordResponse(BaseModel):
    """Schema fuer Learning Records."""
    id: str
    ticket_id: str
    customer_id: str
    agent_id: str
    learning_type: str  # "success", "correction", "lesson", "anti_pattern"
    problem: str
    attempted_solution: Optional[str] = None
    final_solution: str
    reflection: Optional[str] = None
    key_takeaway: Optional[str] = None
    success: bool
    iterations_count: Optional[int] = None
    tools_used: List[str] = []
    human_feedback: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Erweiterte Ticket Schemas
class TicketUpdateEnhanced(TicketUpdate):
    """Erweitertes TicketUpdate mit Approval-Feldern."""
    human_approved: Optional[bool] = None
    human_feedback: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    testing_notes: Optional[str] = None


class TicketResponseEnhanced(TicketResponse):
    """Erweitertes TicketResponse mit Approval-Feldern."""
    human_approved: Optional[bool] = None
    human_feedback: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    testing_notes: Optional[str] = None
    iterations: List[IterationRecord] = []
    learnings: List[LearningRecordResponse] = []
    
    class Config:
        from_attributes = True


class TicketDetailResponseEnhanced(TicketDetailResponse):
    """Erweitertes TicketDetail mit Learning-Info."""
    human_approved: Optional[bool] = None
    human_feedback: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    testing_notes: Optional[str] = None
    iterations: List[IterationRecord] = []
    learnings: List[LearningRecordResponse] = []
    
    class Config:
        from_attributes = True
