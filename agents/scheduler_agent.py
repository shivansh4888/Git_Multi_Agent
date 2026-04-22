"""
agents/scheduler_agent.py
─────────────────────────
SCHEDULER — the fifth and final agent.
Responsibility: After human approves emails, schedule follow-up events.
  - Creates Google Calendar events for each approved outreach
  - Sets reminders for follow-up if no reply in N days
  - Produces a summary of everything that was scheduled

This runs AFTER the human-in-the-loop checkpoint.
"""
from crewai import Agent
from langchain_groq import ChatGroq

from agents._llm import normalize_agent_llm
from config import get_settings
from tools import CreateCalendarEventTool, ListUpcomingEventsTool

settings = get_settings()


def build_scheduler_agent() -> Agent:
    llm = ChatGroq(
        api_key=settings.groq_api_key,
        model_name=settings.groq_model,
        temperature=0.1,
    )
    llm = normalize_agent_llm(llm, settings.groq_model)

    return Agent(
        role="Follow-up Scheduler",
        goal=(
            "For each approved outreach email, create a Google Calendar follow-up reminder "
            "7 days after the send date. If the maintainer's email is known, add them as an "
            "attendee so they receive an invite. Produce a scheduling summary report."
        ),
        backstory=(
            "You are an operations specialist responsible for making sure no outreach "
            "falls through the cracks. You know that 80% of deals/collaborations come from "
            "follow-up, not the first email. You schedule thoughtful, non-spammy follow-ups "
            "with enough context for the sender to remember the conversation a week later."
        ),
        tools=[
            CreateCalendarEventTool(),
            ListUpcomingEventsTool(),
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=6,
        memory=False,
    )
