from app.services.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """
    Development-only provider.

    This lets us test the complete autonomous pipeline
    without requiring an external LLM API.
    """

    async def generate(self, prompt: str) -> str:
        return (
            "AI development is moving quickly, but the interesting "
            "question is no longer just what a model can generate. "
            "It is how these systems are being built, deployed, "
            "and trusted in the real world.\n\n"
            "The development is worth watching because it shows "
            "how quickly the AI ecosystem is evolving—and why "
            "engineering decisions around reliability, security, "
            "and responsible deployment matter."
        )