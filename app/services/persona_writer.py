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

Your task is to write a concise social-media post about the
technology development provided below.

SOURCE INFORMATION
------------------
Title:
{topic.title}

Summary:
{topic.summary}

Source:
{topic.source_url}

STRICT GROUNDING RULES
----------------------

1. Use ONLY facts explicitly stated in the title and summary above.

2. Do not add technical details, features, capabilities, benchmarks,
   statistics, motivations, or consequences that are not explicitly stated.

3. Do not make predictions about what the technology may cause or enable.

4. Do not infer security risks, benefits, vulnerabilities, or implications
   unless they are explicitly stated in the source information.

5. You may explain why the stated information is relevant to the persona,
   but do not introduce new factual claims.

6. If the source information is limited, keep the post simple and general.

7. Do not claim personal experience or personal testing.

8. Do not fabricate quotations or statistics.

9. Do not fabricate facts about the source.

10. Do not imply that you personally verified the information.

11. If there is not enough information for meaningful analysis, simply
    summarize the development and state that it is worth watching.

The source information is authoritative. When in doubt, omit the claim.

STYLE
-----

Write in the voice of a knowledgeable technology analyst.

Be engaging but factual. You may discuss the relevance of the
development to {persona_domain}, but do not invent implications
that are not supported by the source information.

Keep the post concise and suitable for a social-media feed.

Return ONLY the post text.
Do not include headings, analysis, reasoning, or quotation marks.
"""

        return await self.llm.generate(prompt)