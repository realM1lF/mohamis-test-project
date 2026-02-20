"""
CRUD operations for Kanban Board
"""
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy import desc

from .models import Ticket, Comment, TicketStatus
from .schemas import TicketCreate, TicketUpdate, CommentCreate


# Ticket CRUD
def create_ticket(db: Session, ticket: TicketCreate, ticket_id: Optional[str] = None) -> Ticket:
    db_ticket = Ticket(
        id=ticket_id or str(uuid4()),
        title=ticket.title,
        description=ticket.description,
        status=TicketStatus.BACKLOG,
        customer=ticket.customer,
        repository=ticket.repository,
        priority=ticket.priority,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def get_ticket(db: Session, ticket_id: str) -> Optional[Ticket]:
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()


def get_ticket_with_comments(db: Session, ticket_id: str) -> Optional[Ticket]:
    from sqlalchemy.orm import joinedload
    return db.query(Ticket).options(joinedload(Ticket.comments)).filter(Ticket.id == ticket_id).first()


def get_tickets(
    db: Session,
    status: Optional[TicketStatus] = None,
    agent: Optional[str] = None,
    customer: Optional[str] = None,
    repository: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Ticket]:
    query = db.query(Ticket)
    
    if status:
        query = query.filter(Ticket.status == status)
    if agent:
        query = query.filter(Ticket.agent == agent)
    if customer:
        query = query.filter(Ticket.customer == customer)
    if repository:
        query = query.filter(Ticket.repository == repository)
    if priority:
        query = query.filter(Ticket.priority == priority)
    
    return query.order_by(desc(Ticket.created_at)).offset(skip).limit(limit).all()


def update_ticket(db: Session, ticket_id: str, ticket_update: TicketUpdate) -> Optional[Ticket]:
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None
    
    update_data = ticket_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_ticket, field, value)
    
    db_ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def assign_ticket(db: Session, ticket_id: str, agent: Optional[str]) -> Optional[Ticket]:
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None
    
    db_ticket.agent = agent
    db_ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def delete_ticket(db: Session, ticket_id: str) -> bool:
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return False
    
    db.delete(db_ticket)
    db.commit()
    return True


def get_agent_queue(db: Session, agent_id: str) -> List[Ticket]:
    """Get all tickets assigned to an agent, ordered by priority and creation date"""
    return (
        db.query(Ticket)
        .filter(Ticket.agent == agent_id)
        .filter(Ticket.status != TicketStatus.DONE)
        .order_by(
            Ticket.priority.desc(),
            Ticket.created_at.desc()
        )
        .all()
    )


# Comment CRUD
def create_comment(db: Session, ticket_id: str, comment: CommentCreate) -> Optional[Comment]:
    db_ticket = get_ticket(db, ticket_id)
    if not db_ticket:
        return None
    
    db_comment = Comment(
        id=str(uuid4()),
        ticket_id=ticket_id,
        author=comment.author,
        content=comment.content,
        created_at=datetime.utcnow(),
    )
    db.add(db_comment)
    
    # Update ticket's updated_at
    db_ticket.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_comment)
    return db_comment


def get_comments(db: Session, ticket_id: str, skip: int = 0, limit: int = 100) -> List[Comment]:
    return (
        db.query(Comment)
        .filter(Comment.ticket_id == ticket_id)
        .order_by(desc(Comment.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_comment(db: Session, comment_id: str) -> Optional[Comment]:
    return db.query(Comment).filter(Comment.id == comment_id).first()


def delete_comment(db: Session, comment_id: str) -> bool:
    db_comment = get_comment(db, comment_id)
    if not db_comment:
        return False
    
    db.delete(db_comment)
    db.commit()
    return True


# Stats
def get_ticket_stats(db: Session) -> dict:
    """Get basic ticket statistics"""
    total = db.query(Ticket).count()
    by_status = {}
    for status in TicketStatus:
        count = db.query(Ticket).filter(Ticket.status == status).count()
        by_status[status.value] = count
    
    unassigned = db.query(Ticket).filter(Ticket.agent == None).count()
    
    return {
        "total": total,
        "by_status": by_status,
        "unassigned": unassigned,
    }
