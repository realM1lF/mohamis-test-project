"""Embedding provider for text vectorization."""

import os
from typing import List
import httpx


class EmbeddingProvider:
    """Provider for text embeddings using OpenRouter/OpenAI API."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPEN_ROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPEN_ROUTER_API_KEY required")
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "openai/text-embedding-3-small"  # Good balance of quality/price
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        response = await self._embed_batch([text])
        return response[0]
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        return await self._embed_batch(texts)
    
    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Call OpenRouter API for embeddings."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/realM1lF/personal-ki-agents",
        }
        
        payload = {
            "model": self.model,
            "input": texts
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=payload,
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Embedding API error: {response.status_code} - {response.text}")
            
            data = response.json()
            # Sort by index to maintain order
            embeddings = sorted(data["data"], key=lambda x: x["index"])
            return [item["embedding"] for item in embeddings]
