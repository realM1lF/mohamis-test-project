#!/usr/bin/env python3
"""
Agent Worker - Mohami KI-Mitarbeiter.

Unterstützt zwei Modi:
- INTELLIGENT (neu): Tool-Use Framework + 4-Schichten Memory
- LEGACY (Fallback): Basis DeveloperAgent

Usage:
    python agent_worker.py

Environment variables:
    USE_INTELLIGENT_AGENT - "true" für neuen Agent, "false" für Legacy (default: true)
    OPEN_ROUTER_API_KEY - OpenRouter API key for Kimi
    GITHUB_TOKEN - GitHub token for repo access
    REDIS_URL - Redis connection URL
    CHROMA_PERSIST_DIR - ChromaDB persistence directory
    USE_ENHANCED_AGENT - Legacy: Enable enhanced agent with memory (default: false)
"""

import asyncio
import os
import sys
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any

from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / ".env", override=True)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.kanban.models import Base, ensure_kanban_schema
from src.kanban.crud_async import TicketCRUD, CommentCRUD
from src.kanban.schemas import TicketUpdate, CommentCreate
from src.git_provider import GitHubProvider
from src.llm import KimiClient
from src.agents.agent_types import AgentResult

# ============================================================================
# CONFIG SWITCH: Intelligent Agent vs Legacy
# ============================================================================
USE_INTELLIGENT_AGENT = os.getenv("USE_INTELLIGENT_AGENT", "true").lower() == "true"

# Track import errors for logging
INTELLIGENT_ERROR: Optional[str] = None
ENHANCED_ERROR: Optional[str] = None

agent_mode: str = "unknown"

# ============================================================================
# AGENT IMPORT LOGIC with Graceful Fallback
# ============================================================================

if USE_INTELLIGENT_AGENT:
    try:
        from src.agents.intelligent_agent import IntelligentAgent
        agent_mode = "INTELLIGENT"
        print("🧠 IntelligentAgent loaded - Tool-Use + 4-Layer Memory enabled")
    except Exception as e:
        INTELLIGENT_ERROR = str(e)[:100]
        print(f"⚠️  IntelligentAgent not available: {INTELLIGENT_ERROR}")
        print(f"   Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        print("   Falling back to legacy agents...")
        USE_INTELLIGENT_AGENT = False


# Fallback chain if IntelligentAgent not available
if not USE_INTELLIGENT_AGENT:
    USE_ENHANCED = os.getenv("USE_ENHANCED_AGENT", "false").lower() == "true"
    
    if USE_ENHANCED:
        try:
            from src.agents.enhanced_developer_agent import ToolUseDeveloperAgent
            agent_mode = "TOOL-USE"
            print("🔧 ToolUseDeveloperAgent loaded - Tool-Use Framework enabled")
        except Exception as e:
            ENHANCED_ERROR = str(e)[:100]
            print(f"⚠️  ToolUseDeveloperAgent unavailable: {ENHANCED_ERROR}")
            USE_ENHANCED = False
    
    if not USE_ENHANCED:
        from src.agents import DeveloperAgent
        agent_mode = "LEGACY"
        print("📦 DeveloperAgent loaded - Basic mode (limited features)")

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kanban.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)
ensure_kanban_schema(engine)


