"""Load and manage agent configuration from markdown files."""

import os
import re
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class AgentPersonality:
    """Agent personality configuration."""
    name: str
    description: str
    personality_traits: List[str]
    communication_style: str
    strengths: List[str]
    weaknesses: List[str]


@dataclass
class AgentRules:
    """Agent rules and constraints."""
    hard_constraints: List[str]
    code_quality_rules: List[str]
    communication_rules: List[str]
    business_rules: List[str]


@dataclass
class AgentConfig:
    """Complete agent configuration."""
    personality: AgentPersonality
    rules: AgentRules
    system_prompt: str


class AgentConfigLoader:
    """Loads agent configuration from markdown files.
    
    Structure:
        agents/{agent_id}/
            soul.md       - Personality definition
            rules.md      - Hard constraints and rules
    """
    
    def __init__(self, base_path: str = "./agents"):
        self.base_path = Path(base_path)
    
    def load_config(self, agent_id: str) -> AgentConfig:
        """Load complete configuration for an agent.
        
        Args:
            agent_id: Agent identifier (e.g., "mohami")
        
        Returns:
            AgentConfig with personality, rules, and system prompt
        """
        agent_path = self.base_path / agent_id
        
        if not agent_path.exists():
            # Return default config if no custom config exists
            return self._default_config(agent_id)
        
        # Load soul and rules
        personality = self._load_soul(agent_path / "soul.md", agent_id)
        rules = self._load_rules(agent_path / "rules.md")
        
        # Generate system prompt
        system_prompt = self._build_system_prompt(personality, rules)
        
        return AgentConfig(
            personality=personality,
            rules=rules,
            system_prompt=system_prompt
        )
    
    def _load_soul(self, soul_path: Path, agent_id: str) -> AgentPersonality:
        """Parse soul.md file."""
        if not soul_path.exists():
            return self._default_personality(agent_id)
        
        content = soul_path.read_text(encoding="utf-8")
        
        # Parse sections
        name = self._extract_heading(content, "#") or agent_id
        description = self._extract_section(content, "## Persönlichkeit")
        traits = self._extract_list(content, "## Persönlichkeit")
        style = self._extract_section(content, "## Kommunikationsstil")
        strengths = self._extract_list(content, "## Stärken")
        weaknesses = self._extract_list(content, "## Schwächen")
        
        return AgentPersonality(
            name=name.strip("# "),
            description=description,
            personality_traits=traits,
            communication_style=style,
            strengths=strengths,
            weaknesses=weaknesses
        )
    
    def _load_rules(self, rules_path: Path) -> AgentRules:
        """Parse rules.md file."""
        if not rules_path.exists():
            return self._default_rules()
        
        content = rules_path.read_text(encoding="utf-8")
        
        hard_constraints = self._extract_list(content, "## Hard Constraints")
        code_rules = self._extract_list(content, "## Code-Qualität")
        comm_rules = self._extract_list(content, "## Kommunikation")
        business_rules = self._extract_list(content, "## Geschäftsregeln")
        
        return AgentRules(
            hard_constraints=hard_constraints,
            code_quality_rules=code_rules,
            communication_rules=comm_rules,
            business_rules=business_rules
        )
    
    def _build_system_prompt(self, personality: AgentPersonality, rules: AgentRules) -> str:
        """Build system prompt from personality and rules."""
        prompt_parts = [
            f"Du bist {personality.name}, ein KI-Entwickler-Agent.",
            "",
            "## Deine Persönlichkeit",
            personality.description,
            "",
            "## Kommunikationsstil",
            personality.communication_style,
            "",
            "## Deine Stärken",
            "\n".join(f"- {s}" for s in personality.strengths) if personality.strengths else "- Zuverlässig und effizient",
            "",
            "## Harte Constraints (NIEMALS brechen)",
            "\n".join(f"- {c}" for c in rules.hard_constraints) if rules.hard_constraints else "- Niemals Kundendaten teilen",
            "",
            "## Code-Qualitäts-Regeln",
            "\n".join(f"- {r}" for r in rules.code_quality_rules) if rules.code_quality_rules else "- Sauberer Code",
            "",
            "## Kommunikations-Regeln",
            "\n".join(f"- {r}" for r in rules.communication_rules) if rules.communication_rules else "- Auf Deutsch antworten",
            "",
            "Arbeite professionell und effizient. Wenn etwas unklar ist, stelle präzise Rückfragen.",
        ]
        
        return "\n".join(prompt_parts)
    
    def _extract_heading(self, content: str, level: str) -> Optional[str]:
        """Extract main heading."""
        pattern = f"^\\{level} (.+)$"
        match = re.search(pattern, content, re.MULTILINE)
        return match.group(1).strip() if match else None
    
    def _extract_section(self, content: str, heading: str) -> str:
        """Extract text content under a heading (until next heading)."""
        pattern = f"{re.escape(heading)}\\s*\\n(.*?)(?=\\n## |\\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_list(self, content: str, heading: str) -> List[str]:
        """Extract list items under a heading."""
        section = self._extract_section(content, heading)
        # Find all list items (lines starting with - or •)
        items = re.findall(r"^[\s]*[-•][\s]+(.+)$", section, re.MULTILINE)
        return [item.strip() for item in items if item.strip()]
    
    def _default_config(self, agent_id: str) -> AgentConfig:
        """Return default configuration."""
        personality = self._default_personality(agent_id)
        rules = self._default_rules()
        system_prompt = self._build_system_prompt(personality, rules)
        
        return AgentConfig(
            personality=personality,
            rules=rules,
            system_prompt=system_prompt
        )
    
    def _default_personality(self, agent_id: str) -> AgentPersonality:
        """Default personality if no soul.md exists."""
        return AgentPersonality(
            name=agent_id,
            description="Ein hilfsbereiter KI-Entwickler.",
            personality_traits=["professionell", "effizient"],
            communication_style="Klar und prägnant auf Deutsch.",
            strengths=["Code-Qualität", "Problemlösung"],
            weaknesses=["Braucht klare Anforderungen"]
        )
    
    def _default_rules(self) -> AgentRules:
        """Default rules if no rules.md exists."""
        return AgentRules(
            hard_constraints=[
                "Niemals Kundendaten mit Dritten teilen",
                "Keine API-Keys oder Passwörter in Code",
            ],
            code_quality_rules=[
                "Alle Änderungen müssen getestet sein",
                "Keine direkten Commits auf main ohne PR",
            ],
            communication_rules=[
                "Auf Deutsch antworten",
                "Maximal 1 Rückfrage pro Ticket",
            ],
            business_rules=[
                "Keine Preisangebote machen",
                "Keine Zusagen ohne menschliche Bestätigung",
            ]
        )
