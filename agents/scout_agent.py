"""
agents/scout_agent.py
─────────────────────
SCOUT — the first agent in the pipeline.
Responsibility: Search GitHub for promising open-source AI projects.
Passes a structured list of candidate repos to the Researcher agent.

Key design decisions:
  - Uses GitHubSearchTool + GitHubRepoDetailsTool
  - Does NOT do web search (that's Researcher's job)
  - Passes raw JSON to the next agent via shared CrewAI context
"""
from crewai import Agent
from langchain_groq import ChatGroq

from agents._llm import normalize_agent_llm
from config import get_settings
from tools import GitHubSearchTool, GitHubRepoDetailsTool, GitHubContributorsTool

settings = get_settings()


def build_scout_agent() -> Agent:
    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model_name=settings.groq_model,
        temperature=0.1,   # Low temp → deterministic, factual scouting
    )
    llm = normalize_agent_llm(llm, settings.groq_model)

    return Agent(
        role="GitHub Scout",
        goal=(
            "Discover the most promising recently-active open-source AI/ML projects on GitHub "
            "that have momentum (rising stars, recent commits) and active maintainers. "
            f"Find up to {settings.max_projects_to_scout} strong candidates."
        ),
        backstory=(
            "You are a senior open-source intelligence analyst. You have deep expertise in "
            "reading GitHub signals: star velocity, commit frequency, issue responsiveness, "
            "and community health. You cut through noise to find projects that are genuinely "
            "gaining traction in the AI ecosystem — not just hyped ones."
        ),
        tools=[
            GitHubSearchTool(),
            GitHubRepoDetailsTool(),
            GitHubContributorsTool(),
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=8,        # Cap iterations to avoid runaway API calls
        memory=False,
    )
