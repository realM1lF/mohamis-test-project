"""Database connection and schema management for Episodic Memory."""

import os
from typing import Optional
from urllib.parse import quote_plus

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text


# Connection settings from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://mohami:mohami@localhost:5432/mohami_memory"
)

# Global engine cache
_engine: Optional[AsyncEngine] = None


def get_engine() -> AsyncEngine:
    """Get or create async database engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            DATABASE_URL,
            echo=False,
            pool_size=10,
            max_overflow=20
        )
    return _engine


def sanitize_schema_name(customer_id: str) -> str:
    """Sanitize customer_id für Schema-Namen (nur alphanumerisch + underscore)."""
    import re
    safe = re.sub(r'[^a-zA-Z0-9_]', '_', customer_id)
    # Muss mit Buchstabe beginnen
    if safe and safe[0].isdigit():
        safe = "cust_" + safe
    return f"customer_{safe}"


async def init_customer_schema(customer_id: str) -> str:
    """Initialize PostgreSQL schema for a customer.
    
    Creates:
    - Schema with sanitized name
    - Tables: conversations, tickets, episodes, learned_workflows, knowledge_nodes, knowledge_relations
    - Indexes including pgvector indexes
    
    Args:
        customer_id: Customer identifier
        
    Returns:
        Schema name
    """
    engine = get_engine()
    schema_name = sanitize_schema_name(customer_id)
    
    async with engine.begin() as conn:
        # Create schema
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
        
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        
        # Create tables
        
        # 1. Conversations table
        await conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".conversations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                ticket_id VARCHAR(255),
                conversation_id VARCHAR(255) NOT NULL,
                message_role VARCHAR(20) NOT NULL,
                message_content TEXT NOT NULL,
                message_type VARCHAR(50) DEFAULT 'text',
                agent_id VARCHAR(100) NOT NULL,
                agent_mode VARCHAR(50),
                context_snapshot JSONB,
                tools_used JSONB,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                token_count INTEGER,
                message_embedding VECTOR(1536)
            )
        """))
        
        # 2. Tickets table
        await conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".tickets (
                id VARCHAR(255) PRIMARY KEY,
                external_id VARCHAR(255),
                title VARCHAR(500) NOT NULL,
                description TEXT,
                ticket_type VARCHAR(50),
                priority VARCHAR(20),
                status VARCHAR(30),
                shopware_version VARCHAR(20),
                affected_components JSONB,
                affected_plugins JSONB,
                resolution_summary TEXT,
                resolution_type VARCHAR(50),
                files_changed JSONB,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                resolved_at TIMESTAMP,
                assigned_agent VARCHAR(100),
                contributing_agents JSONB,
                resolution_attempts INTEGER DEFAULT 0,
                customer_satisfaction INTEGER,
                description_embedding VECTOR(1536)
            )
        """))
        
        # 3. Episodes table
        await conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".episodes (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                episode_type VARCHAR(50) NOT NULL,
                ticket_id VARCHAR(255),
                conversation_id VARCHAR(255),
                episode_title VARCHAR(500) NOT NULL,
                episode_description TEXT,
                episode_data JSONB,
                preceding_episodes UUID[],
                following_episodes UUID[],
                agent_id VARCHAR(100),
                shopware_version VARCHAR(20),
                environment VARCHAR(50),
                occurred_at TIMESTAMP NOT NULL,
                recorded_at TIMESTAMP DEFAULT NOW(),
                importance_score FLOAT,
                retention_until TIMESTAMP,
                episode_embedding VECTOR(1536)
            )
        """))
        
        # 4. Learned Workflows table
        await conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".learned_workflows (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                workflow_name VARCHAR(200) NOT NULL,
                workflow_description TEXT,
                trigger_patterns JSONB NOT NULL,
                trigger_embedding VECTOR(1536),
                steps JSONB NOT NULL,
                execution_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                avg_execution_time_minutes FLOAT,
                applicable_shopware_versions JSONB,
                applicable_customers JSONB,
                created_at TIMESTAMP DEFAULT NOW(),
                last_used_at TIMESTAMP,
                verified_by VARCHAR(100),
                verified_at TIMESTAMP,
                is_active BOOLEAN DEFAULT true
            )
        """))
        
        # 5. Knowledge Nodes table
        await conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".knowledge_nodes (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                node_type VARCHAR(50) NOT NULL,
                node_name VARCHAR(500) NOT NULL,
                node_description TEXT,
                metadata JSONB,
                node_embedding VECTOR(1536),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        
        # 6. Knowledge Relations table
        await conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS "{schema_name}".knowledge_relations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                from_node UUID REFERENCES "{schema_name}".knowledge_nodes(id),
                to_node UUID REFERENCES "{schema_name}".knowledge_nodes(id),
                relation_type VARCHAR(100) NOT NULL,
                relation_strength FLOAT,
                evidence JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        
        # Create indexes
        
        # Conversations indexes
        await conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_conversations_ticket 
            ON "{schema_name}".conversations(ticket_id)
        """))
        await conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_conversations_created 
            ON "{schema_name}".conversations(created_at DESC)
        """))
        await conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_conversations_role 
            ON "{schema_name}".conversations(message_role)
        """))
        
        # Tickets indexes
        await conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_tickets_status 
            ON "{schema_name}".tickets(status)
        """))
        await conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_tickets_type 
            ON "{schema_name}".tickets(ticket_type)
        """))
        await conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_tickets_created 
            ON "{schema_name}".tickets(created_at DESC)
        """))
        await conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_tickets_version 
            ON "{schema_name}".tickets(shopware_version)
        """))
        
        # Episodes indexes
        await conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_episodes_ticket 
            ON "{schema_name}".episodes(ticket_id)
        """))
        await conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_episodes_type 
            ON "{schema_name}".episodes(episode_type)
        """))
        await conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_episodes_occurred 
            ON "{schema_name}".episodes(occurred_at DESC)
        """))
        await conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_episodes_importance 
            ON "{schema_name}".episodes(importance_score DESC)
        """))
        
        # Knowledge indexes
        await conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_type 
            ON "{schema_name}".knowledge_nodes(node_type)
        """))
        await conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_knowledge_relations_from 
            ON "{schema_name}".knowledge_relations(from_node)
        """))
        await conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_knowledge_relations_to 
            ON "{schema_name}".knowledge_relations(to_node)
        """))
        
        # Workflow indexes
        await conn.execute(text(f"""
            CREATE INDEX IF NOT EXISTS idx_workflows_active 
            ON "{schema_name}".learned_workflows(is_active)
        """))
    
    return schema_name


async def get_session(customer_id: str) -> AsyncSession:
    """Get database session for customer."""
    engine = get_engine()
    schema_name = sanitize_schema_name(customer_id)
    
    # Create session with schema context
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    session = async_session()
    # Set search path for this session
    await session.execute(text(f'SET search_path TO "{schema_name}", public'))
    
    return session


async def check_schema_exists(customer_id: str) -> bool:
    """Check if schema exists for customer."""
    engine = get_engine()
    schema_name = sanitize_schema_name(customer_id)
    
    async with engine.connect() as conn:
        result = await conn.execute(
            text("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = :schema
            """),
            {"schema": schema_name}
        )
        return result.scalar() is not None
