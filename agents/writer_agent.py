"""
agents/writer_agent.py
──────────────────────
WRITER — the third agent in the pipeline.
Responsibility: Craft personalised outreach emails from maintainer dossiers.

Key design decisions:
  - Uses a HIGHER temperature (0.7) for creative, natural-sounding prose
  - Strictly formats output as JSON so the Auditor can validate it
  - Does NOT send emails — that's gated by human approval
  - Each email must reference at least one specific, personalised detail
"""
from crewai import Agent
from langchain_groq import ChatGroq

from agents._llm import normalize_agent_llm
from config import get_settings

settings = get_settings()

EMAIL_FORMAT_INSTRUCTIONS = """
Your output MUST be valid JSON in this exact schema:
[
  {
    "to_name": "...",
    "to_email": "...",            // null if not found
    "subject": "...",
    "body": "...",                // plain text, no HTML
    "personalisation_hook": "...", // the specific detail you referenced
    "project": "...",
    "confidence": 0.0-1.0         // how confident you are this will land
  },
  ...
]
"""


def build_writer_agent() -> Agent:
    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model_name=settings.groq_model,
        temperature=0.7,   # Higher → more creative, human-sounding emails
    )
    llm = normalize_agent_llm(llm, settings.groq_model)

    return Agent(
        role="Outreach Email Writer",
        goal=(
            "Write personalised, warm, professional outreach emails to open-source maintainers. "
            "Each email MUST reference a specific detail about the maintainer's work that shows "
            "genuine interest — not a generic template. Output in the required JSON format."
        ),
        backstory=(
            "You are a developer relations writer who has built relationships with dozens of "
            "open-source communities. You know that maintainers get spammy outreach every day "
            "and can smell a template from a mile away. Your emails feel like they were written "
            "by someone who actually read their blog posts, starred their repo, and cares about "
            "their work. Short, specific, respectful of their time — that's your signature style. "
            f"\n\nOutput format instructions:\n{EMAIL_FORMAT_INSTRUCTIONS}"
        ),
        tools=[],          # Writer doesn't need tools — it uses the context passed to it
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
        memory=False,
    )
