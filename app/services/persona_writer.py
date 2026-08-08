from app.models.topic import TopicCandidate
from app.services.llm.base import LLMProvider


class PersonaWriter:

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def generate_post(
        self,
        topic: TopicCandidate,
        persona_name: str,
        persona_domain: str,
    ) -> str:

        prompt = f"""
You are {persona_name}, an autonomous technology persona
specializing in {persona_domain}.

Write a concise social-media-style post about this topic:

Title:
{topic.title}

Summary:
{topic.summary}

Source:
{topic.source_url}

Maintain a consistent expert voice.

Do not invent facts.
Do not claim personal experiences you do not have.
Focus on why the development matters to the technology ecosystem.

Return only the post text.
"""

        return await self.llm.generate(prompt)