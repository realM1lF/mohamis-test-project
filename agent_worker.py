#!/usr/bin/env python3
"""
Agent Worker - Enhanced with Full Memory System.

This worker includes:
1. Customer Context Memories (from markdown files)
2. Git Repository Cache (Redis-based)
3. Episodic Memory (ticket history as vectors)
4. Soul & Rules (agent personality)

Usage:
    python agent_worker.py

Environment variables:
    OPEN_ROUTER_API_KEY - OpenRouter API key for Kimi
    GITHUB_TOKEN - GitHub token for repo access
    REDIS_URL - Redis connection URL
    CHROMA_PERSIST_DIR - ChromaDB persistence directory
    USE_ENHANCED_AGENT=true - Enable enhanced agent with memory (default: false)
"""

import asyncio
import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / ".env", override=True)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.kanban.models import Base
from src.kanban.crud_async import TicketCRUD, CommentCRUD
from src.kanban.schemas import TicketUpdate
from src.git_provider import GitHubProvider
from src.llm import KimiClient

# Check if we can use Enhanced Agent
USE_ENHANCED = os.getenv("USE_ENHANCED_AGENT", "false").lower() == "true"
ENHANCED_ERROR = None

if USE_ENHANCED:
    try:
        # Try to import memory systems (may fail on Python 3.14)
        from src.memory import ChromaMemoryStore, EmbeddingProvider
        from src.git_cache import GitRepoCache
        from src.agents.enhanced_agent import EnhancedDeveloperAgent
        print("🧠 Enhanced Agent loaded - full memory system enabled")
    except Exception as e:
        ENHANCED_ERROR = str(e)[:100]
        USE_ENHANCED = False
        print(f"⚠️  Enhanced Agent unavailable: {ENHANCED_ERROR}")
        print("   Using Basic Agent (limited memory)")
else:
    print("ℹ️  Enhanced Agent disabled. Set USE_ENHANCED_AGENT=true to enable.")

# Import basic agent last to avoid circular imports
from src.agents import DeveloperAgent

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kanban.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


