"""IntelligentAgent - Main agent with Tool-Use, Memory, and ORPA workflow.

This agent integrates:
- Tool-Use Pattern (AI decides which tools to use)
- 4-Layer Memory System (Short-term, Session, Long-term, Episodic)
- Workspace/Repository Management
- ORPA Workflow (Observe, Reason, Plan, Act)

Example:
    config = AgentConfig(customer_id="acme-corp")
    agent = IntelligentAgent("dev-agent-1", config)
    
    result = await agent.process_ticket(ticket_id="ABC-123")
"""

import os
import asyncio
import json
import logging
import hashlib
import re
import threading
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime
from pathlib import Path

# Import types
from .agent_types import (
    AgentConfig,
    AgentContext,
    AgentResult,
    TicketInfo,
    ORPAState,
    ReasoningResult,
    ToolExecutionPlan,
    ToolExecutionStep,
    ToolExecutionResult,
)
from .orpa_states import ORPAStateMachine, ORPAWorkflow

# Import existing components
try:
    from ..tools.registry import ToolRegistry
    from ..tools.executor import ToolExecutor
    from ..tools.base import ToolResult
    from ..tools.file_tools import FileReadTool, FileWriteTool, FileListTool, FileSearchTool
    from ..tools.code_tools import CodeAnalyzeTool, CodeRefactorTool, CodeGenerateTool
    from ..tools.git_tools import (
        GitStatusTool, GitCommitTool,
        GitHubReadFileTool, GitHubWriteFileTool, GitHubListFilesTool,
        GitHubCreateBranchTool, GitHubGetRepoInfoTool, GitHubCreatePRTool,
    )
    from ..tools.ddev_tools import (
        DDEVExecuteTool,
        WorkspaceSetupTool,
        WorkspaceStatusTool,
        DDEVStartTool,
        DDEVStopTool,
        TestRunnerTool,
        GitSyncTool,
        GitPullTool,
        ListWorkspacesTool,
    )
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False

try:
    from ..memory.unified_manager import UnifiedMemoryManager, LearningEpisode
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False

try:
    from ..infrastructure.workspace_manager import WorkspaceManager, get_workspace_manager
    from ..infrastructure.repository_manager import RepositoryManager, get_repository_manager
    WORKSPACE_AVAILABLE = True
except ImportError:
    WORKSPACE_AVAILABLE = False

try:
    from ..agent_config import AgentConfigLoader
    IDENTITY_AVAILABLE = True
except ImportError:
    IDENTITY_AVAILABLE = False

try:
    from ..llm.kimi_client import KimiClient, Message, LLMResponse
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

logger = logging.getLogger(__name__)


