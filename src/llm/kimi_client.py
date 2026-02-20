"""Kimi 2.5 LLM client using Moonshot AI API."""

import os
from dataclasses import dataclass
from typing import AsyncGenerator, Dict, List, Optional

import httpx


@dataclass
class Message:
    """Chat message."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """LLM response."""
    content: str
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    model: str


class KimiClient:
    """Client for Kimi 2.5 via Moonshot AI API.
    
    Docs: https://platform.moonshot.cn/docs
    """
    
    BASE_URL = "https://openrouter.ai/api/v1"
    MODEL = "moonshotai/kimi-k2.5"  # Kimi 2.5 via OpenRouter
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPEN_ROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("KIMI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key required. Set OPENROUTER_API_KEY env var.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/realM1lF/personal-ki-agents",
            "X-Title": "KI-Mitarbeiter Agent"
        }
    
    async def chat(
        self,
        messages: List[Message],
        temperature: float = 0.3,
        max_tokens: Optional[int] = 4096  # Default to avoid OpenRouter limits
    ) -> LLMResponse:
        """Send chat completion request."""
        payload = {
            "model": self.MODEL,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=120.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Kimi API error: {response.status_code} - {response.text}")
            
            data = response.json()
            
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                usage=data.get("usage", {}),
                model=data.get("model", self.MODEL)
            )
    
    def create_system_prompt(self, context: Dict) -> str:
        """Create system prompt for Developer Agent (German)."""
        return f"""Du bist ein KI-Entwickler-Agent. Du hilfst bei Software-Projekten.

KONTEXT:
- Kunde: {context.get('customer', 'Unbekannt')}
- Repository: {context.get('repository', 'Unbekannt')}
- Projekt-Typ: {context.get('project_type', 'Unbekannt')}

DEINE AUFGABE:
1. Analysiere das Ticket und den Code
2. Prüfe selbstständig: Lese Repository, Dateien, Struktur
3. Stelle NUR Rückfragen, wenn du NICHT selbst herausfinden kannst
4. Wenn klar: Implementiere direkt

REGELN:
- Antworte auf DEUTSCH
- Sei prägnant (max 3-4 Sätze pro Phase)
- Prüfe erst, dann frage
- Keine Wiederholungen zwischen den Phasen

KOMMUNIKATION:
- Observation: Was hast du gefunden?
- Reasoning: Was ist das Problem/Lösung?
- Plan: Konkrete Schritte (kurz)
- Act: Entweder "Ich implementiere..." ODER "Rückfrage: [konkrete Frage]"

Du kommunizierst über das Ticket-System.
"""