class AgentWorker:
    """Worker that continuously processes tickets."""
    
    def __init__(self):
        self.db = SessionLocal()
        self.ticket_crud = TicketCRUD(self.db)
        self.comment_crud = CommentCRUD(self.db)
        
        # Initialize providers
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise ValueError("GITHUB_TOKEN not set in environment")
        
        self.git_provider = GitHubProvider(github_token)
        
        # Check for API key
        router_key = os.getenv("OPEN_ROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        kimi_key = os.getenv("KIMI_API_KEY")
        
        if not (router_key or kimi_key):
            raise ValueError("No API key found. Set OPEN_ROUTER_API_KEY or KIMI_API_KEY")
        
        self.llm_client = KimiClient()
        
        # Initialize agent
        if USE_ENHANCED:
            self.agent = self._create_enhanced_agent()
        else:
            self.agent = self._create_basic_agent()
        
        self.running = False
    
    def _create_enhanced_agent(self):
        """Create agent with full memory system."""
        # Import here to avoid issues at module level
        from src.memory import ChromaMemoryStore, EmbeddingProvider
        from src.git_cache import GitRepoCache
        from src.agents.enhanced_agent import EnhancedDeveloperAgent
        
        # Redis URL for Git Cache
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        # ChromaDB persistence
        chroma_dir = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
        
        # Create memory components
        embedding_provider = EmbeddingProvider()
        memory_store = ChromaMemoryStore(persist_dir=chroma_dir)
        git_cache = GitRepoCache(self.git_provider, redis_url=redis_url)
        
        return EnhancedDeveloperAgent(
            agent_id="mohami",
            git_provider=self.git_provider,
            llm_client=self.llm_client,
            ticket_crud=self.ticket_crud,
            comment_crud=self.comment_crud,
            embedding_provider=embedding_provider,
            memory_store=memory_store,
            git_cache=git_cache,
        )
    
    def _create_basic_agent(self):
        """Create basic agent without memory systems."""
        return DeveloperAgent(
            agent_id="mohami",
            git_provider=self.git_provider,
            llm_client=self.llm_client,
            ticket_crud=self.ticket_crud,
            comment_crud=self.comment_crud,
        )
    
    async def run(self):
        """Main worker loop."""
        self.running = True
        
        print("=" * 60)
        print("🤖 KI-Mitarbeiter Agent Worker")
        print("=" * 60)
        print(f"\n⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("📡 Polling for tickets every 5 seconds...")
        print("🧠 Memory Systems:")
        if USE_ENHANCED:
            print("   ✓ Customer Context Memories")
            print("   ✓ Git Repository Cache (Redis)")
            print("   ✓ Episodic Memory (ChromaDB)")
            print("   ✓ Soul & Rules (Markdown)")
        else:
            print("   ⚠ Basic mode (limited memory)")
            if ENHANCED_ERROR:
                print(f"   ⚠ Reason: {ENHANCED_ERROR}")
            else:
                print("   ℹ Set USE_ENHANCED_AGENT=true to enable")
        print("🛑 Press Ctrl+C to stop\n")
        
        try:
            while self.running:
                await self._process_cycle()
                await asyncio.sleep(5)  # Poll every 5 seconds
        except KeyboardInterrupt:
            print("\n\n👋 Shutting down...")
        finally:
            self.db.close()
    
    async def _process_cycle(self):
        """Process one cycle of tickets."""
        try:
            # 1. Check for new tickets in backlog
            new_tickets = await self.ticket_crud.list(
                status="backlog",
                agent=None
            )
            
            for ticket in new_tickets:
                print(f"\n📨 New ticket: {ticket.id[:8]} - {ticket.title}")
                print(f"   Customer: {ticket.customer}")
                print(f"   Repository: {ticket.repository}")
                print("   → Starting ORPA workflow...")
                
                await self.agent.process_ticket(ticket.id)
                
                print("   ✅ Complete")
            
            # 2. Check for clarification tickets with new responses
            clarification_tickets = await self.ticket_crud.list(
                status="clarification"
            )
            
            for ticket in clarification_tickets:
                if ticket.agent == "mohami":
                    # Check if there are new comments from user
                    comments = await self.comment_crud.get_by_ticket(ticket.id)
                    
                    # Get last (most recent) comment
                    if comments and len(comments) > 0:
                        last_comment = comments[0]
                        
                        # If last comment is from user (not agent), continue
                        if not last_comment.author.startswith("mohami"):
                            print(f"\n💬 Clarification answered: {ticket.id[:8]}")
                            print(f"   User: {last_comment.author}")
                            print("   → Continuing workflow...")
                            
                            await self.agent.process_ticket(ticket.id)
                            
                            print("   ✅ Complete")
            
            # 3. Check for in_progress tickets with new user feedback
            # (e.g., user reports PR was empty or wrong)
            in_progress_tickets = await self.ticket_crud.list(
                status="in_progress"
            )
            
            for ticket in in_progress_tickets:
                if ticket.agent == "mohami":
                    comments = await self.comment_crud.get_by_ticket(ticket.id)
                    
                    # Get last (most recent) comment
                    if comments and len(comments) > 0:
                        last_comment = comments[0]
                        
                        # If last comment is from user (not agent), re-process
                        if not last_comment.author.startswith("mohami"):
                            print(f"\n🔄 User feedback on in_progress: {ticket.id[:8]}")
                            print(f"   User: {last_comment.author}")
                            print(f"   Feedback: {last_comment.content[:50]}...")
                            print("   → Re-processing...")
                            
                            await self.agent.process_ticket(ticket.id)
                            
                            print("   ✅ Complete")
            
        except Exception as e:
            print(f"\n❌ Error in processing cycle: {e}")
            import traceback
            traceback.print_exc()
    
    async def process_single_ticket(self, ticket_id: str):
        """Process a single ticket immediately."""
        print(f"\n🎯 Processing single ticket: {ticket_id}")
        await self.agent.process_ticket(ticket_id)
        print("✅ Complete")


async def main():
    """Main entry point."""
    worker = AgentWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
