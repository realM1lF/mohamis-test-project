"""Async CRUD wrapper for Agent compatibility."""

from typing import Optional, List
from sqlalchemy.orm import Session

from . import crud
from .models import TicketStatus, Ticket, Comment
from .schemas import TicketCreate, TicketUpdate, CommentCreate


class TicketCRUD:
    """Async wrapper for ticket operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, ticket: TicketCreate, ticket_id: Optional[str] = None) -> Ticket:
        return crud.create_ticket(self.db, ticket, ticket_id)
    
    async def get(self, ticket_id: str) -> Optional[Ticket]:
        return crud.get_ticket(self.db, ticket_id)
    
    async def list(
        self,
        status: Optional[TicketStatus] = None,
        agent: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Ticket]:
        return crud.get_tickets(self.db, status=status, agent=agent, skip=skip, limit=limit)
    
    async def update(self, ticket_id: str, update: TicketUpdate) -> Optional[Ticket]:
        return crud.update_ticket(self.db, ticket_id, update)
    
    async def assign(self, ticket_id: str, agent: Optional[str]) -> Optional[Ticket]:
        return crud.assign_ticket(self.db, ticket_id, agent)
    
    async def delete(self, ticket_id: str) -> bool:
        return crud.delete_ticket(self.db, ticket_id)


class CommentCRUD:
    """Async wrapper for comment operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, ticket_id: str, comment: CommentCreate) -> Optional[Comment]:
        return crud.create_comment(self.db, ticket_id, comment)
    
    async def get(self, comment_id: str) -> Optional[Comment]:
        return crud.get_comment(self.db, comment_id)
    
    async def get_by_ticket(self, ticket_id: str) -> List[Comment]:
        return crud.get_comments(self.db, ticket_id)
    
    async def delete(self, comment_id: str) -> bool:
        return crud.delete_comment(self.db, comment_id)
