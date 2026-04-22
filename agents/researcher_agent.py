"""
agents/researcher_agent.py
──────────────────────────
RESEARCHER — the second agent in the pipeline.
Responsibility: Deep-dive into each project's maintainers.
  - Reads the Scout's output (list of repos + contributors)
  - Uses web search to find blogs, talks, Twitter, LinkedIn, interests
  - Produces a rich "maintainer dossier" for the Writer agent

Key design decision:
  - Gets BOTH GitHub data (contributors tool) AND web data (Tavily search)
  - Synthesises into a structured profile, not just raw links
"""
from crewai import Agent
from langchain_groq import ChatGroq

from agents._llm import normalize_agent_llm
from config import get_settings
from tools import GitHubContributorsTool, TavilySearchTool

settings = get_settings()


def build_researcher_agent() -> Agent:
    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model_name=settings.groq_model,
        temperature=0.2,
    )
    llm = normalize_agent_llm(llm, settings.groq_model)

    return Agent(
        role="Maintainer Researcher",
        goal=(
            "For each GitHub project provided by the Scout, build a detailed profile of the "
            "top 1-2 maintainers: their technical interests, writing style, recent work, "
            "community presence, and anything that would help craft a personalised message."
        ),
        backstory=(
            "You are a meticulous research analyst who has spent years studying the open-source "
            "community. You know that the best outreach is hyper-personalised — referencing a "
            "maintainer's specific blog post, conference talk, or technical decision. You gather "
            "intel from GitHub profiles, personal websites, Twitter/X, Hacker News, and dev.to. "
            "You produce structured dossiers that the Writer agent can act on directly."
        ),
        tools=[
            GitHubContributorsTool(),
            TavilySearchTool(),
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=12,
        memory=False,
    )