class IntelligentAgent:
    """Intelligent agent with Tool-Use, Memory, and ORPA workflow.
    
    This is the main agent class that integrates all components:
    - Tool Registry & Executor for tool-use
    - Unified Memory Manager for 4-layer memory
    - Workspace/Repository Manager for code operations
    - ORPA State Machine for workflow management
    - Kimi LLM Client for reasoning
    
    Attributes:
        agent_id: Unique identifier for this agent instance
        config: Agent configuration
        tools: Tool registry with all available tools
        executor: Tool executor with logging
        memory: Unified memory manager (4 layers)
        workspace: Workspace manager for customer repos
        repo_manager: Repository manager for git operations
        llm: LLM client for reasoning
        state_machine: ORPA state machine
    """
    
    def __init__(self, agent_id: str, config: AgentConfig, ticket_crud=None, comment_crud=None, git_provider=None):
        """Initialize the IntelligentAgent.
        
        Args:
            agent_id: Unique identifier for this agent
            config: Agent configuration
            ticket_crud: Optional TicketCRUD for status updates
            comment_crud: Optional CommentCRUD for posting comments
            git_provider: Optional GitProvider for GitHub API operations
            
        Raises:
            RuntimeError: If required dependencies are not available
        """
        self.agent_id = agent_id
        self.config = config
        self.ticket_crud = ticket_crud
        self.comment_crud = comment_crud
        self.git_provider = git_provider
        self._agent_runtime: Dict[str, Any] = {}
        self.llm_timeout_seconds = int(os.getenv("AGENT_LLM_TIMEOUT_SECONDS", "90"))
        self.memory_sync_background = os.getenv("AGENT_MEMORY_SYNC_BACKGROUND", "true").lower() == "true"
        self.semantic_identity_limit = int(os.getenv("AGENT_SEMANTIC_IDENTITY_LIMIT", "2"))
        self.semantic_memory_limit = int(os.getenv("AGENT_SEMANTIC_MEMORY_LIMIT", "3"))
        self.semantic_customer_limit = int(os.getenv("AGENT_SEMANTIC_CUSTOMER_LIMIT", "2"))
        self.semantic_hit_chars = int(os.getenv("AGENT_SEMANTIC_HIT_CHARS", "350"))
        self.memories_fallback_chars = int(os.getenv("AGENT_MEMORIES_FALLBACK_CHARS", "6000"))
        self.compact_tools_prompt = os.getenv("AGENT_COMPACT_TOOLS_PROMPT", "true").lower() == "true"
        self.retrieval_min_score = int(os.getenv("AGENT_RETRIEVAL_MIN_SCORE", "55"))
        self.retrieval_rewrite_loops = int(os.getenv("AGENT_RETRIEVAL_REWRITE_LOOPS", "2"))
        self.max_evidence_gate_failures = int(os.getenv("AGENT_MAX_EVIDENCE_GATE_FAILURES", "2"))
        self.max_consecutive_llm_timeouts = int(os.getenv("AGENT_MAX_CONSECUTIVE_LLM_TIMEOUTS", "3"))
        self.require_pr_for_success = os.getenv("AGENT_REQUIRE_PR_FOR_SUCCESS", "true").lower() == "true"
        self.kimi_max_retries = self._parse_optional_int(os.getenv("KIMI_MAX_RETRIES"))
        self.kimi_timeout_connect = self._parse_optional_float(os.getenv("KIMI_TIMEOUT_CONNECT"))
        self.kimi_timeout_read = self._parse_optional_float(os.getenv("KIMI_TIMEOUT_READ"))
        self.kimi_timeout_write = self._parse_optional_float(os.getenv("KIMI_TIMEOUT_WRITE"))
        self.kimi_timeout_pool = self._parse_optional_float(os.getenv("KIMI_TIMEOUT_POOL"))
        self._consecutive_llm_timeouts = 0
        
        # === 0. IDENTITY laden (aus agents/{agent_id}/) ===
        self.identity_prompt = None
        self.knowledge = ""
        self.memories = ""
        self._config_loader = None
        
        if IDENTITY_AVAILABLE:
            try:
                loader = AgentConfigLoader("./agents")
                identity = loader.load_config(agent_id)
                self.identity_prompt = identity.system_prompt
                self.knowledge = identity.knowledge
                self.memories = identity.memories
                self._config_loader = loader
                raw_runtime = loader.load_agent_runtime_config(agent_id)
                if isinstance(raw_runtime, dict):
                    runtime = raw_runtime.get("runtime", {})
                    if isinstance(runtime, dict):
                        self._agent_runtime = runtime
                    else:
                        self._agent_runtime = {}
                self._apply_agent_runtime_overrides()
                print(f"   🧬 Identity loaded: soul + rules + knowledge ({len(self.knowledge)} chars) + memories ({len(self.memories)} chars)")
            except Exception as e:
                logger.warning(f"Could not load agent identity from agents/{agent_id}/: {e}")
        else:
            logger.warning("agent_config module not available, using default identity")
        
        # Check dependencies
        if not TOOLS_AVAILABLE:
            raise RuntimeError("Tools module not available")
        if not LLM_AVAILABLE:
            raise RuntimeError("LLM module not available")
        
        # === 1. LLM Client (before tools, since CodeGenerateTool needs it) ===
        self.llm = KimiClient(
            max_retries=self.kimi_max_retries,
            timeout_connect=self.kimi_timeout_connect,
            timeout_read=self.kimi_timeout_read,
            timeout_write=self.kimi_timeout_write,
            timeout_pool=self.kimi_timeout_pool,
        )
        
        # === 2. MEMORY initialisieren ===
        if config.enable_memory and MEMORY_AVAILABLE:
            self.memory = UnifiedMemoryManager(
                customer_id=config.customer_id,
                config=None  # Use defaults
            )
            if self.memory_sync_background:
                threading.Thread(
                    target=self._sync_assigned_customers_to_memory_on_startup,
                    daemon=True,
                ).start()
            else:
                self._sync_assigned_customers_to_memory_on_startup()
        else:
            self.memory = None
            if config.enable_memory:
                logger.warning("Memory enabled but module not available")
        
        # === 3. WORKSPACE initialisieren ===
        if config.enable_workspace and WORKSPACE_AVAILABLE:
            self.workspace = get_workspace_manager()
            self.repo_manager = get_repository_manager()
        else:
            self.workspace = None
            self.repo_manager = None
            if config.enable_workspace:
                logger.warning("Workspace enabled but module not available")

        # === 4. TOOLS initialisieren ===
        # Must happen after workspace init because workspace tools depend on self.workspace.
        self.tools = ToolRegistry()
        self._register_all_tools()
        self.executor = ToolExecutor(self.tools, log_executions=True)
        
        # === 5. ORPA State Machine ===
        self.state_machine = ORPAStateMachine(
            max_iterations=config.max_iterations,
            on_transition=self._on_state_transition
        )
        
        # === Callbacks ===
        self._progress_callbacks: List[Callable[[ORPAState, AgentContext], None]] = []
        
        logger.info(f"IntelligentAgent '{agent_id}' initialized for customer '{config.customer_id}'")

    @staticmethod
    def _parse_optional_int(value: Any) -> Optional[int]:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        try:
            return int(text)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_optional_float(value: Any) -> Optional[float]:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        try:
            return float(text)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_bool(value: Any, default: bool) -> bool:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "on"}:
            return True
        if text in {"0", "false", "no", "off"}:
            return False
        return default

    def _apply_agent_runtime_overrides(self):
        """Apply optional per-agent runtime tuning from config.yaml runtime: {...}."""
        runtime = self._agent_runtime or {}
        if not isinstance(runtime, dict):
            return

        # Core ORPA / retrieval controls
        self.llm_timeout_seconds = int(runtime.get("llm_timeout_seconds", self.llm_timeout_seconds))
        self.memory_sync_background = self._parse_bool(
            runtime.get("memory_sync_background"), self.memory_sync_background
        )
        self.semantic_identity_limit = int(runtime.get("semantic_identity_limit", self.semantic_identity_limit))
        self.semantic_memory_limit = int(runtime.get("semantic_memory_limit", self.semantic_memory_limit))
        self.semantic_customer_limit = int(runtime.get("semantic_customer_limit", self.semantic_customer_limit))
        self.semantic_hit_chars = int(runtime.get("semantic_hit_chars", self.semantic_hit_chars))
        self.memories_fallback_chars = int(runtime.get("memories_fallback_chars", self.memories_fallback_chars))
        self.compact_tools_prompt = self._parse_bool(
            runtime.get("compact_tools_prompt"), self.compact_tools_prompt
        )
        self.retrieval_min_score = int(runtime.get("retrieval_min_score", self.retrieval_min_score))
        self.retrieval_rewrite_loops = int(runtime.get("retrieval_rewrite_loops", self.retrieval_rewrite_loops))
        self.max_evidence_gate_failures = int(
            runtime.get("max_evidence_gate_failures", self.max_evidence_gate_failures)
        )
        self.max_consecutive_llm_timeouts = int(
            runtime.get("max_consecutive_llm_timeouts", self.max_consecutive_llm_timeouts)
        )
        self.require_pr_for_success = self._parse_bool(
            runtime.get("require_pr_for_success"), self.require_pr_for_success
        )

        # Optional per-agent Kimi transport overrides
        self.kimi_max_retries = self._parse_optional_int(
            runtime.get("kimi_max_retries", self.kimi_max_retries)
        )
        self.kimi_timeout_connect = self._parse_optional_float(
            runtime.get("kimi_timeout_connect", self.kimi_timeout_connect)
        )
        self.kimi_timeout_read = self._parse_optional_float(
            runtime.get("kimi_timeout_read", self.kimi_timeout_read)
        )
        self.kimi_timeout_write = self._parse_optional_float(
            runtime.get("kimi_timeout_write", self.kimi_timeout_write)
        )
        self.kimi_timeout_pool = self._parse_optional_float(
            runtime.get("kimi_timeout_pool", self.kimi_timeout_pool)
        )

    def _sync_assigned_customers_to_memory_on_startup(self):
        """Sync agent/customer markdown sources into long-term memory (hash-based upsert)."""
        if not self._config_loader or not self.memory or not self.memory.long_term:
            return
        if not self._config_loader.should_auto_sync_customers_on_start(self.agent_id):
            return

        try:
            total_added = 0
            total_updated = 0
            total_deleted = 0
            total_skipped = 0

            # 1) Agent identity files: soul/rules/knowledge
            identity_files = self._collect_agent_identity_files()
            added, updated, deleted, skipped = self._sync_markdown_files_to_memory(
                files=identity_files,
                memory_type="agent_identity",
                source_group="agent_identity",
                customer_id=None,
            )
            total_added += added
            total_updated += updated
            total_deleted += deleted
            total_skipped += skipped

            # 2) Agent memories directory (recursive)
            memory_files = self._collect_agent_memory_files()
            added, updated, deleted, skipped = self._sync_markdown_files_to_memory(
                files=memory_files,
                memory_type="agent_memories",
                source_group="agent_memories",
                customer_id=None,
            )
            total_added += added
            total_updated += updated
            total_deleted += deleted
            total_skipped += skipped

            # 3) Assigned customer markdown files (shared + legacy path)
            assigned_customers = self._config_loader.get_assigned_customers(self.agent_id)
            customers_root = Path("./customers")
            legacy_root = Path("./agents") / self.agent_id / "customers"
            for customer_id in assigned_customers:
                files = self._collect_customer_files(customer_id, customers_root, legacy_root)
                added, updated, deleted, skipped = self._sync_markdown_files_to_memory(
                    files=files,
                    memory_type="customer_context",
                    source_group="customer_context",
                    customer_id=customer_id,
                )
                total_added += added
                total_updated += updated
                total_deleted += deleted
                total_skipped += skipped

            logger.info(
                f"Startup markdown sync for '{self.agent_id}': "
                f"added={total_added}, updated={total_updated}, deleted={total_deleted}, "
                f"skipped={total_skipped}, assigned_customers={len(assigned_customers)}"
            )
        except Exception as e:
            logger.warning(f"Startup markdown sync failed: {e}")

    async def _call_llm(
        self,
        messages: List[Message],
        temperature: float,
        max_tokens: int,
        phase: str,
    ) -> LLMResponse:
        """Wrap LLM calls with a hard timeout for robust worker behavior."""
        try:
            response = await asyncio.wait_for(
                self.llm.chat(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ),
                timeout=self.llm_timeout_seconds,
            )
            self._consecutive_llm_timeouts = 0
            return response
        except asyncio.TimeoutError as e:
            self._consecutive_llm_timeouts += 1
            raise TimeoutError(
                f"LLM timeout in phase '{phase}' after {self.llm_timeout_seconds}s "
                f"(consecutive={self._consecutive_llm_timeouts})"
            ) from e

    def _collect_agent_identity_files(self) -> List[Path]:
        """Collect canonical agent identity markdown files."""
        agent_root = Path("./agents") / self.agent_id
        candidates = [
            agent_root / "soul.md",
            agent_root / "rules.md",
            agent_root / "knowledge.md",
        ]
        return [p for p in candidates if p.exists() and p.is_file()]

    def _collect_agent_memory_files(self) -> List[Path]:
        """Collect all supported text memory files under agents/{agent_id}/memories recursively."""
        memories_root = Path("./agents") / self.agent_id / "memories"
        if not memories_root.exists():
            return []
        files: List[Path] = []
        for pattern in ("*.md", "*.txt"):
            files.extend([p for p in memories_root.rglob(pattern) if p.is_file()])
        return sorted(set(files))

    def _collect_customer_files(
        self,
        customer_id: str,
        customers_root: Path,
        legacy_root: Path,
    ) -> List[Path]:
        """Collect shared + legacy customer markdown files recursively."""
        files: List[Path] = []
        shared_dir = customers_root / customer_id
        legacy_dir = legacy_root / customer_id
        if shared_dir.exists():
            files.extend([p for p in shared_dir.rglob("*.md") if p.is_file()])
        if legacy_dir.exists():
            files.extend([p for p in legacy_dir.rglob("*.md") if p.is_file()])
        return sorted(files)

    def _chunk_markdown(self, content: str, max_chars: int = 1400, overlap: int = 200) -> List[str]:
        """Chunk markdown into retrieval-friendly pieces without dropping content."""
        if not content:
            return []
        if len(content) <= max_chars:
            return [content]

        chunks: List[str] = []
        start = 0
        length = len(content)
        while start < length:
            end = min(start + max_chars, length)
            if end < length:
                split_nl = content.rfind("\n", start, end)
                if split_nl > start + 300:
                    end = split_nl
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= length:
                break
            start = max(end - overlap, start + 1)
        return chunks

    def _sync_markdown_files_to_memory(
        self,
        files: List[Path],
        memory_type: str,
        source_group: str,
        customer_id: Optional[str],
    ) -> Tuple[int, int, int, int]:
        """Hash-based upsert + stale deletion for markdown sources."""
        collection_name = f"{self.memory.long_term.customer_id}_{memory_type}"
        collection = self.memory.long_term.chroma._get_collection(collection_name)

        existing_by_source: Dict[str, Dict[str, Any]] = {}
        results = collection.get(include=["metadatas"]) or {}
        ids = results.get("ids") or []
        metas = results.get("metadatas") or []
        for i, memory_id in enumerate(ids):
            meta = metas[i] if i < len(metas) and metas[i] else {}
            if meta.get("agent_id") != self.agent_id:
                continue
            if meta.get("source_group") != source_group:
                continue
            if (customer_id or "") != (meta.get("customer_id") or ""):
                continue
            source = meta.get("source", "")
            if not source:
                continue
            entry = existing_by_source.setdefault(source, {"ids": [], "hash": meta.get("content_hash", "")})
            entry["ids"].append(memory_id)

        added = 0
        updated = 0
        deleted = 0
        skipped = 0
        seen_sources = set()

        for md_file in files:
            try:
                content = md_file.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning(f"Could not read markdown file {md_file}: {e}")
                continue

            source = str(md_file.resolve())
            seen_sources.add(source)
            content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
            existing = existing_by_source.get(source)
            if existing and existing.get("hash") == content_hash:
                skipped += 1
                continue

            if existing and existing.get("ids"):
                try:
                    collection.delete(ids=existing["ids"])
                    deleted += len(existing["ids"])
                    updated += 1
                except Exception as e:
                    logger.warning(f"Could not delete stale chunks for {source}: {e}")
            else:
                added += 1

            chunks = self._chunk_markdown(content)
            total_chunks = len(chunks)
            for idx, chunk in enumerate(chunks):
                chunk_id = hashlib.md5(
                    f"{self.agent_id}|{memory_type}|{source}|{content_hash}|{idx}".encode("utf-8")
                ).hexdigest()
                metadata = {
                    "agent_id": self.agent_id,
                    "customer_id": customer_id or "",
                    "source_group": source_group,
                    "source": source,
                    "relative_path": str(md_file),
                    "content_hash": content_hash,
                    "chunk_index": idx,
                    "chunk_total": total_chunks,
                    "loaded_at": datetime.utcnow().isoformat(),
                }
                collection.add(ids=[chunk_id], documents=[chunk], metadatas=[metadata])

        # Delete sources that no longer exist on disk
        stale_sources = set(existing_by_source.keys()) - seen_sources
        for source in stale_sources:
            stale_ids = existing_by_source[source].get("ids", [])
            if not stale_ids:
                continue
            try:
                collection.delete(ids=stale_ids)
                deleted += len(stale_ids)
            except Exception as e:
                logger.warning(f"Could not delete removed source '{source}' chunks: {e}")

        return added, updated, deleted, skipped
    
    def _register_all_tools(self):
        """Register all available tools with the registry."""
        # File tools (core -- must succeed)
        self.tools.register(FileReadTool(), category="file")
        self.tools.register(FileWriteTool(), category="file")
        self.tools.register(FileListTool(), category="file")
        self.tools.register(FileSearchTool(), category="file")
        
        # Code tools (each registered individually so one failure doesn't block others)
        for tool_factory, name in [
            (lambda: CodeAnalyzeTool(), "CodeAnalyzeTool"),
            (lambda: CodeRefactorTool(), "CodeRefactorTool"),
            (lambda: CodeGenerateTool(llm_client=self.llm), "CodeGenerateTool"),
        ]:
            try:
                self.tools.register(tool_factory(), category="code")
            except Exception as e:
                logger.warning(f"Failed to register {name}: {e}")
        
        # Local git tools
        for tool_factory, name in [
            (lambda: GitStatusTool(), "GitStatusTool"),
            (lambda: GitCommitTool(), "GitCommitTool"),
        ]:
            try:
                self.tools.register(tool_factory(), category="git")
            except Exception as e:
                logger.warning(f"Failed to register {name}: {e}")
        
        # GitHub API tools (remote operations via git_provider)
        if not self.git_provider:
            raise RuntimeError(
                "git_provider is required for IntelligentAgent. "
                "Pass a GitProvider instance (e.g. GitHubProvider) when creating the agent."
            )
        gp = self.git_provider
        for tool_factory, name in [
                (lambda: GitHubReadFileTool(git_provider=gp), "GitHubReadFileTool"),
                (lambda: GitHubWriteFileTool(git_provider=gp), "GitHubWriteFileTool"),
                (lambda: GitHubListFilesTool(git_provider=gp), "GitHubListFilesTool"),
                (lambda: GitHubCreateBranchTool(git_provider=gp), "GitHubCreateBranchTool"),
                (lambda: GitHubGetRepoInfoTool(git_provider=gp), "GitHubGetRepoInfoTool"),
                (lambda: GitHubCreatePRTool(git_provider=gp), "GitHubCreatePRTool"),
            ]:
                try:
                    self.tools.register(tool_factory(), category="github")
                except Exception as e:
                    logger.warning(f"Failed to register {name}: {e}")
        
        # Workspace/DDEV tools (for local development environments)
        # Tools use get_workspace_manager() internally; only register when workspace enabled
        if self.workspace:
            for tool_factory, name in [
                (lambda: WorkspaceSetupTool(), "WorkspaceSetupTool"),
                (lambda: WorkspaceStatusTool(), "WorkspaceStatusTool"),
                (lambda: DDEVExecuteTool(), "DDEVExecuteTool"),
                (lambda: DDEVStartTool(), "DDEVStartTool"),
                (lambda: DDEVStopTool(), "DDEVStopTool"),
                (lambda: TestRunnerTool(), "TestRunnerTool"),
                (lambda: GitSyncTool(), "GitSyncTool"),
                (lambda: GitPullTool(), "GitPullTool"),
                (lambda: ListWorkspacesTool(), "ListWorkspacesTool"),
            ]:
                try:
                    self.tools.register(tool_factory(), category="workspace")
                except Exception as e:
                    logger.warning(f"Failed to register {name}: {e}")
        else:
            logger.warning("No workspace - Workspace/DDEV tools not available")
        
        logger.info(f"Registered {len(self.tools)} tools")
    
    def _on_state_transition(
        self, 
        old_state: ORPAState, 
        new_state: ORPAState, 
        context: Optional[AgentContext]
    ):
        """Callback for state transitions."""
        logger.info(f"ORPA: {old_state.value} → {new_state.value}")
        
        # Notify progress callbacks
        for callback in self._progress_callbacks:
            try:
                callback(new_state, context)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
    
    def on_progress(self, callback: Callable[[ORPAState, AgentContext], None]):
        """Register a progress callback.
        
        Args:
            callback: Function(state, context) called on state changes
        """
        self._progress_callbacks.append(callback)
    
    # ==================================================================
    # MAIN WORKFLOW
    # ==================================================================
    
    async def process_ticket(self, ticket_id: str, ticket_data: Optional[Dict] = None) -> AgentResult:
        """Process a ticket through the complete ORPA workflow.
        
        This is the main entry point for ticket processing.
        
        Args:
            ticket_id: The ticket identifier
            ticket_data: Optional ticket data (fetched if not provided)
            
        Returns:
            AgentResult with the processing outcome
        """
        logger.info(f"Processing ticket {ticket_id}")
        self._consecutive_llm_timeouts = 0
        context: Optional[AgentContext] = None

        try:
            # Create ticket info
            if ticket_data:
                ticket = TicketInfo(
                    ticket_id=ticket_id,
                    title=ticket_data.get("title", ""),
                    description=ticket_data.get("description", ""),
                    customer_id=ticket_data.get("customer_id", self.config.customer_id),
                    repository=ticket_data.get("repository"),
                    branch=ticket_data.get("branch"),
                    labels=ticket_data.get("labels", []),
                    metadata=ticket_data.get("metadata", {}),
                )
            else:
                # Create minimal ticket info
                ticket = TicketInfo(
                    ticket_id=ticket_id,
                    title=f"Ticket {ticket_id}",
                    description="",
                    customer_id=self.config.customer_id,
                )
            
            # Create context
            context = AgentContext(ticket=ticket)
            context.workspace_path = self.config.workspace_path
            
            # Load memory context if available
            if self.memory:
                print("   📝 Loading memory context...")
                try:
                    memory_context = self.memory.build_agent_context(
                        ticket_id=ticket_id,
                        ticket_description=ticket.description,
                        customer_id=ticket.customer_id
                    )
                    context.relevant_learnings = memory_context.get("relevant_learnings", [])
                    context.similar_tickets = memory_context.get("recent_learnings", [])
                    context.chat_history = memory_context.get("chat_history", [])
                    print(f"   📝 Memory loaded: {len(context.relevant_learnings)} learnings, {len(context.similar_tickets)} similar")
                except Exception as e:
                    print(f"   ⚠️  Memory load failed (continuing): {e}")
            
            # Start ORPA workflow
            print("   🔄 Starting ORPA state machine...")
            self.state_machine.reset()
            self.state_machine.start(context)
            
            # Run workflow loop
            while not self.state_machine.is_terminal:
                state = self.state_machine.current_state
                
                if state == ORPAState.OBSERVING:
                    await self._observe(context)
                    
                elif state == ORPAState.REASONING:
                    await self._reason(context)
                    
                elif state == ORPAState.PLANNING:
                    await self._plan(context)
                    
                elif state == ORPAState.ACTING:
                    await self._act(context)
                    
                elif state == ORPAState.NEEDS_CLARIFICATION:
                    return self._create_result(context, success=False)
                    
                elif state == ORPAState.ERROR:
                    await self._post_comment(
                        context.ticket.ticket_id,
                        f"❌ Fehler bei der Verarbeitung. Ich schaue mir das nochmal an."
                    )
                    return self._create_result(context, success=False)

            # Terminal state reached. Only run quality gates on successful completion.
            if self.state_machine.current_state != ORPAState.COMPLETED:
                return self._create_result(context, success=False)

            # Workflow completed successfully (validate minimal workflow gates first)
            gate_result = await self._validate_minimal_quality_gates(context)
            if not gate_result.get("passed", True):
                context.needs_clarification = True
                context.clarification_question = (
                    "Die Mindest-Qualitätsgates sind noch nicht erfüllt. "
                    "Bitte Ticket prüfen und ggf. Anforderungen präzisieren."
                )
                details = gate_result.get("details", [])
                details_text = "\n".join(f"- {d}" for d in details) if details else "- Unbekannt"
                await self._post_comment(
                    context.ticket.ticket_id,
                    "⚠️ **Workflow nicht abgeschlossen (Quality-Gate)**\n\n"
                    "Die Umsetzung wurde ausgeführt, aber vor `testing` fehlen Pflichtpunkte:\n"
                    f"{details_text}\n\n"
                    "Ich habe deshalb nicht als final abgeschlossen markiert."
                )
                return self._create_result(context, success=False)

            # Workflow completed successfully
            files = [
                r.data.get("path", "")
                for r in context.execution_results
                if r.success and r.data and isinstance(r.data, dict)
            ]
            completion_comment = await self._build_customer_completion_comment(context, files)
            await self._post_comment(context.ticket.ticket_id, completion_comment)
            return self._create_result(context, success=True)
            
        except Exception as e:
            logger.exception(f"Error processing ticket {ticket_id}")
            return AgentResult(
                ticket_id=ticket_id,
                success=False,
                message=f"Processing failed: {str(e)}",
                error=str(e),
                final_state=ORPAState.ERROR,
            )
        finally:
            if context is not None:
                try:
                    await self._persist_ticket_git_context(context)
                except Exception as persist_error:
                    logger.debug(f"Could not persist ticket git context: {persist_error}")
    
    # ==================================================================
    # ORPA PHASES
    # ==================================================================
    
    async def _observe(self, context: AgentContext):
        """ORPA: OBSERVE Phase - Gather information.
        
        Collects:
        - Repository structure
        - Relevant files based on ticket
        - Git status
        - Similar past solutions from memory
        """
        print("   👁️  ORPA Phase: OBSERVING")
        logger.debug("ORPA Phase: OBSERVING")
        context.iteration += 1
        
        try:
            # 1. Get repository info if workspace available
            if self.workspace and context.ticket.customer_id:
                repo_info = self.workspace.get_repo_info(
                    context.ticket.customer_id, context.ticket.repository
                )
                if repo_info:
                    context.repo_info = repo_info
                    context.add_observation("repo_info", repo_info)
            
            # 2. Get repository structure
            if self.workspace and context.ticket.customer_id:
                ws = self.workspace.get_workspace(
                    context.ticket.customer_id, context.ticket.repository
                )
                workspace_path = ws.workspace_path if ws else None
                if workspace_path and Path(workspace_path).exists():
                    # List top-level structure
                    result = await self.executor.execute(
                        "file_list",
                        {"path": str(workspace_path), "recursive": False},
                        agent_id=self.agent_id,
                        ticket_id=context.ticket.ticket_id
                    )
                    if result.success:
                        context.repository_structure = result.data
                        context.add_observation("repository_structure", result.data)
            
            # 3. Search for relevant files based on ticket
            if context.ticket.description:
                keywords = self._extract_keywords(context.ticket.description)
                for keyword in keywords[:3]:  # Limit to top 3 keywords
                    if self.workspace and context.ticket.customer_id:
                        ws = self.workspace.get_workspace(
                            context.ticket.customer_id, context.ticket.repository
                        )
                        workspace_path = ws.workspace_path if ws else None
                        if workspace_path:
                            result = await self.executor.execute(
                                "file_search",
                                {
                                    "pattern": keyword,
                                    "path": str(workspace_path),
                                    "max_results": 5
                                },
                                agent_id=self.agent_id,
                                ticket_id=context.ticket.ticket_id
                            )
                            if result.success and result.data.get("matches"):
                                context.relevant_files.extend([
                                    m["file"] for m in result.data["matches"]
                                ])
            
            # 3.5 Infer lightweight repo profile from repo-owned files/scripts/CI.
            if context.ticket.repository:
                repo_profile = await self._infer_repo_profile(context)
                if repo_profile:
                    context.add_observation("repo_profile", repo_profile)
            
            # 4. Get similar solutions from memory
            if self.memory and context.ticket.description:
                print("      Memory: searching similar solutions...")
                similar = self.memory.find_solutions(context.ticket.description, limit=3)
                if similar:
                    context.relevant_learnings = similar
                    context.add_observation("similar_solutions", similar)
                    print(f"      Memory: found {len(similar)} similar solutions")
                else:
                    print("      Memory: no similar solutions found")
            
            # Transition to REASONING
            print("   👁️  OBSERVE complete")
            self.state_machine.transition_to(ORPAState.REASONING, "Observation complete")
            
        except Exception as e:
            print(f"   ❌ Observation failed: {e}")
            logger.exception("Observation failed")
            self.state_machine.complete(success=False, reason=f"Observation error: {e}")
    
    async def _reason(self, context: AgentContext):
        """ORPA: REASON Phase - Analyze and decide.
        
        The LLM analyzes:
        - What the user wants
        - Which tools are needed
        - The approach to take
        """
        print("   🧠 ORPA Phase: REASONING")
        logger.debug("ORPA Phase: REASONING")
        
        try:
            # Get tool schemas for LLM
            tools_schemas = self.tools.get_schemas_for_llm(format="openai")
            
            # Build reasoning prompt
            prompt = self._build_reasoning_prompt(context, tools_schemas)
            
            # Call LLM
            system_prompt = self._get_system_prompt(context, phase="reasoning")
            print(f"      System prompt: {len(system_prompt)} chars")
            print(f"      User prompt: {len(prompt)} chars")
            print(f"      Prompt total: {len(system_prompt) + len(prompt)} chars")
            messages = [
                Message(role="system", content=system_prompt),
                Message(role="user", content=prompt)
            ]
            
            print(f"      Calling LLM (Kimi 2.5, timeout={self.llm_timeout_seconds}s)...")
            response = await self._call_llm(
                messages=messages,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens,
                phase="reasoning",
            )
            print(f"      LLM response: {len(response.content)} chars, tokens: {response.usage}")
            
            # Parse reasoning result
            try:
                content = response.content
                # Extract JSON from response (handle markdown code blocks)
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                
                reasoning_data = json.loads(content.strip())
                reasoning = ReasoningResult.parse(reasoning_data)
                
            except json.JSONDecodeError:
                # Fallback: treat entire response as understanding
                reasoning = ReasoningResult(
                    understanding=response.content,
                    needed_tools=[],
                    approach="Direct implementation based on understanding",
                    needs_clarification=False,
                )
            
            # Update context with reasoning
            context.understanding = reasoning.understanding
            context.approach = reasoning.approach
            context.needed_tools = reasoning.needed_tools
            context.needs_clarification = reasoning.needs_clarification
            context.clarification_question = reasoning.clarification_question
            
            # Check if clarification needed
            if reasoning.needs_clarification:
                question = reasoning.clarification_question or "Ich habe eine Rückfrage zu diesem Ticket."
                await self._post_comment(
                    context.ticket.ticket_id,
                    f"❓ {question}\n\nBitte antworte hier, dann mache ich weiter."
                )
                self.state_machine.needs_clarification(question)
                return
            
            # Transition to PLANNING
            print(f"   🧠 REASON complete: {context.understanding[:100]}")
            self.state_machine.transition_to(ORPAState.PLANNING, "Reasoning complete")
            
        except TimeoutError as e:
            print(f"   ❌ Reasoning timeout: {e}")
            if self._consecutive_llm_timeouts >= self.max_consecutive_llm_timeouts:
                question = (
                    "Das Modell hat mehrfach hintereinander nicht rechtzeitig geantwortet. "
                    "Bitte Ticket später erneut starten oder Anforderungen reduzieren."
                )
                context.needs_clarification = True
                context.clarification_question = question
                await self._post_comment(context.ticket.ticket_id, f"⚠️ {question}")
                self.state_machine.needs_clarification(question)
                return
            self.state_machine.complete(success=False, reason=f"Reasoning timeout: {e}")
        except Exception as e:
            print(f"   ❌ Reasoning failed: {e}")
            logger.exception("Reasoning failed")
            self.state_machine.complete(success=False, reason=f"Reasoning error: {e}")
    
    async def _plan(self, context: AgentContext):
        """ORPA: PLAN Phase - Create execution plan.
        
        Creates a detailed plan of which tools to execute
        and in what order.
        """
        print("   📋 ORPA Phase: PLANNING")
        logger.debug("ORPA Phase: PLANNING")
        
        try:
            # Build planning prompt
            prompt = self._build_planning_prompt(context)
            
            # Call LLM
            system_prompt = self._get_system_prompt(context, phase="planning")
            messages = [
                Message(role="system", content=system_prompt),
                Message(role="user", content=prompt)
            ]
            
            print(
                f"      Calling LLM for plan ({len(prompt)} chars prompt, timeout={self.llm_timeout_seconds}s)..."
            )
            response = await self._call_llm(
                messages=messages,
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens,
                phase="planning",
            )
            print(f"      LLM plan response: {len(response.content)} chars")
            
            # Parse execution plan
            plan = self._parse_plan_response(response.content, context)
            if not plan or not plan.steps:
                print("      ⚠️  Plan parse failed, requesting one strict retry...")
                retry_prompt = self._build_plan_retry_prompt(context, response.content)
                retry_response = await self._call_llm(
                    messages=[
                        Message(role="system", content=system_prompt),
                        Message(role="user", content=retry_prompt),
                    ],
                    temperature=self.config.llm_temperature,
                    max_tokens=self.config.llm_max_tokens,
                    phase="planning-retry",
                )
                plan = self._parse_plan_response(retry_response.content, context)
                if not plan or not plan.steps:
                    question = (
                        "Ich konnte keinen sicheren, maschinenlesbaren Ausführungsplan erzeugen. "
                        "Bitte beschreibe die gewünschte Änderung konkreter (Dateien/Zielverhalten)."
                    )
                    context.needs_clarification = True
                    context.clarification_question = question
                    await self._post_comment(context.ticket.ticket_id, f"❓ {question}")
                    self.state_machine.needs_clarification(question)
                    return
            
            # Ensure PR step exists when plan has repo changes (fixes LLM omission/truncation)
            plan = self._ensure_pr_step_if_repo_changes(plan, context)
            context.execution_plan = plan
            
            # Transition to ACTING
            self.state_machine.transition_to(ORPAState.ACTING, "Planning complete")
            
        except TimeoutError as e:
            logger.exception("Planning timeout")
            question = (
                "Planning hat wegen eines LLM-Timeouts nicht rechtzeitig geantwortet. "
                "Bitte Ticket erneut starten; falls es wieder passiert, Anfrage stärker eingrenzen."
            )
            if self._consecutive_llm_timeouts >= self.max_consecutive_llm_timeouts:
                question = (
                    "Mehrere LLM-Timeouts hintereinander im Planning. "
                    "Bitte Ticket später erneut starten oder präzisieren."
                )
            context.needs_clarification = True
            context.clarification_question = question
            await self._post_comment(context.ticket.ticket_id, f"⚠️ {question}\n\nTechnischer Hinweis: {e}")
            self.state_machine.needs_clarification(question)
            return
        except Exception as e:
            logger.exception("Planning failed")
            self.state_machine.complete(success=False, reason=f"Planning error: {e}")
    
    async def _act(self, context: AgentContext):
        """ORPA: ACT Phase - Execute the plan.
        
        Executes tools in sequence, handling errors and
        adapting the plan as needed.
        """
        logger.warning("ORPA Phase: ACTING - %d steps planned", 
                       len(context.execution_plan.steps) if context.execution_plan else 0)
        
        if not context.execution_plan or not context.execution_plan.steps:
            print("   ⚠️  No execution plan or 0 steps - failing")
            self.state_machine.complete(success=False, reason="No execution plan or empty plan")
            return

        evidence_gate = self._evaluate_evidence_gate(context)
        if not evidence_gate["passed"]:
            failures = int(context.observations.get("evidence_gate_failures", 0) or 0) + 1
            context.add_observation("evidence_gate_failures", failures)
            context.add_observation("evidence_gate_last_reason", evidence_gate["reason"])
            print(f"   ⚠️  Evidence gate blocked execution: {evidence_gate['reason']}")
            if failures <= self.max_evidence_gate_failures and context.iteration < self.config.max_iterations:
                context.add_observation("retrieval_failures", failures)
                self.state_machine.transition_to(
                    ORPAState.REASONING,
                    "Insufficient evidence, expanding retrieval context",
                )
            else:
                context.needs_clarification = True
                context.clarification_question = (
                    "Ich habe noch nicht genug belastbare Evidenz für eine sichere Umsetzung. "
                    "Bitte präzisiere Zielverhalten oder betroffene Dateien."
                )
                self.state_machine.needs_clarification(context.clarification_question)
            return
        
        try:
            results = []
            all_success = True
            
            for step in context.execution_plan.steps:
                print(f"   🔧 Step {step.step_number}: {step.tool_name} ({step.description})")
                
                # Check if tool is allowed
                if not self._is_tool_allowed(step.tool_name):
                    result = ToolExecutionResult(
                        step=step,
                        success=False,
                        error=f"Tool '{step.tool_name}' is not allowed",
                    )
                    results.append(result)
                    all_success = False
                    continue
                
                # Resolve __GENERATE__ placeholders in parameters
                params = dict(step.parameters)
                params = self._enforce_branch_reuse(context, step.tool_name, params)
                for key, value in params.items():
                    if value == "__GENERATE__":
                        print(f"      Generating content for '{key}'...")
                        params[key] = await self._generate_content(context, step)
                        print(f"      Generated {len(params[key])} chars")
                
                # Execute tool
                tool_result = await self.executor.execute(
                    tool_name=step.tool_name,
                    parameters=params,
                    agent_id=self.agent_id,
                    ticket_id=context.ticket.ticket_id
                )
                
                # Record result
                exec_result = ToolExecutionResult(
                    step=step,
                    success=tool_result.success,
                    data=tool_result.data,
                    error=tool_result.error,
                    execution_time_ms=tool_result.execution_time_ms or 0,
                )
                results.append(exec_result)
                self._update_context_git_state_from_step(context, step.tool_name, params, exec_result)
                
                if tool_result.success:
                    print(f"      ✓ Success: {str(tool_result.data)[:150]}")
                else:
                    all_success = False
                    print(f"      ✗ Failed: {tool_result.error}")
                    
                    # Check if we should continue or abort
                    if step.condition != "continue_on_error":
                        break
            
            # Update context
            context.execution_results = results
            
            # Decide next state
            if all_success:
                self.state_machine.complete(success=True, reason="All steps completed")
            else:
                # Check if we should retry/reason
                if context.iteration < self.config.max_iterations:
                    logger.info("Some steps failed, re-reasoning...")
                    self.state_machine.transition_to(
                        ORPAState.REASONING, 
                        "Some steps failed, re-evaluating"
                    )
                else:
                    self.state_machine.complete(
                        success=False, 
                        reason="Max iterations reached with failures"
                    )
            
        except Exception as e:
            logger.exception("Acting failed")
            self.state_machine.complete(success=False, reason=f"Execution error: {e}")

    def _evaluate_evidence_gate(self, context: AgentContext) -> Dict[str, Any]:
        """Ensure we have enough retrieval evidence before executing writes."""
        retrieval = context.observations.get("retrieval_quality_planning") or context.observations.get("retrieval_quality_reasoning") or {}
        score = int(retrieval.get("score", 0) or 0)
        hit_count = int(retrieval.get("hit_count", 0) or 0)
        if score >= self.retrieval_min_score and hit_count >= 2:
            return {"passed": True, "reason": "sufficient evidence"}
        return {
            "passed": False,
            "reason": f"low retrieval evidence (score={score}, hits={hit_count}, min_score={self.retrieval_min_score})",
        }
    
    # ==================================================================
    # PROMPT BUILDERS
    # ==================================================================
    
    def _get_system_prompt(self, context: Optional[AgentContext] = None, phase: str = "reasoning") -> str:
        """Build the system prompt from identity files + operational rules.
        
        Layers (in order of LLM weight):
        1. Identity (soul.md + rules.md) -- who am I, what are my constraints
        2. Operational workflow -- how to use tools, PR workflow
        3. Knowledge (knowledge.md) -- what do I know about my tech stack
        4. Memories (memories/*.md) -- curated learnings from the operator
        5. Customer context (customers/{id}/) -- per-customer specifics
        6. Session metadata -- customer_id, agent_id
        """
        customer_id = (
            context.ticket.customer_id if context and context.ticket.customer_id
            else self.config.customer_id
        )
        
        parts = []
        
        # --- Layer 1: Identity (from soul.md + rules.md) ---
        if self.identity_prompt:
            parts.append(self.identity_prompt)
        else:
            parts.append(f"Du bist {self.agent_id}, ein KI-Entwickler-Agent.")
        
        # --- Layer 2: Operational workflow (hardcoded system logic) ---
        parts.append("""DEINE AUFGABE:
1. Analysiere Tickets und entscheide welche Tools du brauchst
2. Erstelle detaillierte Pläne zur Umsetzung
3. Führe die Pläne aus und adaptiere bei Bedarf

PFLICHT-WORKFLOW FÜR CODE-ÄNDERUNGEN:
Jede Code-Änderung MUSS über einen Pull Request laufen. Folge IMMER diesem Workflow:
1. github_get_repo_info → Default-Branch ermitteln
2. github_create_branch → Feature-Branch erstellen (Name: "mohami/ticket-<kurzer-name>"), ODER bestehenden Ticket-Branch wiederverwenden
3. github_write_file → Dateien auf den Ticket-Branch schreiben (jeweils mit commit message)
4. github_create_pr → Pull Request vom Ticket-Branch zum Default-Branch erstellen oder vorhandenen Ticket-PR wiederverwenden

Nutze NIEMALS file_write für Änderungen an Kunden-Repositories. file_write ist NUR für temporäre lokale Dateien.
Wenn etwas unklar ist, frage nach (needs_clarification: true).""")
        
        # --- Layer 3: Knowledge (from knowledge.md) ---
        if self.knowledge:
            parts.append(f"## DEIN WISSEN\n{self.knowledge}")
        
        # --- Layer 4: Semantic retrieval from DB (agent memories + customer context) ---
        semantic_context = self._build_semantic_memory_context(context, phase=phase)
        if semantic_context:
            parts.append(semantic_context)
        elif self.memories:
            # Fallback only when DB memory is unavailable.
            truncated_memories = self.memories[: self.memories_fallback_chars]
            if len(self.memories) > len(truncated_memories):
                truncated_memories += "\n...[gekürzt]..."
            parts.append(f"## DEINE ERINNERUNGEN\n{truncated_memories}")
        
        # --- Layer 5: Session metadata ---
        parts.append(f"KUNDE: {customer_id}\nAGENT: {self.agent_id}")
        
        return "\n\n".join(parts)

    def _build_semantic_memory_context(self, context: Optional[AgentContext], phase: str = "reasoning") -> str:
        """Retrieve relevant memory chunks with adaptive budget and quality scoring."""
        if not context or not self.memory or not self.memory.long_term:
            return ""

        query_parts = [
            context.ticket.title or "",
            context.ticket.description or "",
            context.understanding or "",
            context.approach or "",
        ]
        base_query = "\n".join([p for p in query_parts if p]).strip()
        if not base_query:
            return ""

        budget = self._get_retrieval_budget(context, phase)
        queries = self._build_retrieval_queries(base_query, context, max_rewrites=self.retrieval_rewrite_loops)
        customer_id = context.ticket.customer_id or ""
        sections: List[str] = []

        try:
            identity_hits_all: List[Dict[str, Any]] = []
            memory_hits_all: List[Dict[str, Any]] = []
            customer_hits_all: List[Dict[str, Any]] = []

            for query in queries:
                identity_hits_all.extend(
                    self.memory.long_term.search(query=query, memory_type="agent_identity", limit=budget["identity_limit"])
                )
                memory_hits_all.extend(
                    self.memory.long_term.search(query=query, memory_type="agent_memories", limit=budget["memory_limit"])
                )
                customer_hits_all.extend(
                    self.memory.long_term.search(query=query, memory_type="customer_context", limit=budget["customer_limit"])
                )

            identity_hits = self._dedupe_hits(identity_hits_all)[: budget["identity_limit"]]
            memory_hits = self._dedupe_hits(memory_hits_all)[: budget["memory_limit"]]
            customer_hits = self._dedupe_hits(customer_hits_all)[: budget["customer_limit"]]

            # Keep retrieval metrics in context for evidence gates and diagnostics.
            quality = self._compute_retrieval_quality(
                base_query=base_query,
                hits=identity_hits + memory_hits + customer_hits,
            )
            context.add_observation(
                f"retrieval_quality_{phase}",
                {
                    **quality,
                    "queries_used": len(queries),
                    "budget": budget,
                },
            )

            if identity_hits:
                lines = [
                    f"- {h.get('content', '')[:budget['hit_chars']]}"
                    for h in identity_hits
                    if h.get("content")
                ]
                if lines:
                    sections.append("### RELEVANTES AGENT-IDENTITY-WISSEN\n" + "\n".join(lines))

            if memory_hits:
                lines = [
                    f"- {h.get('content', '')[:budget['hit_chars']]}"
                    for h in memory_hits
                    if h.get("content")
                ]
                if lines:
                    sections.append("### RELEVANTE AGENT-MEMORIES\n" + "\n".join(lines))

            if customer_hits:
                filtered = []
                for hit in customer_hits:
                    meta = hit.get("metadata", {}) if isinstance(hit, dict) else {}
                    if customer_id and (meta.get("customer_id") or "") not in {"", customer_id}:
                        continue
                    content = hit.get("content", "")
                    if content:
                        filtered.append(f"- {content[:budget['hit_chars']]}")
                if filtered:
                    sections.append("### RELEVANTER KUNDENKONTEXT (SEMANTISCH)\n" + "\n".join(filtered))
        except Exception as e:
            logger.debug(f"Semantic memory retrieval failed: {e}")
            return ""

        if not sections:
            return ""
        return "## SEMANTISCHER KONTEXT AUS LANGZEITGEDÄCHTNIS\n" + "\n\n".join(sections)

    def _get_retrieval_budget(self, context: AgentContext, phase: str) -> Dict[str, int]:
        """Select retrieval budget adaptively by phase and observed failures."""
        profile = "small"
        failures = int(context.observations.get("retrieval_failures", 0) or 0)
        gate_failures = int(context.observations.get("evidence_gate_failures", 0) or 0)
        if phase in {"planning", "acting"}:
            profile = "medium"
        if failures > 0 or gate_failures > 0 or context.iteration > 1:
            profile = "large"

        defaults = {
            "small": {
                "identity_limit": max(1, self.semantic_identity_limit),
                "memory_limit": max(1, self.semantic_memory_limit),
                "customer_limit": max(1, self.semantic_customer_limit),
                "hit_chars": max(120, self.semantic_hit_chars),
            },
            "medium": {
                "identity_limit": max(1, self.semantic_identity_limit + 1),
                "memory_limit": max(2, self.semantic_memory_limit + 2),
                "customer_limit": max(1, self.semantic_customer_limit + 1),
                "hit_chars": max(200, int(self.semantic_hit_chars * 1.4)),
            },
            "large": {
                "identity_limit": max(2, self.semantic_identity_limit + 2),
                "memory_limit": max(3, self.semantic_memory_limit + 3),
                "customer_limit": max(2, self.semantic_customer_limit + 2),
                "hit_chars": max(260, int(self.semantic_hit_chars * 1.8)),
            },
        }
        return defaults.get(profile, defaults["small"])

    def _build_retrieval_queries(
        self,
        base_query: str,
        context: AgentContext,
        max_rewrites: int = 2,
    ) -> List[str]:
        """Build query candidates without hardcoded domain logic."""
        queries = [base_query]
        keywords = self._extract_keywords(
            " ".join(
                [
                    context.ticket.title or "",
                    context.ticket.description or "",
                    context.understanding or "",
                    context.approach or "",
                ]
            )
        )
        if keywords:
            queries.append(" ".join(keywords[:8]))
        if len(keywords) >= 4:
            queries.append(" ".join(keywords[:4] + keywords[-2:]))
        return list(dict.fromkeys([q.strip() for q in queries[: 1 + max_rewrites] if q.strip()]))

    def _dedupe_hits(self, hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate retrieval hits by id/source while keeping best distance."""
        by_key: Dict[str, Dict[str, Any]] = {}
        for hit in hits:
            if not isinstance(hit, dict):
                continue
            key = str(hit.get("id") or (hit.get("metadata") or {}).get("source") or "")
            if not key:
                continue
            prev = by_key.get(key)
            if not prev:
                by_key[key] = hit
                continue
            prev_distance = float(prev.get("distance", 999))
            cur_distance = float(hit.get("distance", 999))
            if cur_distance < prev_distance:
                by_key[key] = hit
        return sorted(by_key.values(), key=lambda h: float(h.get("distance", 999)))

    def _compute_retrieval_quality(self, base_query: str, hits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute retrieval quality score (RQS) from count, distance and term coverage."""
        if not hits:
            return {"score": 0, "hit_count": 0, "avg_distance": 999, "coverage": 0.0}

        distances = [float(h.get("distance", 1.5)) for h in hits if h.get("distance") is not None]
        avg_distance = sum(distances) / len(distances) if distances else 1.5
        distance_score = max(0.0, min(35.0, (1.4 - avg_distance) / 1.4 * 35.0))

        count_score = max(0.0, min(40.0, len(hits) / 8.0 * 40.0))

        terms = [t for t in self._extract_keywords(base_query) if len(t) > 3][:12]
        if terms:
            hit_text = " ".join((h.get("content") or "").lower() for h in hits[:10])
            matched = sum(1 for t in terms if t in hit_text)
            coverage = matched / max(1, len(terms))
        else:
            coverage = 0.5
        coverage_score = max(0.0, min(25.0, coverage * 25.0))

        score = int(round(count_score + distance_score + coverage_score))
        return {
            "score": score,
            "hit_count": len(hits),
            "avg_distance": round(avg_distance, 4),
            "coverage": round(coverage, 4),
        }
    
    def _build_reasoning_prompt(
        self, 
        context: AgentContext, 
        tools_schemas: Optional[List[Dict]] = None
    ) -> str:
        """Build the prompt for the reasoning phase."""
        
        # Format observations
        observations_text = ""
        if context.repository_structure:
            dirs = context.repository_structure.get("directories", [])[:10]
            files = context.repository_structure.get("files", [])[:10]
            observations_text += f"\nVerzeichnisse: {[d['name'] for d in dirs]}"
            observations_text += f"\nDateien: {[f['name'] for f in files]}"
        
        if context.relevant_files:
            observations_text += f"\nRelevante Dateien: {context.relevant_files[:5]}"
        
        repo_profile = context.observations.get("repo_profile", {})
        if repo_profile:
            observations_text += f"\nRepo-Signale: {repo_profile.get('signals', [])[:8]}"
            observations_text += f"\nRepo-Test-Kommandos: {repo_profile.get('test_commands', [])[:4]}"
            observations_text += f"\nRepo-Lint-Kommandos: {repo_profile.get('lint_commands', [])[:4]}"
            observations_text += f"\nRepo-Build-Kommandos: {repo_profile.get('build_commands', [])[:4]}"
        
        # Format similar learnings
        learnings_text = ""
        if context.relevant_learnings:
            learnings_text = "\n\nÄHNLICHE LÖSUNGEN AUS DER VERGANGENHEIT:\n"
            for learning in context.relevant_learnings[:3]:
                learnings_text += f"- {learning.get('content', '')[:200]}...\n"
        
        repo_text = f"Repository: {context.ticket.repository}" if context.ticket.repository else "Repository: (nicht angegeben)"
        active_branch_text = context.ticket.branch or "(kein bestehender Branch)"
        active_pr_text = context.ticket.metadata.get("active_pr_url") or "(kein bestehender PR)"
        
        tools_prompt = (
            self._build_compact_tools_prompt()
            if self.compact_tools_prompt
            else self.tools.get_formatted_tools_prompt()
        )

        prompt = f"""
Analysiere dieses Ticket und entscheide wie du vorgehst.

=== TICKET ===
ID: {context.ticket.ticket_id}
Titel: {context.ticket.title}
{repo_text}
Aktiver Branch: {active_branch_text}
Aktiver PR: {active_pr_text}
Kunde: {context.ticket.customer_id or "unbekannt"}
Beschreibung:
{context.ticket.description}

=== BEOBACHTUNGEN ===
{observations_text}
{learnings_text}

=== VERFÜGBARE TOOLS ===
{tools_prompt}

=== DEINE AUFGABE ===
1. Analysiere das Ticket: Was will der User?
2. Identifiziere: Welche Tools brauche ich?
3. Entscheide: Was ist der beste Ansatz?

Antworte als JSON:
{{
    "understanding": "Klare Beschreibung was zu tun ist",
    "needed_tools": ["tool_name_1", "tool_name_2"],
    "approach": "Kurze Beschreibung des Vorgehens",
    "needs_clarification": false,
    "clarification_question": null,
    "confidence": 0.9
}}

Wenn etwas unklar ist, setze needs_clarification auf true und stelle eine konkrete Frage.
"""
        return prompt

    def _build_compact_tools_prompt(self) -> str:
        """Return a compact tool list to keep the reasoning prompt small."""
        lines = ["# Available Tools (compact)"]
        for tool in self.tools.list_available():
            desc = (tool.description or "").strip().replace("\n", " ")
            if len(desc) > 120:
                desc = f"{desc[:120]}..."
            lines.append(f"- {tool.name}: {desc}")
        return "\n".join(lines)
    
    def _build_planning_prompt(self, context: AgentContext) -> str:
        """Build the prompt for the planning phase."""
        repo_profile = context.observations.get("repo_profile", {})
        existing_branch = (context.ticket.branch or "").strip()
        existing_pr_url = (context.ticket.metadata.get("active_pr_url") or "").strip()
        has_existing_branch = bool(existing_branch)
        repo_profile_text = ""
        if repo_profile:
            repo_profile_text = (
                f"\n=== REPO-SIGNALE (aus Dateien/CI) ===\n"
                f"Signale: {repo_profile.get('signals', [])[:10]}\n"
                f"Test-Kommandos: {repo_profile.get('test_commands', [])[:5]}\n"
                f"Lint-Kommandos: {repo_profile.get('lint_commands', [])[:5]}\n"
                f"Build-Kommandos: {repo_profile.get('build_commands', [])[:5]}\n"
            )
        branch_instruction = (
            f"2. github_create_branch → BESTEHENDEN Branch '{existing_branch}' wiederverwenden (kein neuer Branchname)\n"
            f"3. github_write_file → Auf Branch '{existing_branch}' committen\n"
            f"4. github_create_pr → PR für Branch '{existing_branch}' aktualisieren/wiederverwenden"
            if has_existing_branch
            else "2. github_create_branch → Feature-Branch \"mohami/ticket-<name>\"\n"
                 "3. github_write_file → Dateien schreiben (EINE Datei pro Step)\n"
                 "4. github_create_pr → Pull Request erstellen"
        )
        branch_status_text = existing_branch if has_existing_branch else "(kein bestehender Branch)"
        pr_status_text = existing_pr_url if existing_pr_url else "(kein bestehender PR)"
        example_branch = existing_branch if has_existing_branch else "mohami/ticket-beispiel"
        
        tools_prompt = (
            self._build_compact_tools_prompt()
            if self.compact_tools_prompt
            else self.tools.get_formatted_tools_prompt()
        )

        prompt = f"""
Erstelle einen Ausführungsplan für dieses Ticket.

=== TICKET ===
Titel: {context.ticket.title}
Beschreibung: {context.ticket.description}

=== VERSTÄNDNIS ===
{context.understanding}

=== ANSATZ ===
{context.approach}

=== BESTEHENDE GIT-KONTEXTINFOS ===
Aktiver Branch: {branch_status_text}
Aktiver PR: {pr_status_text}

=== VERFÜGBARE TOOLS ===
{tools_prompt}
{repo_profile_text}

=== AUFGABE ===
Erstelle einen JSON-Plan mit Tool-Aufrufen.

PFLICHT-WORKFLOW für Repository-Änderungen:
1. github_get_repo_info → Default-Branch ermitteln
{branch_instruction}

KRITISCHE JSON-REGELN:
- Für "content" Parameter (Dateiinhalte): Nutze den Platzhalter "__GENERATE__"
- Beschreibe in "description" WAS der Inhalt sein soll
- Der tatsächliche Inhalt wird automatisch generiert
- Nutze github_write_file (NICHT file_write) für Repository-Änderungen
- Wenn ein sicherer Plan nicht möglich ist, liefere KEINEN riskanten Plan
- WENN "Aktiver Branch" gesetzt ist: KEINEN neuen Branch-Namen erfinden
- WENN "Aktiver PR" gesetzt ist: denselben PR-Branch wiederverwenden, kein separater Zweit-PR
- Repository: {context.ticket.repository}

Antworte NUR mit diesem JSON (keine Erklärung):
```json
{{
    "steps": [
        {{
            "step_number": 1,
            "tool": "github_get_repo_info",
            "parameters": {{"repo": "{context.ticket.repository}"}},
            "description": "Default-Branch ermitteln"
        }},
        {{
            "step_number": 2,
            "tool": "github_create_branch",
            "parameters": {{"repo": "{context.ticket.repository}", "branch_name": "{example_branch}", "from_branch": "main"}},
            "description": "Feature-Branch erstellen"
        }},
        {{
            "step_number": 3,
            "tool": "github_write_file",
            "parameters": {{"repo": "{context.ticket.repository}", "path": "datei.md", "content": "__GENERATE__", "branch": "{example_branch}", "message": "Add datei.md"}},
            "description": "Datei mit XYZ Inhalt erstellen"
        }},
        {{
            "step_number": 4,
            "tool": "github_create_pr",
            "parameters": {{"repo": "{context.ticket.repository}", "title": "Ticket: Beschreibung", "body": "...", "head_branch": "{example_branch}", "base_branch": "main"}},
            "description": "Pull Request erstellen"
        }}
    ]
}}
```
"""
        return prompt
    
    # ==================================================================
    # HELPERS
    # ==================================================================
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for file search."""
        # Simple keyword extraction
        # In production, this could use NLP
        words = text.lower().split()
        # Filter common words and technical terms
        tech_terms = [
            w for w in words 
            if len(w) > 3 and 
            w not in ["this", "that", "with", "from", "have", "should", "please"]
        ]
        # Return unique terms
        return list(dict.fromkeys(tech_terms))[:5]
    
    def _is_tool_allowed(self, tool_name: str) -> bool:
        """Check if a tool is allowed for this agent."""
        if self.config.forbidden_tools and tool_name in self.config.forbidden_tools:
            return False
        if self.config.allowed_tools is not None:
            return tool_name in self.config.allowed_tools
        return True
    
    async def _generate_content(self, context: AgentContext, step: ToolExecutionStep) -> str:
        """Generate file content via LLM for __GENERATE__ placeholders.
        
        Reads existing file from GitHub first (if it exists) so the LLM
        can modify rather than replace.
        """
        file_path = step.parameters.get("path", "unknown")
        repo = step.parameters.get("repo", context.ticket.repository)
        branch = step.parameters.get("branch", "main")
        
        existing_content = ""
        if repo:
            try:
                read_result = await self.executor.execute(
                    "github_read_file",
                    {"repo": repo, "path": file_path, "branch": branch},
                    agent_id=self.agent_id,
                    ticket_id=context.ticket.ticket_id,
                )
                if read_result.success and read_result.data:
                    existing_content = read_result.data.get("content", "")
                    print(f"      Read existing file: {len(existing_content)} chars")
            except Exception:
                pass
        
        existing_section = ""
        if existing_content:
            existing_section = f"""
BESTEHENDER INHALT der Datei (MUSS beibehalten werden, nur ergänzen/anpassen):
---
{existing_content}
---
WICHTIG: Behalte den bestehenden Inhalt bei und passe ihn nur gemäß der Aufgabe an."""
        else:
            existing_section = "\nDie Datei existiert noch nicht. Erstelle sie komplett neu."
        
        prompt = f"""Generiere den KOMPLETTEN Inhalt für die Datei '{file_path}'.

Ticket: {context.ticket.title}
Beschreibung: {context.ticket.description}
Repository: {context.ticket.repository}
Step-Beschreibung: {step.description}

Verständnis: {context.understanding[:300] if context.understanding else ''}
{existing_section}

Antworte NUR mit dem Dateiinhalt. Keine Erklärung, kein Markdown-Code-Block, nur den reinen Inhalt der Datei."""
        
        try:
            messages = [
                Message(role="system", content="Du bist ein Entwickler. Generiere NUR den angeforderten Dateiinhalt. Keine Erklärungen. Wenn eine bestehende Datei angegeben ist, behalte deren Inhalt bei und ergänze/ändere nur was nötig ist."),
                Message(role="user", content=prompt),
            ]
            response = await self._call_llm(
                messages=messages,
                temperature=0.3,
                max_tokens=4096,
                phase="content-generation",
            )
            content = response.content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:])
                if content.endswith("```"):
                    content = content[:-3].rstrip()
            return content
        except Exception as e:
            print(f"      ⚠️  Content generation failed: {e}")
            return f"# {context.ticket.title}\n\nContent generation failed. Please edit manually."
    
    def _parse_plan_response(self, raw_response: str, context: AgentContext) -> Optional[ToolExecutionPlan]:
        """Parse the LLM plan response with robust JSON handling (strict mode)."""
        
        content = raw_response
        
        # Extract JSON from markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            parts = content.split("```")
            if len(parts) >= 3:
                content = parts[1]
        
        # Try direct parse first
        try:
            plan_data = json.loads(content.strip())
            plan = self._build_plan_from_data(plan_data)
            return plan if plan.steps else None
        except json.JSONDecodeError:
            pass
        
        # Try to repair: replace unescaped newlines inside strings
        try:
            repaired = re.sub(r'(?<=": ")([^"]*?)(?=")', 
                            lambda m: m.group(0).replace('\n', '\\n'), 
                            content)
            plan_data = json.loads(repaired.strip())
            print("      JSON repaired successfully")
            plan = self._build_plan_from_data(plan_data)
            return plan if plan.steps else None
        except (json.JSONDecodeError, re.error):
            pass
        
        # Try to extract individual step objects via regex
        try:
            step_pattern = r'\{[^{}]*"tool"\s*:\s*"([^"]+)"[^{}]*"parameters"\s*:\s*(\{[^{}]*\})[^{}]*"description"\s*:\s*"([^"]*)"[^{}]*\}'
            matches = re.findall(step_pattern, raw_response, re.DOTALL)
            if matches:
                steps = []
                for i, (tool, params_str, desc) in enumerate(matches, 1):
                    try:
                        params = json.loads(params_str)
                    except json.JSONDecodeError:
                        params = {}
                    steps.append(ToolExecutionStep(
                        step_number=i, tool_name=tool,
                        parameters=params, description=desc,
                    ))
                print(f"      Extracted {len(steps)} steps via regex")
                return ToolExecutionPlan(steps=steps, estimated_steps=len(steps))
        except Exception:
            pass
        
        print("      ⚠️  All plan parsing attempts failed (strict mode)")
        return None
    
    def _build_plan_from_data(self, plan_data: dict) -> ToolExecutionPlan:
        """Build a ToolExecutionPlan from parsed JSON data."""
        steps_data = plan_data.get("steps", [])
        print(f"   📋 Plan: {len(steps_data)} steps")
        for s in steps_data:
            print(f"      → {s.get('tool', '?')}: {s.get('description', '')[:80]}")
        
        steps = []
        for i, step_data in enumerate(steps_data, 1):
            steps.append(ToolExecutionStep(
                step_number=i,
                tool_name=step_data.get("tool"),
                parameters=step_data.get("parameters", {}),
                description=step_data.get("description", ""),
                depends_on=step_data.get("depends_on"),
                condition=step_data.get("condition"),
            ))
        return ToolExecutionPlan(steps=steps, estimated_steps=len(steps))
    
    def _ensure_pr_step_if_repo_changes(
        self, plan: ToolExecutionPlan, context: AgentContext
    ) -> ToolExecutionPlan:
        """Append github_create_pr if plan has repo changes but no PR step (LLM omission/truncation)."""
        if not plan or not plan.steps or not context.ticket.repository:
            return plan

        has_repo_changes = any(
            s.tool_name in ("github_create_branch", "github_write_file")
            for s in plan.steps
        )
        has_pr_step = any(s.tool_name == "github_create_pr" for s in plan.steps)
        if not has_repo_changes or has_pr_step:
            return plan

        # Infer branch and base from plan / context
        branch = context.ticket.branch or ""
        repo_profile = context.observations.get("repo_profile", {})
        base_branch = repo_profile.get("default_branch", "main")
        for s in plan.steps:
            if s.tool_name == "github_create_branch":
                branch = s.parameters.get("branch_name", branch) or branch
            elif s.tool_name == "github_write_file":
                b = s.parameters.get("branch", "")
                if b:
                    branch = b
        if not branch:
            branch = f"mohami/ticket-{context.ticket.ticket_id[:8]}"

        next_num = max((s.step_number for s in plan.steps), default=0) + 1
        pr_step = ToolExecutionStep(
            step_number=next_num,
            tool_name="github_create_pr",
            parameters={
                "repo": context.ticket.repository,
                "title": f"Mohami: {context.ticket.title}",
                "body": (context.understanding or context.ticket.description or "")[:500],
                "head_branch": branch,
                "base_branch": base_branch,
            },
            description="Pull Request erstellen",
        )
        print(f"   📋 Plan ergänzt: PR-Step angehängt (Branch: {branch})")
        return ToolExecutionPlan(
            steps=list(plan.steps) + [pr_step],
            estimated_steps=len(plan.steps) + 1,
        )

    def _create_standard_github_plan(self, context: AgentContext) -> ToolExecutionPlan:
        """Create a standard GitHub workflow plan as last-resort fallback."""
        repo = context.ticket.repository
        if not repo:
            return ToolExecutionPlan(steps=[])
        
        branch_name = context.ticket.branch or f"mohami/ticket-{context.ticket.ticket_id[:8]}"
        title_slug = context.ticket.title.lower().replace(" ", "-")[:30]
        
        steps = [
            ToolExecutionStep(
                step_number=1, tool_name="github_get_repo_info",
                parameters={"repo": repo},
                description="Default-Branch ermitteln",
            ),
            ToolExecutionStep(
                step_number=2, tool_name="github_create_branch",
                parameters={"repo": repo, "branch_name": branch_name, "from_branch": "main"},
                description="Feature-Branch erstellen",
            ),
            ToolExecutionStep(
                step_number=3, tool_name="github_write_file",
                parameters={
                    "repo": repo, "path": f"{title_slug}.md",
                    "content": "__GENERATE__", "branch": branch_name,
                    "message": f"Add {context.ticket.title}",
                },
                description=f"Datei erstellen: {context.ticket.title}",
            ),
            ToolExecutionStep(
                step_number=4, tool_name="github_create_pr",
                parameters={
                    "repo": repo, "title": f"Mohami: {context.ticket.title}",
                    "body": context.understanding[:500] if context.understanding else context.ticket.description,
                    "head_branch": branch_name, "base_branch": "main",
                },
                description="Pull Request erstellen",
            ),
        ]
        print(f"   📋 Fallback Plan: {len(steps)} steps (standard GitHub workflow)")
        return ToolExecutionPlan(steps=steps, estimated_steps=len(steps))

    def _build_plan_retry_prompt(self, context: AgentContext, previous_output: str) -> str:
        """Request a strict machine-parseable JSON plan after parse failure."""
        return f"""
Dein vorheriger Plan war nicht sicher parsebar.
Erzeuge den Plan erneut als STRIKTES JSON mit Top-Level "steps".

Ticket: {context.ticket.title}
Repository: {context.ticket.repository}
Verständnis: {context.understanding[:600]}

Vorherige (fehlerhafte) Antwort:
---
{previous_output[:3000]}
---

Anforderungen:
- Nur JSON, keine Markdown-Codeblöcke, keine Erklärung.
- Jeder Step braucht: step_number, tool, parameters, description.
- Für Dateiinhalte immer "__GENERATE__" nutzen.
- Für Repo-Änderungen muss Branch + Write + PR enthalten sein.
"""

    async def _infer_repo_profile(self, context: AgentContext) -> Dict[str, Any]:
        """Infer minimal repo profile from repo-defined manifests/scripts/CI.

        No hardcoded framework logic: only collect signals and commands that
        are explicitly present in repository files.
        """
        repo = context.ticket.repository
        if not repo:
            return {}

        profile: Dict[str, Any] = {
            "repository": repo,
            "default_branch": "main",
            "signals": [],
            "test_commands": [],
            "lint_commands": [],
            "build_commands": [],
            "ci_defined": False,
        }

        try:
            info = await self.executor.execute(
                "github_get_repo_info",
                {"repo": repo},
                agent_id=self.agent_id,
                ticket_id=context.ticket.ticket_id
            )
            if info.success and info.data:
                profile["default_branch"] = info.data.get("default_branch", "main")
        except Exception:
            pass

        branch = profile["default_branch"]
        file_paths: List[str] = []
        try:
            listing = await self.executor.execute(
                "github_list_files",
                {"repo": repo, "branch": branch},
                agent_id=self.agent_id,
                ticket_id=context.ticket.ticket_id
            )
            if listing.success and listing.data:
                file_paths = [f.get("path", "") for f in listing.data.get("files", []) if f.get("path")]
        except Exception:
            pass

        if not file_paths:
            return profile

        interesting = {
            "package.json",
            "pyproject.toml",
            "requirements.txt",
            "composer.json",
            "Makefile",
            ".gitlab-ci.yml",
            "bitbucket-pipelines.yml",
        }
        workflow_files = [
            p for p in file_paths
            if p.startswith(".github/workflows/") and p.endswith((".yml", ".yaml"))
        ][:8]
        selected = [p for p in file_paths if p in interesting] + workflow_files

        for path in selected:
            try:
                read = await self.executor.execute(
                    "github_read_file",
                    {"repo": repo, "path": path, "branch": branch},
                    agent_id=self.agent_id,
                    ticket_id=context.ticket.ticket_id
                )
                if not read.success or not read.data:
                    continue
                content = read.data.get("content", "") or ""
                profile["signals"].append(path)

                if path == "package.json":
                    try:
                        pkg = json.loads(content)
                        scripts = pkg.get("scripts", {}) if isinstance(pkg, dict) else {}
                        if isinstance(scripts, dict):
                            if "test" in scripts:
                                profile["test_commands"].append("npm run test")
                            if "lint" in scripts:
                                profile["lint_commands"].append("npm run lint")
                            if "build" in scripts:
                                profile["build_commands"].append("npm run build")
                    except Exception:
                        pass
                elif path == "Makefile":
                    targets = re.findall(r"^([a-zA-Z0-9_.-]+)\s*:", content, re.MULTILINE)
                    for target in targets:
                        low = target.lower()
                        if "test" in low:
                            profile["test_commands"].append(f"make {target}")
                        if "lint" in low or "check" in low:
                            profile["lint_commands"].append(f"make {target}")
                        if "build" in low:
                            profile["build_commands"].append(f"make {target}")
                else:
                    for line in content.splitlines():
                        stripped = line.strip()
                        if "run:" in stripped:
                            cmd = stripped.split("run:", 1)[1].strip().strip("\"'")
                        elif stripped.startswith("- "):
                            cmd = stripped[2:].strip().strip("\"'")
                        else:
                            continue

                        low = cmd.lower()
                        if any(k in low for k in ["test", "pytest", "phpunit", "vitest", "jest"]):
                            profile["test_commands"].append(cmd)
                            profile["ci_defined"] = True
                        if any(k in low for k in ["lint", "flake8", "ruff", "eslint", "phpcs", "check"]):
                            profile["lint_commands"].append(cmd)
                            profile["ci_defined"] = True
                        if any(k in low for k in ["build", "compile"]):
                            profile["build_commands"].append(cmd)
                            profile["ci_defined"] = True
            except Exception:
                continue

        for key in ("signals", "test_commands", "lint_commands", "build_commands"):
            profile[key] = list(dict.fromkeys(profile[key]))

        return profile

    def _enforce_branch_reuse(
        self,
        context: AgentContext,
        tool_name: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Force reuse of the active ticket branch during rework cycles."""
        active_branch = (context.ticket.branch or "").strip()
        if not active_branch:
            return parameters

        patched = dict(parameters)
        if tool_name == "github_create_branch":
            patched["branch_name"] = active_branch
        elif tool_name == "github_write_file":
            patched["branch"] = active_branch
        elif tool_name == "github_create_pr":
            patched["head_branch"] = active_branch
        return patched

    def _update_context_git_state_from_step(
        self,
        context: AgentContext,
        tool_name: str,
        parameters: Dict[str, Any],
        result: ToolExecutionResult,
    ) -> None:
        """Capture branch/PR data from successful tool results for ticket persistence."""
        if not result.success:
            return

        if tool_name == "github_create_branch":
            branch_name = None
            if isinstance(result.data, dict):
                branch_name = result.data.get("branch_name")
            if not branch_name:
                branch_name = parameters.get("branch_name")
            if branch_name:
                context.ticket.branch = str(branch_name)

        elif tool_name == "github_write_file":
            branch = parameters.get("branch")
            if branch and not context.ticket.branch:
                context.ticket.branch = str(branch)

        elif tool_name == "github_create_pr":
            head_branch = parameters.get("head_branch")
            if head_branch:
                context.ticket.branch = str(head_branch)

            if isinstance(result.data, dict):
                pr_url = result.data.get("url")
                pr_number = result.data.get("pr_number")
                if pr_url and "/pull/" in str(pr_url):
                    context.ticket.metadata["active_pr_url"] = str(pr_url)
                if pr_number:
                    context.ticket.metadata["active_pr_number"] = str(pr_number)

    async def _persist_ticket_git_context(self, context: AgentContext) -> None:
        """Persist active branch/PR context to ticket record for follow-up iterations."""
        if not self.ticket_crud:
            return
        from ..kanban.schemas import TicketUpdate

        active_branch = context.ticket.branch
        active_pr_url = context.ticket.metadata.get("active_pr_url")
        active_pr_number = context.ticket.metadata.get("active_pr_number")

        if not (active_branch or active_pr_url or active_pr_number):
            return

        await self.ticket_crud.update(
            context.ticket.ticket_id,
            TicketUpdate(
                active_branch=active_branch,
                active_pr_url=active_pr_url,
                active_pr_number=active_pr_number,
            ),
        )

    async def _build_customer_completion_comment(
        self,
        context: AgentContext,
        changed_files: List[str],
    ) -> str:
        """Build a customer-friendly completion comment via LLM with safe fallback."""
        changed_files_text = ", ".join(changed_files[:15]) if changed_files else "(keine)"
        prompt = f"""
Erstelle einen Abschluss-Kommentar für ein Support-Ticket.

Zielgruppe: Nicht-technische Kundinnen und Kunden.
Sprache: Deutsch.
Ton: Freundlich, klar, ohne Fachjargon.
Format: Kurzer Markdown-Text (max. 6 kurze Sätze).

MUSS enthalten:
1. Kurze Bestätigung, dass die Aufgabe erledigt wurde.
2. Einfache Erklärung, was angepasst wurde.
3. 2-3 konkrete, leicht verständliche Testschritte für den Kunden.
4. Hinweis, dass der Kunde sich melden soll, falls etwas noch nicht passt.

WICHTIG:
- Keine Dateipfade, keine Dateinamen, kein Code, keine Toolnamen.
- Keine internen Begriffe wie "Verständnis", "Geänderte Dateien", "ORPA", "github_write_file".
- Keine technische Aufzählung interner Arbeitsschritte.

Tickettitel: {context.ticket.title}
Ticketbeschreibung: {context.ticket.description}
Interne Kurz-Zusammenfassung: {context.understanding[:600]}
Interner Ansatz: {context.approach[:600]}
Interne Dateiliste (nur Kontext, NICHT ausgeben): {changed_files_text}

Antworte nur mit dem finalen Kommentartext.
"""
        try:
            system_prompt = self._get_system_prompt(context, phase="completion")
            response = await self._call_llm(
                messages=[
                    Message(role="system", content=system_prompt),
                    Message(role="user", content=prompt),
                ],
                temperature=0.2,
                max_tokens=500,
                phase="completion-comment",
            )
            comment = (response.content or "").strip()
            if comment:
                return comment
        except Exception as e:
            logger.debug(f"Completion comment generation failed, using fallback: {e}")

        return (
            "✅ **Fertig!**\n\n"
            "Ich habe die gewünschte Anpassung umgesetzt.\n\n"
            "Bitte teste kurz:\n"
            "- Prüfe die betroffene Funktion in deinem normalen Ablauf.\n"
            "- Wiederhole den Schritt, bei dem das Problem vorher aufgetreten ist.\n"
            "- Kontrolliere, ob das erwartete Ergebnis jetzt zuverlässig erscheint.\n\n"
            "Wenn noch etwas nicht passt, schreib mir bitte kurz, was du genau siehst."
        )

    async def _validate_minimal_quality_gates(self, context: AgentContext) -> Dict[str, Any]:
        """Validate minimal workflow gates before reporting success."""
        if not context.ticket.repository:
            return {"passed": True, "details": ["Kein Repository angegeben – Gates übersprungen."]}

        successful = [r for r in context.execution_results if r.success]
        branch_ok = bool(context.ticket.branch) or any(
            r.step.tool_name == "github_create_branch" for r in successful
        )
        commit_ok = any(
            r.step.tool_name == "github_write_file"
            and isinstance(r.data, dict)
            and bool(r.data.get("commit_sha"))
            for r in successful
        )
        pr_results = [r for r in successful if r.step.tool_name == "github_create_pr"]
        pr_ok = bool(context.ticket.metadata.get("active_pr_url")) or any(
            isinstance(r.data, dict) and bool(r.data.get("url")) for r in pr_results
        )

        details: List[str] = []
        if not branch_ok:
            details.append("Feature-Branch wurde nicht erfolgreich erstellt.")
        if not commit_ok:
            details.append("Kein bestätigter Commit aus `github_write_file` gefunden.")
        if self.require_pr_for_success and not pr_ok:
            details.append("Pull Request wurde nicht erfolgreich erstellt.")

        # Optional: evaluate provider checks if available.
        if pr_ok and hasattr(self.git_provider, "get_pr_checks_summary"):
            pr_number = None
            for res in pr_results:
                if isinstance(res.data, dict) and res.data.get("pr_number"):
                    pr_number = res.data.get("pr_number")
                    break
            if pr_number:
                try:
                    checks = await self.git_provider.get_pr_checks_summary(
                        context.ticket.repository, int(pr_number)
                    )
                    conclusion = (checks or {}).get("conclusion", "unknown")
                    if conclusion in {"failure", "cancelled", "timed_out", "action_required"}:
                        details.append(f"PR-Checks melden Fehlerstatus: {conclusion}.")
                except Exception as e:
                    logger.debug(f"Optional PR checks lookup failed: {e}")

        return {"passed": len(details) == 0, "details": details}
    
    def _create_result(self, context: AgentContext, success: bool) -> AgentResult:
        """Create the final result."""
        
        # Extract files modified from execution results
        files_modified = []
        for result in context.execution_results:
            if result.success and result.data:
                if isinstance(result.data, dict):
                    path = result.data.get("path")
                    if path:
                        files_modified.append(path)
        
        # Create message based on outcome
        if success:
            message = f"Ticket processed successfully. "
            message += f"Completed in {context.iteration} iterations."
        else:
            if context.needs_clarification:
                message = f"Needs clarification: {context.clarification_question}"
            else:
                message = f"Processing incomplete. Check execution results."
        
        result = AgentResult(
            ticket_id=context.ticket.ticket_id,
            success=success,
            message=message,
            files_modified=files_modified,
            iterations_used=context.iteration,
            final_state=self.state_machine.current_state,
        )
        
        # Record in memory if available
        if self.memory and success:
            episode = LearningEpisode(
                ticket_id=context.ticket.ticket_id,
                problem=context.ticket.description[:200],
                solution=context.understanding[:200],
                success=success,
                episode_type="resolution" if success else "error",
                metadata={
                    "approach": context.approach,
                    "tools_used": ",".join(context.needed_tools) if context.needed_tools else "",
                    "iterations": context.iteration,
                }
            )
            self.memory.record_learning(episode)
        
        return result
    
    # ==================================================================
    # KANBAN INTEGRATION
    # ==================================================================
    
    async def _post_comment(self, ticket_id: str, content: str):
        """Post a comment to a ticket if CommentCRUD is available."""
        if not self.comment_crud:
            logger.debug(f"No comment_crud, skipping comment on {ticket_id}")
            return
        try:
            from ..kanban.schemas import CommentCreate
            comment = CommentCreate(author=self.agent_id, content=content)
            await self.comment_crud.create(ticket_id, comment)
        except Exception as e:
            logger.warning(f"Failed to post comment: {e}")
    
    # ==================================================================
    # UTILITY METHODS
    # ==================================================================
    
    async def execute_tool(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any],
        ticket_id: Optional[str] = None
    ) -> ToolResult:
        """Execute a single tool directly.
        
        This is a convenience method for direct tool execution
        outside of the ORPA workflow.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            ticket_id: Optional ticket ID for logging
            
        Returns:
            ToolResult from execution
        """
        return await self.executor.execute(
            tool_name=tool_name,
            parameters=parameters,
            agent_id=self.agent_id,
            ticket_id=ticket_id
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_id": self.agent_id,
            "customer_id": self.config.customer_id,
            "orpa_state": self.state_machine.current_state.value,
            "iteration": self.state_machine.iteration_count,
            "tools_registered": len(self.tools),
            "memory_enabled": self.memory is not None,
            "workspace_enabled": self.workspace is not None,
        }
    
    def __repr__(self) -> str:
        return f"<IntelligentAgent: {self.agent_id}, state={self.state_machine.current_state.value}>"
