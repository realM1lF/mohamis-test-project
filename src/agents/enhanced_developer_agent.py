"""Enhanced Developer Agent with Tool-Use Framework.

This module provides an enhanced version of the DeveloperAgent that uses
the Tool-Use Framework instead of hardcoded logic.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any

from ..git_provider import GitProvider
from ..kanban.crud_async import TicketCRUD, CommentCRUD
from ..kanban.schemas import TicketUpdate, CommentCreate
from ..llm.kimi_client import KimiClient, Message
from ..tools.base import ToolResult
from ..tools.agent_integration import AgentToolManager, ToolCall


class AgentState(Enum):
    """Agent execution states."""
    IDLE = "idle"
    OBSERVING = "observing"
    REASONING = "reasoning"
    PLANNING = "planning"
    ACTING = "acting"
    TOOL_EXECUTION = "tool_execution"


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
    repo_structure: str = ""
    is_empty_repo: bool = True
    plan: Optional[str] = None
    tool_results: List[Dict] = field(default_factory=list)


class ToolUseDeveloperAgent:
    """Developer Agent with Tool-Use Framework.
    
    This agent uses the Tool-Use Framework to dynamically decide
    which tools to use based on the task at hand, rather than
    using hardcoded logic.
    
    Example:
        agent = ToolUseDeveloperAgent(
            git_provider=git_provider,
            llm_client=llm_client,
            ticket_crud=ticket_crud,
            comment_crud=comment_crud,
        )
        await agent.process_ticket(ticket_id)
    """
    
    def __init__(
        self,
        git_provider: GitProvider,
        llm_client: KimiClient,
        ticket_crud: TicketCRUD,
        comment_crud: CommentCRUD,
        agent_id: str = "mohami-tool"
    ):
        """Initialize the enhanced developer agent.
        
        Args:
            git_provider: Git provider for repository operations
            llm_client: LLM client for code generation
            ticket_crud: Ticket CRUD operations
            comment_crud: Comment CRUD operations
            agent_id: Unique agent identifier
        """
        self.agent_id = agent_id
        self.git = git_provider
        self.llm = llm_client
        self.tickets = ticket_crud
        self.comments = comment_crud
        self.state = AgentState.IDLE
        self.current_context: Optional[AgentContext] = None
        
        # Initialize tool manager
        self.tool_manager = AgentToolManager()
        self.tool_manager.register_default_tools()
    
    async def process_ticket(self, ticket_id: str) -> None:
        """Process a ticket using the tool-use workflow.
        
        This method implements the ORPA workflow with dynamic tool selection.
        
        Args:
            ticket_id: ID of the ticket to process
        """
        try:
            # OBSERVE Phase
            self.state = AgentState.OBSERVING
            context = await self._observe(ticket_id)
            self.current_context = context
            
            # REASON Phase - with tool use
            self.state = AgentState.REASONING
            analysis = await self._reason_with_tools(context)
            
            # PLAN Phase - with tool use
            self.state = AgentState.PLANNING
            plan = await self._plan_with_tools(context, analysis)
            context.plan = plan
            
            # ACT Phase - with tool use
            self.state = AgentState.ACTING
            await self._act_with_tools(context, analysis, plan)
            
        except Exception as e:
            await self._handle_error(ticket_id, e)
        finally:
            self.state = AgentState.IDLE
            self.current_context = None
    
    async def _observe(self, ticket_id: str) -> AgentContext:
        """OBSERVE: Analyze repository and ticket.
        
        Args:
            ticket_id: Ticket ID
            
        Returns:
            Populated AgentContext
        """
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
        
        # Use tools to gather repository information
        try:
            # Check repository state using git status tool
            repo_info = await self.git.get_repository_info(ticket.repository)
            context.tech_stack["default_branch"] = repo_info.default_branch
            
            # Try to get file listing
            branches = await self.git.list_branches(ticket.repository)
            
            # Try to read README
            try:
                readme = await self.git.get_file_content(
                    ticket.repository, "README.md", repo_info.default_branch
                )
                context.files_read.append("README.md")
                context.is_empty_repo = False
                context.repo_structure = "Repository has README.md"
            except:
                context.is_empty_repo = True
                context.repo_structure = "Empty repository (no README.md)"
                
        except Exception as e:
            context.repo_structure = f"Could not analyze repo: {e}"
        
        return context
    
    async def _reason_with_tools(self, context: AgentContext) -> str:
        """REASON: Analyze what needs to be done using tools.
        
        The LLM decides whether to use tools to gather more information
        or proceed directly with the analysis.
        
        Args:
            context: Agent context
            
        Returns:
            Analysis result
        """
        # Build system prompt with tools
        system_prompt = """Du bist Mohami, ein KI-Entwickler. Analysiere das Ticket und entscheide:
