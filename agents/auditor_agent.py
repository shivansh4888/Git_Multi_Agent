"""
agents/auditor_agent.py
───────────────────────
AUDITOR — the fourth agent, the reliability layer.
Responsibility: QA-check every email draft before it reaches the human.
  - Validates JSON structure
  - Checks for generic/templated language
  - Flags missing personalisation
  - Scores email quality and either approves or sends back for revision

This agent is a core interview talking point:
  "I added an Auditor specifically to handle the reliability challenges of
   autonomous agents — if Writer produces a bad email, Auditor catches it
   before it ever reaches a human or gets sent."
"""
from crewai import Agent
from langchain_groq import ChatGroq

from agents._llm import normalize_agent_llm
from config import get_settings

settings = get_settings()

AUDIT_CRITERIA = """
For each email draft, check ALL of the following:
1. JSON is valid and has all required fields
2. Subject line is specific, not generic ("Quick question" is FAIL)
3. Body references at least ONE specific detail about the maintainer
4. Body is between 80-250 words (too short = lazy, too long = ignored)
5. No spam trigger words (e.g. "synergy", "circle back", "per my last email")
6. Tone is warm and peer-to-peer, not salesy
7. Clear, single call-to-action at the end
8. confidence score is justified

Output a JSON audit report:
{
  "approved": [...emails that passed],
  "rejected": [
    {"email": {...}, "reasons": ["...", "..."], "fix_instructions": "..."}
  ],
  "overall_quality_score": 0.0-1.0
}
"""


def build_auditor_agent() -> Agent:
    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model_name=settings.groq_model,
        temperature=0.0,   # Zero temp → strict, consistent evaluation
    )
    llm = normalize_agent_llm(llm, settings.groq_model)

    return Agent(
        role="Quality Auditor",
        goal=(
            "Review every outreach email draft and approve only those that meet quality "
            "standards. Flag generic templates, missing personalisation, or structural issues. "
            "Return a structured audit report — never let a bad email through."
        ),
        backstory=(
            "You are a senior quality assurance engineer who has reviewed thousands of "
            "outreach campaigns. You are immune to persuasion — you evaluate emails purely "
            "on merit against a strict rubric. Your job is to be the last defence before "
            "a human sees these drafts. You would rather reject 10 good emails than let "
            "1 bad one through, because one bad email can damage a relationship permanently. "
            f"\n\nAudit criteria:\n{AUDIT_CRITERIA}"
        ),
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=4,
        memory=False,
    )
