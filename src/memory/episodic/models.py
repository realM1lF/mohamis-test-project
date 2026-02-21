"""SQLAlchemy Models for Episodic Memory."""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, String, Text, DateTime, Integer, Float, 
    Boolean, JSON, ForeignKey, ARRAY, UUID as SQLAlchemyUUID
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Conversation(Base):
    """Konversations-Nachrichten mit Embedding."""
    __tablename__ = "conversations"
    
    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(String(255), index=True)
    conversation_id = Column(String(255), nullable=False)
    message_role = Column(String(20), nullable=False)  # user, assistant, system, tool
    message_content = Column(Text, nullable=False)
    message_type = Column(String(50), default="text")  # text, code, image, file
    agent_id = Column(String(100), nullable=False)
    agent_mode = Column(String(50))  # observe, reason, plan, act
    context_snapshot = Column(JSON)  # Vollständiger Kontext
    tools_used = Column(JSON)  # Tool-Aufrufe und Ergebnisse
    created_at = Column(DateTime, default=datetime.utcnow)
    token_count = Column(Integer)
    message_embedding = Column(String)  # VECTOR(1536) - als String gespeichert für SQLAlchemy
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "ticket_id": self.ticket_id,
            "conversation_id": self.conversation_id,
            "message_role": self.message_role,
            "message_content": self.message_content,
            "message_type": self.message_type,
            "agent_id": self.agent_id,
            "agent_mode": self.agent_mode,
            "context_snapshot": self.context_snapshot,
            "tools_used": self.tools_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "token_count": self.token_count
        }


class Ticket(Base):
    """Ticket-Informationen und Historie."""
    __tablename__ = "tickets"
    
    id = Column(String(255), primary_key=True)
    external_id = Column(String(255))  # z.B. GitHub Issue #
    title = Column(String(500), nullable=False)
    description = Column(Text)
    ticket_type = Column(String(50))  # bug, feature, support, task
    priority = Column(String(20))  # critical, high, medium, low
    status = Column(String(30))  # open, in_progress, resolved, closed
    shopware_version = Column(String(20))
    affected_components = Column(JSON)  # ["checkout", "product"]
    affected_plugins = Column(JSON)  # ["SwagPayPal"]
    resolution_summary = Column(Text)
    resolution_type = Column(String(50))  # code_fix, config_change, education
    files_changed = Column(JSON)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime)
    assigned_agent = Column(String(100))
    contributing_agents = Column(JSON)
    resolution_attempts = Column(Integer, default=0)
    customer_satisfaction = Column(Integer)  # 1-5
    description_embedding = Column(String)  # VECTOR(1536)
    
    # Relationships
    episodes = relationship("Episode", back_populates="ticket")
    conversations = relationship("Conversation", foreign_keys=[id], 
                                primaryjoin="Ticket.id == Conversation.ticket_id")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "external_id": self.external_id,
            "title": self.title,
            "description": self.description,
            "ticket_type": self.ticket_type,
            "priority": self.priority,
            "status": self.status,
            "shopware_version": self.shopware_version,
            "affected_components": self.affected_components,
            "affected_plugins": self.affected_plugins,
            "resolution_summary": self.resolution_summary,
            "resolution_type": self.resolution_type,
            "files_changed": self.files_changed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "assigned_agent": self.assigned_agent,
            "contributing_agents": self.contributing_agents,
            "resolution_attempts": self.resolution_attempts,
            "customer_satisfaction": self.customer_satisfaction
        }