1. Brauche ich mehr Informationen? Dann nutze die verfügbaren Tools.
2. Kann ich direkt implementieren? Dann gib eine klare Analyse.

Antworte auf Deutsch. Denke Schritt für Schritt."""

        # Add tool descriptions
        tool_prompt = self.tool_manager.get_system_prompt_with_tools()
        full_system_prompt = f"{system_prompt}\n\n{tool_prompt}"
        
        # Build user prompt
        user_prompt = f"""Ticket: {context.ticket_title}
Beschreibung: {context.ticket_description}
Repository: {context.repository}
Status: {context.repo_structure}

Analysiere das Ticket. Nutze Tools wenn nötig, um mehr zu erfahren."""

        messages = [
            Message(role="system", content=full_system_prompt),
            Message(role="user", content=user_prompt),
        ]
        
        # Run tool loop for reasoning phase
        result = await self._run_tool_loop(
            messages=messages,
            max_iterations=3,
            ticket_id=context.ticket_id
        )
        
        # Store tool results in context
        context.tool_results.extend(result.get("tool_calls_made", []))
        
        return result.get("final_response", "")
    
    async def _plan_with_tools(self, context: AgentContext, analysis: str) -> str:
        """PLAN: Create implementation plan using tools.
        
        Args:
            context: Agent context
            analysis: Previous analysis
            
        Returns:
            Implementation plan
        """
        system_prompt = """Du bist Mohami. Erstelle einen Implementierungsplan.
Nutze Tools um:
- Die Repository-Struktur zu erkunden
- Existierende Dateien zu analysieren
- Den besten Ansatz zu bestimmen

Antworte auf Deutsch."""

        tool_prompt = self.tool_manager.get_system_prompt_with_tools()
        full_system_prompt = f"{system_prompt}\n\n{tool_prompt}"
        
        user_prompt = f"""Analyse: {analysis}

Ticket: {context.ticket_title}
Beschreibung: {context.ticket_description}

Erstelle einen detaillierten Plan:
1. Welche Tools brauche ich?
2. Welche Dateien erstelle/ändere ich?
3. Was ist die Commit-Strategie?"""

        messages = [
            Message(role="system", content=full_system_prompt),
            Message(role="user", content=user_prompt),
        ]
        
        result = await self._run_tool_loop(
            messages=messages,
            max_iterations=5,
            ticket_id=context.ticket_id
        )
        
        context.tool_results.extend(result.get("tool_calls_made", []))
        
        return result.get("final_response", "")
    
    async def _act_with_tools(
        self,
        context: AgentContext,
        analysis: str,
        plan: str
    ) -> None:
        """ACT: Implement using tools.
        
        Args:
            context: Agent context
            analysis: Analysis result
            plan: Implementation plan
        """
        # Check if we need clarification
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
            # IMPLEMENT using tool loop
            await self._implement_with_tools(context, plan)
    
    async def _implement_with_tools(self, context: AgentContext, plan: str) -> None:
        """Actually implement using tools.
        
        Args:
            context: Agent context
            plan: Implementation plan
        """
        system_prompt = """Du bist Mohami. Implementiere das Ticket.
Nutze die verfügbaren Tools um:
1. Dateien zu lesen und zu verstehen
2. Neuen Code zu generieren
3. Dateien zu schreiben
4. Git-Operationen durchzuführen

Antworte auf Deutsch."""

        tool_prompt = self.tool_manager.get_system_prompt_with_tools()
        full_system_prompt = f"{system_prompt}\n\n{tool_prompt}"
        
        user_prompt = f"""Implementiere dieses Ticket:

Titel: {context.ticket_title}
Beschreibung: {context.ticket_description}

Plan: {plan}

Repository: {context.repository}
Status: {"Leeres Repo" if context.is_empty_repo else "Bestehendes Repo"}

Führe die Implementierung durch:
1. Lies relevante Dateien (file_read)
2. Schreibe neue/aktualisierte Dateien (file_write)
3. Erstelle Git-Branch wenn nötig (git_branch)
4. Erstelle Commit (git_commit)

Arbeite Schritt für Schritt und nutze die Tools."""

        messages = [
            Message(role="system", content=full_system_prompt),
            Message(role="user", content=user_prompt),
        ]
        
        result = await self._run_tool_loop(
            messages=messages,
            max_iterations=10,
            ticket_id=context.ticket_id
        )
        
        # Add summary comment
        tool_calls = result.get("tool_calls_made", [])
        files_modified = [
            call["parameters"].get("path", "unknown")
            for call in tool_calls
            if call["tool"] == "file_write" and call["result"]["success"]
        ]
        
        summary = f"""✅ **Implementierung abgeschlossen**