class AgentWorker:
    """Worker that continuously processes tickets with configurable agent."""
    
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
        
        # Initialize agent based on selected mode
        self.agent = self._create_agent()
        self.running = False
        self._processing: set = set()
        self.stale_working_minutes = int(os.getenv("AGENT_STALE_WORKING_MINUTES", "15"))
    
    def _create_agent(self):
        """Create the appropriate agent based on mode."""
        if agent_mode == "INTELLIGENT":
            return self._create_intelligent_agent()
        elif agent_mode == "TOOL-USE":
            return self._create_tool_use_agent()
        else:
            return self._create_legacy_agent()
    
    def _create_intelligent_agent(self):
        """Create the new IntelligentAgent with full capabilities."""
        from src.agents.intelligent_agent import IntelligentAgent, AgentConfig
        
        config = AgentConfig(
            customer_id=os.getenv("DEFAULT_CUSTOMER_ID", "default"),
            max_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "5")),
            enable_memory=True,
            enable_workspace=True,
        )
        return IntelligentAgent(
            "mohami", config,
            ticket_crud=self.ticket_crud,
            comment_crud=self.comment_crud,
            git_provider=self.git_provider,
        )
    
    def _create_tool_use_agent(self):
        """Create ToolUseDeveloperAgent (fallback level 1)."""
        from src.agents.enhanced_developer_agent import ToolUseDeveloperAgent
        
        return ToolUseDeveloperAgent(
            agent_id="mohami",
            git_provider=self.git_provider,
            llm_client=self.llm_client,
            ticket_crud=self.ticket_crud,
            comment_crud=self.comment_crud,
        )
    
    def _create_legacy_agent(self):
        """Create basic DeveloperAgent (fallback level 2)."""
        from src.agents import DeveloperAgent
        
        return DeveloperAgent(
            agent_id="mohami",
            git_provider=self.git_provider,
            llm_client=self.llm_client,
            ticket_crud=self.ticket_crud,
            comment_crud=self.comment_crud,
        )

    def _get_assigned_customers(self, agent_id: str) -> list[str]:
        """Read clients list from agents/{agent_id}/config.yaml.

        Empty/missing list means unrestricted for backward compatibility.
        """
        if not agent_id:
            return []
        cfg_path = Path(__file__).parent / "agents" / agent_id / "config.yaml"
        if not cfg_path.exists():
            return []
        try:
            raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            clients = raw.get("clients", [])
            if isinstance(clients, list):
                return [str(c).strip() for c in clients if str(c).strip()]
        except Exception:
            pass
        return []

    def _agent_can_process_customer(self, agent_id: str, customer_id: str) -> bool:
        if not agent_id or not customer_id:
            return True
        assigned = self._get_assigned_customers(agent_id)
        if not assigned:
            return True
        return customer_id in assigned

    async def _reject_unassigned_ticket(self, ticket):
        """Move invalid agent/customer assignments to clarification with system comment."""
        msg = (
            f"⚠️ Agent '{ticket.agent}' ist nicht für Kunde '{ticket.customer}' zugewiesen. "
            "Bitte passenden KI-Mitarbeiter wählen oder clients-Zuordnung in "
            f"agents/{ticket.agent}/config.yaml ergänzen."
        )
        try:
            comments = await self.comment_crud.get_by_ticket(ticket.id)
            already = any(
                c.author == "system" and "nicht für Kunde" in (c.content or "")
                for c in comments
            )
            if not already:
                await self.comment_crud.create(
                    ticket.id,
                    CommentCreate(author="system", content=msg),
                )
            await self.ticket_crud.update(ticket.id, TicketUpdate(status="clarification"))
        except Exception as e:
            print(f"   ⚠️ Could not move invalid assignment to clarification: {e}")

    async def _set_agent_working(self, ticket_id: str, is_working: bool):
        """Set/clear activity marker so UI can show agent progress."""
        try:
            await self.ticket_crud.update(
                ticket_id,
                TicketUpdate(
                    agent_working_since=(datetime.utcnow() if is_working else None)
                ),
            )
        except Exception as e:
            print(f"   ⚠️ Could not update agent activity marker for {ticket_id[:8]}: {e}")

    def _is_stale_working(self, ticket) -> bool:
        if not getattr(ticket, "agent_working_since", None):
            return False
        cutoff = datetime.utcnow() - timedelta(minutes=max(1, self.stale_working_minutes))
        return ticket.agent_working_since < cutoff

    async def _mark_processing_error(self, ticket_id: str, message: str):
        """Move ticket to clarification with a user-visible system message."""
        try:
            await self.comment_crud.create(
                ticket_id,
                CommentCreate(
                    author="system",
                    content=(
                        "⚠️ Verarbeitung wurde abgebrochen. "
                        f"{message}\n\nBitte Ticket erneut auf 'In Progress' setzen."
                    ),
                ),
            )
            await self.ticket_crud.update(ticket_id, TicketUpdate(status="clarification"))
        except Exception as e:
            print(f"   ⚠️ Could not mark processing error for {ticket_id[:8]}: {e}")

    def _is_user_reply(self, author: str, agent_id: str) -> bool:
        """True only for human/user replies, not agent or system automation."""
        if not author:
            return False
        if author == "system":
            return False
        if agent_id and author.startswith(agent_id):
            return False
        return True
    
    async def run(self):
        """Main worker loop."""
        self.running = True
        
        print("=" * 60)
        print("🤖 Mohami Agent Worker")
        print("=" * 60)
        print(f"\n⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("📡 Polling for tickets every 5 seconds...")
        
        # Show which mode is active
        print("\n🎛️  Agent Mode:")
        if agent_mode == "INTELLIGENT":
            print("   🧠 INTELLIGENT (Tool-Use + 4-Layer Memory)")
            print("   ✓ Tool Registry with 8+ Tools")
            print("   ✓ Short, Session, Long & Episodic Memory")
            print("   ✓ Workspace Management (DDEV)")
        elif agent_mode == "TOOL-USE":
            print("   🔧 TOOL-USE (Tool Framework)")
            print("   ✓ Dynamic Tool Selection")
            print("   ✓ Tool Execution Loop")
            print("   ⚠ Limited Memory Features")
        elif agent_mode == "LEGACY":
            print("   📦 LEGACY (Basic)")
            print("   ✓ Core ORPA Workflow")
            print("   ⚠ No Tool-Use")
            print("   ⚠ No Advanced Memory")
        else:
            print(f"   ❓ UNKNOWN MODE: {agent_mode}")
        
        # Show fallback info if applicable
        if INTELLIGENT_ERROR:
            print(f"\n⚠️  Fallback reason: IntelligentAgent import failed")
            print(f"   Error: {INTELLIGENT_ERROR}")
        if ENHANCED_ERROR:
            print(f"\n⚠️  Fallback reason: EnhancedAgent import failed")
            print(f"   Error: {ENHANCED_ERROR}")
        
        print("\n🛑 Press Ctrl+C to stop\n")
        
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
            # 1. Check for in_progress tickets assigned to an agent (user moved them from backlog)
            in_progress_tickets = await self.ticket_crud.list(
                status="in_progress",
            )
            
            for ticket in in_progress_tickets:
                if not ticket.agent:
                    continue
                if ticket.id in self._processing:
                    continue
                if not self._agent_can_process_customer(ticket.agent, ticket.customer):
                    print(
                        f"\n🚫 Invalid assignment: ticket {ticket.id[:8]} agent={ticket.agent} "
                        f"customer={ticket.customer}"
                    )
                    await self._reject_unassigned_ticket(ticket)
                    continue
                if ticket.agent_working_since and not self._is_stale_working(ticket):
                    # Another worker instance may still be actively processing this ticket.
                    continue
                if ticket.agent_working_since and self._is_stale_working(ticket):
                    print(
                        f"\n♻️ Recover stale ticket: {ticket.id[:8]} "
                        f"(older than {self.stale_working_minutes}m)"
                    )
                    await self._set_agent_working(ticket.id, False)
                
                # Check if agent already posted a comment (= already started working)
                comments = await self.comment_crud.get_by_ticket(ticket.id)
                agent_comments = [c for c in comments if c.author == ticket.agent]
                last_comment = comments[0] if comments else None
                if agent_comments and (
                    not last_comment
                    or last_comment.author == "system"
                    or last_comment.author.startswith(ticket.agent)
                ):
                    continue
                
                self._processing.add(ticket.id)
                print(f"\n📨 Ticket ready: {ticket.id[:8]} - {ticket.title}")
                print(f"   Customer: {ticket.customer}")
                print(f"   Repository: {ticket.repository}")
                print(f"   Agent: {ticket.agent} ({agent_mode} mode)")
                print("   → Starting ORPA workflow...")
                
                ticket_data = {
                    "title": ticket.title,
                    "description": ticket.description,
                    "customer_id": ticket.customer,
                    "repository": ticket.repository,
                    "branch": ticket.active_branch,
                    "metadata": {
                        "active_pr_url": ticket.active_pr_url,
                        "active_pr_number": ticket.active_pr_number,
                    },
                }
                await self._set_agent_working(ticket.id, True)
                try:
                    result = await self.agent.process_ticket(ticket.id, ticket_data)
                except Exception as e:
                    print(f"   ❌ Processing failed: {e}")
                    await self._mark_processing_error(ticket.id, f"Fehler: {e}")
                    continue
                finally:
                    self._processing.discard(ticket.id)
                    await self._set_agent_working(ticket.id, False)
                
                if isinstance(result, AgentResult):
                    if result.success:
                        print("   ✅ Complete → Testing")
                        await self.ticket_crud.update(ticket.id, TicketUpdate(status="testing"))
                    elif result.final_state and "clarification" in str(result.final_state).lower():
                        print("   ❓ Needs clarification")
                        await self.ticket_crud.update(ticket.id, TicketUpdate(status="clarification"))
                    else:
                        print(f"   ❌ Failed: {result.message}")
                        await self._mark_processing_error(
                            ticket.id,
                            result.message or "Unbekannter Fehler beim Bearbeiten.",
                        )
                else:
                    print("   ✅ Complete → Testing")
                    await self.ticket_crud.update(ticket.id, TicketUpdate(status="testing"))
            
            # 2. Check for clarification tickets with new responses
            clarification_tickets = await self.ticket_crud.list(
                status="clarification"
            )
            
            for ticket in clarification_tickets:
                if not ticket.agent:
                    continue
                if ticket.id in self._processing:
                    continue
                if not self._agent_can_process_customer(ticket.agent, ticket.customer):
                    print(
                        f"\n🚫 Invalid assignment: ticket {ticket.id[:8]} agent={ticket.agent} "
                        f"customer={ticket.customer}"
                    )
                    await self._reject_unassigned_ticket(ticket)
                    continue
                
                comments = await self.comment_crud.get_by_ticket(ticket.id)
                if comments and len(comments) > 0:
                    last_comment = comments[0]
                    
                    if self._is_user_reply(last_comment.author, ticket.agent):
                        self._processing.add(ticket.id)
                        print(f"\n💬 Clarification answered: {ticket.id[:8]}")
                        print(f"   User: {last_comment.author}")
                        print("   → Continuing workflow...")
                        
                        await self.ticket_crud.update(ticket.id, TicketUpdate(status="in_progress"))
                        
                        ticket_data = {
                            "title": ticket.title,
                            "description": (
                                ticket.description
                                + f"\n\n--- Rückfrage-Antwort ({last_comment.author}) ---\n"
                                + last_comment.content
                            ),
                            "customer_id": ticket.customer,
                            "repository": ticket.repository,
                            "branch": ticket.active_branch,
                            "metadata": {
                                "active_pr_url": ticket.active_pr_url,
                                "active_pr_number": ticket.active_pr_number,
                            },
                        }
                        await self._set_agent_working(ticket.id, True)
                        try:
                            result = await self.agent.process_ticket(ticket.id, ticket_data)
                        except Exception as e:
                            print(f"   ❌ Clarification processing failed: {e}")
                            await self._mark_processing_error(ticket.id, f"Fehler: {e}")
                            continue
                        finally:
                            self._processing.discard(ticket.id)
                            await self._set_agent_working(ticket.id, False)
                        
                        if isinstance(result, AgentResult):
                            if result.success:
                                print("   ✅ Complete → Testing")
                                await self.ticket_crud.update(ticket.id, TicketUpdate(status="testing"))
                            elif result.final_state and "clarification" in str(result.final_state).lower():
                                print("   ❓ Needs clarification")
                                await self.ticket_crud.update(ticket.id, TicketUpdate(status="clarification"))
                            else:
                                print(f"   ❌ Failed: {result.message}")
                                await self._mark_processing_error(
                                    ticket.id,
                                    result.message or "Unbekannter Fehler beim Bearbeiten.",
                                )
                        else:
                            print("   ✅ Complete → Testing")
                            await self.ticket_crud.update(ticket.id, TicketUpdate(status="testing"))
            
            # 3. Check for testing tickets with user feedback (re-work request)
            testing_tickets = await self.ticket_crud.list(status="testing")
            
            for ticket in testing_tickets:
                if not ticket.agent:
                    continue
                if ticket.id in self._processing:
                    continue
                if not self._agent_can_process_customer(ticket.agent, ticket.customer):
                    print(
                        f"\n🚫 Invalid assignment: ticket {ticket.id[:8]} agent={ticket.agent} "
                        f"customer={ticket.customer}"
                    )
                    await self._reject_unassigned_ticket(ticket)
                    continue
                
                comments = await self.comment_crud.get_by_ticket(ticket.id)
                if not comments:
                    continue
                
                last_comment = comments[0]
                if not self._is_user_reply(last_comment.author, ticket.agent):
                    continue
                
                self._processing.add(ticket.id)
                print(f"\n🔄 Testing feedback: {ticket.id[:8]}")
                print(f"   User: {last_comment.author}")
                print(f"   Feedback: {last_comment.content[:80]}...")
                print("   → Re-processing...")
                
                await self.ticket_crud.update(ticket.id, TicketUpdate(status="in_progress"))
                
                ticket_data = {
                    "title": ticket.title,
                    "description": (
                        ticket.description
                        + f"\n\n--- Testing-Feedback ({last_comment.author}) ---\n"
                        + last_comment.content
                    ),
                    "customer_id": ticket.customer,
                    "repository": ticket.repository,
                    "branch": ticket.active_branch,
                    "metadata": {
                        "active_pr_url": ticket.active_pr_url,
                        "active_pr_number": ticket.active_pr_number,
                    },
                }
                await self._set_agent_working(ticket.id, True)
                try:
                    result = await self.agent.process_ticket(ticket.id, ticket_data)
                except Exception as e:
                    print(f"   ❌ Re-processing failed: {e}")
                    await self._mark_processing_error(ticket.id, f"Fehler: {e}")
                    continue
                finally:
                    self._processing.discard(ticket.id)
                    await self._set_agent_working(ticket.id, False)
                
                if isinstance(result, AgentResult):
                    if result.success:
                        print("   ✅ Complete → Testing")
                        await self.ticket_crud.update(ticket.id, TicketUpdate(status="testing"))
                    elif result.final_state and "clarification" in str(result.final_state).lower():
                        print("   ❓ Needs clarification")
                        await self.ticket_crud.update(ticket.id, TicketUpdate(status="clarification"))
                    else:
                        print(f"   ❌ Failed: {result.message}")
                        await self._mark_processing_error(
                            ticket.id,
                            result.message or "Unbekannter Fehler beim Bearbeiten.",
                        )
                else:
                    print("   ✅ Complete → Testing")
                    await self.ticket_crud.update(ticket.id, TicketUpdate(status="testing"))
            
        except Exception as e:
            print(f"\n❌ Error in processing cycle: {e}")
            import traceback
            traceback.print_exc()
    
    async def process_single_ticket(self, ticket_id: str):
        """Process a single ticket immediately."""
        print(f"\n🎯 Processing single ticket: {ticket_id}")
        print(f"   Agent mode: {agent_mode}")
        
        # Get ticket data for passing to agent
        ticket = await self.ticket_crud.get(ticket_id)
        if ticket:
            if not self._agent_can_process_customer("mohami", ticket.customer):
                print(
                    f"🚫 Agent 'mohami' is not assigned to customer '{ticket.customer}'. "
                    "Moving ticket to clarification."
                )
                await self.ticket_crud.update(ticket_id, TicketUpdate(status="clarification"))
                await self.comment_crud.create(
                    ticket_id,
                    CommentCreate(
                        author="system",
                        content=(
                            "⚠️ Agent 'mohami' ist nicht für diesen Kunden zugewiesen. "
                            "Bitte clients-Zuordnung in agents/mohami/config.yaml prüfen."
                        ),
                    ),
                )
                return
            # Claim ticket before processing
            await self.ticket_crud.update(ticket_id, TicketUpdate(
                status="in_progress",
                agent="mohami",
            ))
            
            ticket_data = {
                "title": ticket.title,
                "description": ticket.description,
                "customer_id": ticket.customer,
                "repository": ticket.repository,
                "branch": ticket.active_branch,
                "metadata": {
                    "active_pr_url": ticket.active_pr_url,
                    "active_pr_number": ticket.active_pr_number,
                },
            }
            await self._set_agent_working(ticket_id, True)
            try:
                result = await self.agent.process_ticket(ticket_id, ticket_data)
            finally:
                await self._set_agent_working(ticket_id, False)
            
            # Handle result if available (IntelligentAgent returns AgentResult)
            if isinstance(result, AgentResult):
                if result.success:
                    print("✅ Complete → Testing")
                    await self.ticket_crud.update(ticket.id, TicketUpdate(status="testing"))
                elif result.final_state and "clarification" in str(result.final_state).lower():
                    print("❓ Needs clarification")
                    await self.ticket_crud.update(ticket.id, TicketUpdate(status="clarification"))
                else:
                    print(f"❌ Failed: {result.message}")
                    await self._mark_processing_error(
                        ticket.id,
                        result.message or "Unbekannter Fehler beim Bearbeiten.",
                    )
            else:
                print("✅ Complete → Testing")
                await self.ticket_crud.update(ticket.id, TicketUpdate(status="testing"))
        else:
            print(f"❌ Ticket not found: {ticket_id}")


async def main():
    """Main entry point."""
    worker = AgentWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
