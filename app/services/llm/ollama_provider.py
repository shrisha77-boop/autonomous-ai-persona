import ollama

from app.services.llm.base import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(self, model: str = "llama3.2:3b"):
        self.model = model

    async def generate(self, prompt: str) -> str:
        response = await ollama.AsyncClient().chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        return response["message"]["content"].strip()