class Episode(Base):
    """Wichtige Ereignisse/Episoden (Fehler, Erfolge, Entscheidungen)."""
    __tablename__ = "episodes"
    
    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    episode_type = Column(String(50), nullable=False)  # error, success, decision, milestone
    ticket_id = Column(String(255), ForeignKey("tickets.id"))
    conversation_id = Column(String(255))
    episode_title = Column(String(500), nullable=False)
    episode_description = Column(Text)
    episode_data = Column(JSON)  # Flexibles JSON für typ-spezifische Daten
    preceding_episodes = Column(ARRAY(SQLAlchemyUUID(as_uuid=True)))
    following_episodes = Column(ARRAY(SQLAlchemyUUID(as_uuid=True)))
    agent_id = Column(String(100))
    shopware_version = Column(String(20))
    environment = Column(String(50))  # production, staging, local
    occurred_at = Column(DateTime, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    importance_score = Column(Float)  # 0.0 - 1.0
    retention_until = Column(DateTime)
    episode_embedding = Column(String)  # VECTOR(1536)
    
    # Relationships
    ticket = relationship("Ticket", back_populates="episodes")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "episode_type": self.episode_type,
            "ticket_id": self.ticket_id,
            "conversation_id": self.conversation_id,
            "episode_title": self.episode_title,
            "episode_description": self.episode_description,
            "episode_data": self.episode_data,
            "preceding_episodes": [str(e) for e in self.preceding_episodes] if self.preceding_episodes else [],
            "following_episodes": [str(e) for e in self.following_episodes] if self.following_episodes else [],
            "agent_id": self.agent_id,
            "shopware_version": self.shopware_version,
            "environment": self.environment,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "importance_score": self.importance_score,
            "retention_until": self.retention_until.isoformat() if self.retention_until else None
        }


class LearnedWorkflow(Base):
    """Gelernte Workflows für wiederkehrende Prozesse."""
    __tablename__ = "learned_workflows"
    
    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_name = Column(String(200), nullable=False)
    workflow_description = Column(Text)
    trigger_patterns = Column(JSON, nullable=False)
    trigger_embedding = Column(String)  # VECTOR(1536)
    steps = Column(JSON, nullable=False)  # [{"step": 1, "action": "...", "tool": "..."}]
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    avg_execution_time_minutes = Column(Float)
    applicable_shopware_versions = Column(JSON)  # ["6.5.x", "6.6.x"]
    applicable_customers = Column(JSON)  # Spezifisch oder ["all"]
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime)
    verified_by = Column(String(100))
    verified_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "workflow_name": self.workflow_name,
            "workflow_description": self.workflow_description,
            "trigger_patterns": self.trigger_patterns,
            "steps": self.steps,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "avg_execution_time_minutes": self.avg_execution_time_minutes,
            "applicable_shopware_versions": self.applicable_shopware_versions,
            "applicable_customers": self.applicable_customers,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "verified_by": self.verified_by,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "is_active": self.is_active
        }
    
    @property
    def success_rate(self) -> float:
        if self.execution_count == 0:
            return 0.0
        return self.success_count / self.execution_count


class KnowledgeNode(Base):
    """Knowledge Graph Nodes (Entitäten)."""
    __tablename__ = "knowledge_nodes"
    
    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_type = Column(String(50), nullable=False)  # file, class, function, plugin, concept
    node_name = Column(String(500), nullable=False)
    node_description = Column(Text)
    metadata = Column(JSON)
    node_embedding = Column(String)  # VECTOR(1536)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    outgoing_relations = relationship(
        "KnowledgeRelation",
        foreign_keys="KnowledgeRelation.from_node",
        back_populates="from_node_obj"
    )
    incoming_relations = relationship(
        "KnowledgeRelation",
        foreign_keys="KnowledgeRelation.to_node",
        back_populates="to_node_obj"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "node_type": self.node_type,
            "node_name": self.node_name,
            "node_description": self.node_description,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class KnowledgeRelation(Base):
    """Knowledge Graph Relations."""
    __tablename__ = "knowledge_relations"
    
    id = Column(SQLAlchemyUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_node = Column(SQLAlchemyUUID(as_uuid=True), ForeignKey("knowledge_nodes.id"))
    to_node = Column(SQLAlchemyUUID(as_uuid=True), ForeignKey("knowledge_nodes.id"))
    relation_type = Column(String(100), nullable=False)  # imports, extends, uses, depends_on, solves
    relation_strength = Column(Float)  # 0.0 - 1.0
    evidence = Column(JSON)  # Tickets/Episoden die Relation belegen
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    from_node_obj = relationship(
        "KnowledgeNode",
        foreign_keys=[from_node],
        back_populates="outgoing_relations"
    )
    to_node_obj = relationship(
        "KnowledgeNode",
        foreign_keys=[to_node],
        back_populates="incoming_relations"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "from_node": str(self.from_node),
            "to_node": str(self.to_node),
            "relation_type": self.relation_type,
            "relation_strength": self.relation_strength,
            "evidence": self.evidence,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