**Durchgeführte Aktionen:**
- {len(tool_calls)} Tool-Aufrufe
- {len(files_modified)} Dateien modifiziert

**Geänderte Dateien:**
{chr(10).join([f'- {f}' for f in files_modified]) if files_modified else '- Keine'}

**Status:** {'Erfolgreich' if result.get('complete') else 'Unvollständig'}
"""
        
        await self._add_comment(context.ticket_id, summary)
        await self.tickets.update(
            context.ticket_id,
            TicketUpdate(status="done" if result.get("complete") else "clarification")
        )
    
    async def _run_tool_loop(
        self,
        messages: List[Message],
        max_iterations: int = 5,
        ticket_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run a loop of LLM -> Tool -> LLM.
        
        Args:
            messages: Initial messages
            max_iterations: Maximum iterations
            ticket_id: Ticket ID for context
            
        Returns:
            Final result with history
        """
        conversation_history = []
        tool_calls_made = []
        
        for iteration in range(max_iterations):
            self.state = AgentState.TOOL_EXECUTION
            
            # Get LLM response
            response = await self.llm.chat(messages, temperature=0.3, max_tokens=1000)
            content = response.content
            
            conversation_history.append({"role": "assistant", "content": content})
            
            # Check for tool calls
            tool_calls = self.tool_manager.parse_tool_calls(content)
            
            if not tool_calls:
                # No tool calls, we're done
                return {
                    "complete": True,
                    "final_response": content,
                    "conversation_history": conversation_history,
                    "tool_calls_made": tool_calls_made,
                    "iterations": iteration + 1,
                }
            
            # Execute tool calls
            for tool_call in tool_calls:
                self.state = AgentState.TOOL_EXECUTION
                
                result = await self.tool_manager.execute_tool_call(
                    tool_call,
                    agent_id=self.agent_id,
                    ticket_id=ticket_id
                )
                
                tool_calls_made.append({
                    "tool": tool_call.tool_name,
                    "parameters": tool_call.parameters,
                    "result": result.to_dict(),
                })
                
                # Format result for LLM
                result_message = self.tool_manager.format_tool_result_for_llm(result)
                
                # Add to conversation
                messages.append(Message(role="assistant", content=content))
                messages.append(Message(role="user", content=result_message))
                conversation_history.append({"role": "tool", "content": result_message})
        
        # Max iterations reached
        return {
            "complete": False,
            "final_response": "Maximum iterations reached",
            "conversation_history": conversation_history,
            "tool_calls_made": tool_calls_made,
            "iterations": max_iterations,
        }
    
    def _check_needs_clarification(
        self,
        analysis: str,
        plan: str,
        context: AgentContext
    ) -> bool:
        """Check if clarification is needed.
        
        Args:
            analysis: Analysis text
            plan: Plan text
            context: Context
            
        Returns:
            True if clarification needed
        """
        # Simple heuristic - check for question words
        combined = (analysis + " " + plan).lower()
        
        question_indicators = [
            "unklar", "frage", "rückfrage", "?",
            "nicht spezifiziert", "fehlende information",
        ]
        
        return any(indicator in combined for indicator in question_indicators)
    
    async def _generate_question(self, context: AgentContext, analysis: str) -> str:
        """Generate a clarification question.
        
        Args:
            context: Context
            analysis: Analysis
            
        Returns:
            Question text
        """
        system_prompt = "Du bist Mohami. Stelle EINE konkrete Rückfrage. Maximal 2 Sätze. Deutsch."
        
        user_prompt = f"""Analyse: {analysis}

Stelle EINE kurze, präzise Frage an den Kunden. Was ist das wichtigste Unklare?"""
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt),
        ]
        
        response = await self.llm.chat(messages, temperature=0.3, max_tokens=200)
        return response.content.strip()
    
    async def _add_comment(self, ticket_id: str, content: str) -> None:
        """Add a comment to the ticket.
        
        Args:
            ticket_id: Ticket ID
            content: Comment content
        """
        comment = CommentCreate(
            author=self.agent_id,
            content=content
        )
        await self.comments.create(ticket_id, comment)
    
    async def _handle_error(self, ticket_id: str, error: Exception) -> None:
        """Handle errors.
        
        Args:
            ticket_id: Ticket ID
            error: Exception that occurred
        """
        await self._add_comment(ticket_id, f"❌ Fehler: {str(error)[:200]}")
        print(f"Agent {self.agent_id} error on ticket {ticket_id}: {error}")
