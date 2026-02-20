"""Enhanced Developer Agent with full memory system."""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from ..git_provider import GitProvider
from ..git_cache import GitRepoCache
from ..kanban.crud_async import TicketCRUD, CommentCRUD
from ..kanban.schemas import TicketUpdate, CommentCreate
from ..llm.kimi_client import KimiClient, Message
from ..memory import ChromaMemoryStore, EmbeddingProvider, CustomerContextManager, EpisodicMemory
from ..agent_config import AgentConfigLoader


class AgentState(Enum):
    """Agent execution states."""
    IDLE = "idle"
    OBSERVING = "observing"
    REASONING = "reasoning"
    PLANNING = "planning"
    ACTING = "acting"


@dataclass
class AgentContext:
    """Context for the agent execution."""
    customer: str
    repository: str
    ticket_id: str
    ticket_title: str
    ticket_description: str
    project_type: str = "python"
    tech_stack: Dict = field(default_factory=dict)
    conversation_history: List[Dict] = field(default_factory=list)
    files_read: List[str] = field(default_factory=list)
    is_empty_repo: bool = True
    plan: Optional[str] = None


class EnhancedDeveloperAgent:
    """Developer Agent with full memory and context system."""
    
    def __init__(
        self,
        agent_id: str,
        git_provider: GitProvider,
        llm_client: KimiClient,
        ticket_crud: TicketCRUD,
        comment_crud: CommentCRUD,
        # New memory components
        embedding_provider: Optional[EmbeddingProvider] = None,
        memory_store: Optional[ChromaMemoryStore] = None,
        git_cache: Optional[GitRepoCache] = None,
    ):
        self.agent_id = agent_id
        self.git = git_provider
        self.llm = llm_client
        self.tickets = ticket_crud
        self.comments = comment_crud
        self.state = AgentState.IDLE
        self.current_context: Optional[AgentContext] = None
        
        # Initialize memory components
        self.embeddings = embedding_provider or EmbeddingProvider()
        self.memory_store = memory_store or ChromaMemoryStore()
        self.git_cache = git_cache or GitRepoCache()
        
        # Initialize managers
        self.config_loader = AgentConfigLoader(f"./agents/{agent_id}")
        self.context_manager = CustomerContextManager(
            agent_id=agent_id,
            memory_store=self.memory_store,
            embedding_provider=self.embeddings
        )
        self.episodic_memory = EpisodicMemory(
            memory_store=self.memory_store,
            embedding_provider=self.embeddings
        )
        
        # Load agent config
        self.agent_config = self.config_loader.load_config(agent_id)
    
    async def process_ticket(self, ticket_id: str) -> None:
        """Process a ticket with full context."""
        try:
            self.state = AgentState.OBSERVING
            context = await self._observe(ticket_id)
            self.current_context = context
            
            self.state = AgentState.REASONING
            analysis = await self._reason(context)
            
            self.state = AgentState.PLANNING
            plan = await self._plan(context, analysis)
            context.plan = plan
            
            self.state = AgentState.ACTING
            await self._act(context, analysis, plan)
            
        except Exception as e:
            await self._handle_error(ticket_id, e)
        finally:
            self.state = AgentState.IDLE
            self.current_context = None
    
    async def _observe(self, ticket_id: str) -> AgentContext:
        """OBSERVE: Gather all relevant information."""
        ticket = await self.tickets.get(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        # Set to in_progress
        await self.tickets.update(
            ticket_id,
            TicketUpdate(status="in_progress", agent=self.agent_id)
        )
        
        comments = await self.comments.get_by_ticket(ticket_id)
        
        context = AgentContext(
            customer=ticket.customer,
            repository=ticket.repository,
            ticket_id=ticket_id,
            ticket_title=ticket.title,
            ticket_description=ticket.description,
            conversation_history=[
                {"from": c.author, "text": c.content, "at": c.created_at}
                for c in comments
            ]
        )
        
        # 1. Load customer context (async, but don't wait)
        asyncio.create_task(
            self.context_manager.ensure_indexed(ticket.customer)
        )
        
        # 2. Get repository snapshot (cached)
        try:
            repo_snapshot = await self.git_cache.refresh_if_needed(
                ticket.repository,
                self.git,
                max_age_seconds=300  # Refresh if older than 5 min
            )
            context.is_empty_repo = repo_snapshot.is_empty
            context.files_read = list(repo_snapshot.files.keys())
        except Exception as e:
            print(f"Git cache error: {e}")
            context.is_empty_repo = True
        
        # 3. Record this interaction
        await self.episodic_memory.record_conversation_turn(
            customer_id=ticket.customer,
            ticket_id=ticket_id,
            author="user",
            content=f"Ticket: {ticket.title}\n{ticket.description}"
        )
        
        return context
    
    async def _reason(self, context: AgentContext) -> str:
        """REASON: Analyze with full context."""
        # Build mega system prompt with all context
        system_prompt = await self._build_full_system_prompt(context)
        
        user_prompt = f"""Analysiere dieses Ticket:

**Titel:** {context.ticket_title}
**Beschreibung:** {context.ticket_description}
**Repository:** {context.repository} ({'leer' if context.is_empty_repo else 'existiert'})

Was muss gemacht werden?"""
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt)
        ]
        
        response = await self.llm.chat(messages, temperature=0.3, max_tokens=500)
        analysis = response.content
        
        await self._add_comment(
            context.ticket_id,
            f"🧠 **Analyse**\n\n{analysis}"
        )
        
        return analysis
    
    async def _build_full_system_prompt(self, context: AgentContext) -> str:
        """Build comprehensive system prompt with all context."""
        parts = []
        
        # 1. Base personality and rules
        parts.append(self.agent_config.system_prompt)
        parts.append("")
        
        # 2. Customer context
        try:
            customer_context = await self.context_manager.get_context_summary(context.customer)
            if customer_context:
                parts.append(customer_context)
                parts.append("")
        except Exception as e:
            print(f"Customer context error: {e}")
        
        # 3. Episodic memory (past similar tickets)
        try:
            episodic_context = await self.episodic_memory.get_relevant_context(
                customer_id=context.customer,
                current_ticket_description=context.ticket_description,
                n_lessons=2,
                n_episodes=2
            )
            if episodic_context:
                parts.append(episodic_context)
                parts.append("")
        except Exception as e:
            print(f"Episodic memory error: {e}")
        
        # 4. Repository state
        parts.append("## Aktueller Repository-Status")
        if context.is_empty_repo:
            parts.append("- Repository ist LEER (Initial-Commit nötig)")
        else:
            parts.append(f"- Repository existiert mit: {', '.join(context.files_read)}")
        parts.append("")
        
        return "\n".join(parts)
    
    async def _plan(self, context: AgentContext, analysis: str) -> str:
        """PLAN: Create implementation plan."""
        system_prompt = self.agent_config.system_prompt[:500] + "\n\nErstelle einen kurzen Plan."
        
        user_prompt = f"""Analyse: {analysis}

Repository-Status: {'Leer - Initial-Commit nötig' if context.is_empty_repo else 'Existiert'}

Erstelle einen Implementierungsplan (max 3 Punkte)."""
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt)
        ]
        
        response = await self.llm.chat(messages, temperature=0.3, max_tokens=400)
        plan = response.content
        
        await self._add_comment(
            context.ticket_id,
            f"📋 **Plan**\n\n{plan}"
        )
        
        return plan
    
    async def _act(self, context: AgentContext, analysis: str, plan: str) -> None:
        """ACT: Implement or ask."""
        needs_clarification = self._check_needs_clarification(analysis, plan, context)
        
        if needs_clarification:
            question = await self._generate_question(context, analysis)
            await self._add_comment(
                context.ticket_id,
                f"❓ {question}\n\nAntworte kurz, dann mache ich weiter."
            )
            await self.tickets.update(
                context.ticket_id,
                TicketUpdate(status="clarification")
            )
        else:
            await self._implement(context, plan)
    
    def _check_needs_clarification(self, analysis: str, plan: str, context: AgentContext) -> bool:
        """Check if we need clarification."""
        desc_lower = context.ticket_description.lower()
        
        # Simple tasks don't need clarification
        if "readme" in desc_lower and ("coming soon" in desc_lower or "initial" in desc_lower):
            return False
        
        analysis_lower = analysis.lower()
        if any(word in analysis_lower for word in ["unklar", "frage", "rückfrage", "?"]):
            return True
        
        return False
    
    async def _generate_question(self, context: AgentContext, analysis: str) -> str:
        """Generate focused question."""
        system_prompt = "Stelle EINE konkrete Rückfrage. Max 2 Sätze. Deutsch."
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"Analyse: {analysis}\n\nStelle EINE kurze Frage.")
        ]
        
        response = await self.llm.chat(messages, temperature=0.3, max_tokens=200)
        return response.content.strip()
    
    async def _implement(self, context: AgentContext, plan: str) -> None:
        """Implement - make real commits."""
        ticket_id_short = context.ticket_id[:8]
        
        try:
            await self._add_comment(
                context.ticket_id,
                f"⚡ Ich implementiere das jetzt..."
            )
            
            repo_info = await self.git.get_repository_info(context.repository)
            default_branch = repo_info.default_branch
            
            # Check if empty
            is_empty = context.is_empty_repo
            
            # Generate files
            files_to_commit = await self._generate_files(context)
            
            if not files_to_commit:
                await self._add_comment(
                    context.ticket_id,
                    "⚠️ Konnte keine Dateien generieren."
                )
                await self.tickets.update(
                    context.ticket_id,
                    TicketUpdate(status="clarification")
                )
                return
            
            commit_message = f"[{context.ticket_id[:8]}] {context.ticket_title}"
            
            if is_empty:
                # Empty repo - direct commit
                await self._add_comment(
                    context.ticket_id,
                    f"⚡ Repository ist leer. Erstelle Initial-Commit..."
                )
                
                for file_path, content in files_to_commit.items():
                    await self._create_file_in_empty_repo(
                        context.repository, file_path, content, commit_message
                    )
                
                await self._add_comment(
                    context.ticket_id,
                    f"✅ **Fertig!** Initial-Commit auf `{default_branch}` erstellt."
                )
                
                # Record as lesson
                await self.episodic_memory.record_ticket_resolution(
                    customer_id=context.customer,
                    ticket_id=context.ticket_id,
                    problem=context.ticket_description,
                    solution=f"Initial-Commit mit {list(files_to_commit.keys())}",
                    success=True
                )
                
                await self.tickets.update(
                    context.ticket_id,
                    TicketUpdate(status="done")
                )
            else:
                # Branch + PR
                branch_name = f"feature/{ticket_id_short}-{self._slugify(context.ticket_title)}"
                
                await self.git.create_branch(context.repository, branch_name, default_branch)
                await self.git.create_commit(
                    context.repository, branch_name, commit_message, files_to_commit,
                    author_name=self.agent_config.personality.name,
                    author_email=f"{self.agent_id}@ki-agent.dev"
                )
                
                pr = await self.git.create_pr(
                    context.repository,
                    f"[{context.ticket_id[:8]}] {context.ticket_title}",
                    f"Ticket: {context.ticket_id}",
                    branch_name, default_branch
                )
                
                await self._add_comment(
                    context.ticket_id,
                    f"✅ **Fertig!** PR erstellt: [{pr.title}]({pr.url})"
                )
                
                await self.tickets.update(
                    context.ticket_id,
                    TicketUpdate(status="testing")
                )
            
        except Exception as e:
            await self._add_comment(
                context.ticket_id, f"❌ Fehler: {str(e)[:200]}"
            )
            await self.tickets.update(
                context.ticket_id,
                TicketUpdate(status="clarification")
            )
    
    async def _generate_files(self, context: AgentContext) -> Dict[str, str]:
        """Generate file contents."""
        files = {}
        desc_lower = context.ticket_description.lower()
        
        if "readme" in desc_lower:
            content = "COMING SOON"
            import re
            quotes = re.findall(r'["\']([^"\']+)["\']', context.ticket_description)
            if quotes:
                content = quotes[0]
            files["README.md"] = content
        
        if not context.files_read:
            files[".gitignore"] = "__pycache__/\n*.pyc\n.env\n"
        
        return files
    
    async def _create_file_in_empty_repo(self, repo: str, path: str, content: str, message: str):
        """Create file in empty repo."""
        import base64
        import httpx
        
        parts = repo.split('/')
        owner, repo_name = parts[0], parts[1]
        
        content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        async with httpx.AsyncClient() as client:
            await client.put(
                f"https://api.github.com/repos/{owner}/{repo_name}/contents/{path}",
                headers={
                    "Authorization": f"Bearer {self.git.token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                json={"message": message, "content": content_b64}
            )
    
    def _slugify(self, text: str) -> str:
        """Convert to branch-safe slug."""
        import re
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug[:30]
    
    async def _add_comment(self, ticket_id: str, content: str) -> None:
        """Add comment and record in episodic memory."""
        comment = CommentCreate(author=self.agent_id, content=content)
        await self.comments.create(ticket_id, comment)
        
        # Record in episodic memory
        if self.current_context:
            await self.episodic_memory.record_conversation_turn(
                customer_id=self.current_context.customer,
                ticket_id=ticket_id,
                author=self.agent_id,
                content=content
            )
    
    async def _handle_error(self, ticket_id: str, error: Exception) -> None:
        """Handle errors."""
        await self._add_comment(ticket_id, f"❌ Fehler: {str(error)[:200]}")
    
    async def run_auto_mode(self, poll_interval: int = 30) -> None:
        """Auto-mode with full memory."""
        print(f"🤖 {self.agent_id} (Enhanced) gestartet")
        while True:
            try:
                from ..kanban.models import TicketStatus
                
                # New tickets
                open_tickets = await self.tickets.list(
                    status=TicketStatus.BACKLOG, agent=None
                )
                for ticket in open_tickets:
                    print(f"📨 Neues Ticket: {ticket.id}")
                    await self.process_ticket(ticket.id)
                
                # Clarification tickets
                clarification = await self.tickets.list(status=TicketStatus.CLARIFICATION)
                for ticket in clarification:
                    if ticket.agent == self.agent_id:
                        comments = await self.comments.get_by_ticket(ticket.id)
                        if comments and comments[0].author != self.agent_id:
                            print(f"💬 Rückfrage beantwortet: {ticket.id}")
                            await self.process_ticket(ticket.id)
                
            except Exception as e:
                print(f"Error: {e}")
            
            await asyncio.sleep(poll_interval)
