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



# === Phase 1: Learning System CRUD Operations ===

from typing import Dict, Any
from datetime import datetime
from .models import TicketIteration, LearningRecord


class TicketIterationCRUD:
    """CRUD fuer Ticket-Iterationen (Tracking des Agent's Arbeitsverlaufs)."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, iteration_data: Dict[str, Any]) -> TicketIteration:
        """Erstellt eine neue Iteration."""
        db_iteration = TicketIteration(**iteration_data)
        self.db.add(db_iteration)
        self.db.commit()
        self.db.refresh(db_iteration)
        return db_iteration
    
    async def get(self, iteration_id: str) -> Optional[TicketIteration]:
        """Holt eine Iteration nach ID."""
        return self.db.query(TicketIteration).filter(TicketIteration.id == iteration_id).first()
    
    async def get_by_ticket(self, ticket_id: str) -> List[TicketIteration]:
        """Holt alle Iterationen eines Tickets."""
        return (
            self.db.query(TicketIteration)
            .filter(TicketIteration.ticket_id == ticket_id)
            .order_by(TicketIteration.iteration_number)
            .all()
        )
    
    async def update(self, iteration_id: str, update_data: Dict[str, Any]) -> Optional[TicketIteration]:
        """Aktualisiert eine Iteration."""
        iteration = await self.get(iteration_id)
        if iteration:
            for key, value in update_data.items():
                setattr(iteration, key, value)
            self.db.commit()
            self.db.refresh(iteration)
        return iteration
    
    async def delete(self, iteration_id: str) -> bool:
        """Loescht eine Iteration."""
        iteration = await self.get(iteration_id)
        if iteration:
            self.db.delete(iteration)
            self.db.commit()
            return True
        return False


class LearningRecordCRUD:
    """CRUD fuer Learning Records (Gelernte Lessons)."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create(self, learning_data: Dict[str, Any]) -> LearningRecord:
        """Erstellt einen neuen Learning Record."""
        db_learning = LearningRecord(**learning_data)
        self.db.add(db_learning)
        self.db.commit()
        self.db.refresh(db_learning)
        return db_learning
    
    async def get(self, learning_id: str) -> Optional[LearningRecord]:
        """Holt einen Learning Record nach ID."""
        return self.db.query(LearningRecord).filter(LearningRecord.id == learning_id).first()
    
    async def get_by_ticket(self, ticket_id: str) -> List[LearningRecord]:
        """Holt alle Learnings eines Tickets."""
        return (
            self.db.query(LearningRecord)
            .filter(LearningRecord.ticket_id == ticket_id)
            .all()
        )
    
    async def get_by_customer(
        self, 
        customer_id: str, 
        learning_type: Optional[str] = None,
        success: Optional[bool] = None,
        limit: int = 10
    ) -> List[LearningRecord]:
        """Holt Learnings eines Kunden mit optionalen Filtern."""
        query = self.db.query(LearningRecord).filter(LearningRecord.customer_id == customer_id)
        
        if learning_type:
            query = query.filter(LearningRecord.learning_type == learning_type)
        if success is not None:
            query = query.filter(LearningRecord.success == success)
        
        return query.order_by(LearningRecord.created_at.desc()).limit(limit).all()
    
    async def get_anti_patterns(self, customer_id: str, problem_query: str) -> List[LearningRecord]:
        """Holt Anti-Patterns (was hat nicht funktioniert)."""
        return (
            self.db.query(LearningRecord)
            .filter(LearningRecord.customer_id == customer_id)
            .filter(LearningRecord.learning_type == "anti_pattern")
            .filter(LearningRecord.problem.contains(problem_query))
            .all()
        )
    
    async def update(self, learning_id: str, update_data: Dict[str, Any]) -> Optional[LearningRecord]:
        """Aktualisiert einen Learning Record."""
        learning = await self.get(learning_id)
        if learning:
            for key, value in update_data.items():
                setattr(learning, key, value)
            self.db.commit()
            self.db.refresh(learning)
        return learning
    
    async def delete(self, learning_id: str) -> bool:
        """Loescht einen Learning Record."""
        learning = await self.get(learning_id)
        if learning:
            self.db.delete(learning)
            self.db.commit()
            return True
        return False
