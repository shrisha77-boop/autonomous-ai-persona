import ollama

from app.core.config import settings
from app.services.llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(
        self,
        model: str | None = None,
        host: str | None = None,
    ):
        self.model = model or settings.OLLAMA_MODEL
        self.host = host or settings.OLLAMA_HOST

    async def generate(self, prompt: str) -> str:
        client = ollama.AsyncClient(host=self.host)
        response = await client.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response["message"]["content"].strip()