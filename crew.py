"""
crew.py
───────
The central orchestrator. Defines all Tasks and wires the 5-agent Crew together.

Architecture:
  Scout ──► Researcher ──► Writer ──► Auditor ──[HUMAN GATE]──► Scheduler

CrewAI passes each task's output as context to the next task automatically.
We use sequential process here — easy to reason about, great for demos.
Switch to Process.hierarchical for a "manager LLM" pattern if needed.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

from crewai import Crew, Task, Process
from loguru import logger

from agents import (
    build_scout_agent,
    build_researcher_agent,
    build_writer_agent,
    build_auditor_agent,
    build_scheduler_agent,
)
from config import get_settings

settings = get_settings()


# ── Task definitions ──────────────────────────────────────────────────────────

def build_tasks(
    agents: dict,
    search_query: str = "topic:machine-learning stars:>200 pushed:>2024-01-01",
    max_projects: Optional[int] = None,
) -> list[Task]:
    """
    Build all tasks with explicit context passing.
    Each task's output feeds directly into the next via `context` param.
    """

    max_projects_to_scout = max_projects or settings.max_projects_to_scout

    task_scout = Task(
        description=(
            f"Search GitHub for promising open-source AI/ML projects using this query: "
            f"'{search_query}'. "
            f"For each of the top {max_projects_to_scout} results:\n"
            "  1. Fetch detailed repo info (stars, topics, README excerpt)\n"
            "  2. Get the top 2 contributors with their public profile data\n"
            "  3. Assess the project's momentum and community health\n\n"
            "Output a structured JSON list of candidate projects with their contributors."
        ),
        expected_output=(
            "A JSON array of up to 10 objects. Each object contains: "
            "full_name, description, stars, topics, url, momentum_score (0-10), "
            "and a 'contributors' list with login, name, email, bio, twitter, blog."
        ),
        agent=agents["scout"],
    )

    task_research = Task(
        description=(
            "You have received a list of GitHub projects and their maintainers from the Scout. "
            "For each project, research the TOP maintainer deeply:\n"
            "  1. Search the web for their blog posts, conference talks, dev.to articles\n"
            "  2. Find their Twitter/X, LinkedIn, or personal website activity\n"
            "  3. Note their stated technical interests and opinions\n"
            "  4. Find ONE recent, specific thing they did that's worth referencing in an email\n\n"
            "Focus on depth over breadth — pick the 5 strongest maintainer profiles."
        ),
        expected_output=(
            "A JSON array of maintainer dossiers. Each contains: "
            "name, github_login, email, project, personalisation_hook "
            "(the ONE specific thing to reference), interests, web_presence."
        ),
        agent=agents["researcher"],
        context=[task_scout],   # Receives Scout's output as context
    )

    task_write = Task(
        description=(
            "Using the maintainer dossiers from the Researcher, write a personalised "
            "outreach email for each maintainer. Requirements:\n"
            "  - Subject line must be specific (mention their project or a detail)\n"
            "  - First sentence must reference their personalisation_hook\n"
            "  - Body: 100-200 words, warm and peer-to-peer tone\n"
            "  - Clear single CTA at the end (e.g. 'Would you be open to a 20-min chat?')\n"
            "  - Include a confidence score (0-1) for how likely this email will get a reply\n\n"
            "Output ONLY the JSON array, no preamble."
        ),
        expected_output=(
            "A JSON array of email drafts. Each object: "
            "to_name, to_email, subject, body, personalisation_hook, project, confidence."
        ),
        agent=agents["writer"],
        context=[task_research],
    )

    task_audit = Task(
        description=(
            "Audit ALL email drafts from the Writer. For each email:\n"
            "  1. Validate JSON structure\n"
            "  2. Check subject is specific (not generic)\n"
            "  3. Verify personalisation_hook is actually used in the body\n"
            "  4. Confirm word count is 80-250 words\n"
            "  5. Check for spam language\n"
            "  6. Validate the confidence score is reasonable\n\n"
            "Reject any email that fails 2 or more checks. "
            "For rejected emails, provide clear fix_instructions. "
            "Output the structured audit report JSON."
        ),
        expected_output=(
            "A JSON audit report with: approved (list of passing emails), "
            "rejected (list with reasons + fix_instructions), overall_quality_score."
        ),
        agent=agents["audit"],
        context=[task_write],
    )

    task_schedule = Task(
        description=(
            "The human has approved a set of emails (you'll receive the approved list). "
            "For each approved email:\n"
            "  1. Create a Google Calendar event titled 'Follow-up: [maintainer name] re [project]'\n"
            "  2. Set it 7 days from today\n"
            "  3. Description should include the original email subject and a reminder of context\n"
            "  4. Add attendee if email is known\n\n"
            "After scheduling, output a summary of all events created."
        ),
        expected_output=(
            "A scheduling summary: list of events created with title, date, "
            "attendee, and calendar_link (or DEMO_MODE status if OAuth not configured)."
        ),
        agent=agents["scheduler"],
        context=[task_audit],
    )

    return [task_scout, task_research, task_write, task_audit, task_schedule]


# ── Crew builder ──────────────────────────────────────────────────────────────

def build_crew(
    search_query: Optional[str] = None,
    max_projects: Optional[int] = None,
) -> tuple[Crew, list[Task]]:
    """
    Instantiate all agents, build tasks, and assemble the Crew.
    Returns both the Crew and the tasks list (for result inspection).
    """
    agents = {
        "scout": build_scout_agent(),
        "researcher": build_researcher_agent(),
        "writer": build_writer_agent(),
        "audit": build_auditor_agent(),
        "scheduler": build_scheduler_agent(),
    }

    query = search_query or "topic:machine-learning stars:>200 pushed:>2024-01-01"
    tasks = build_tasks(agents, search_query=query, max_projects=max_projects)

    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
        memory=False,
    )

    return crew, tasks


# ── Human-in-the-loop gate ────────────────────────────────────────────────────

def human_approval_gate(audit_result_raw: str) -> list[dict]:
    """
    Parse the Auditor's output and present approved emails to the human.
    In CLI mode: interactive prompt. In Streamlit: handled by ui/app.py.

    Returns the list of human-approved emails.
    """
    try:
        # Strip potential markdown fences
        clean = audit_result_raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        audit = json.loads(clean)
    except json.JSONDecodeError:
        logger.warning("Auditor output was not valid JSON — attempting partial parse")
        audit = {"approved": [], "rejected": []}

    approved = audit.get("approved", [])
    rejected = audit.get("rejected", [])

    logger.info(f"Audit complete: {len(approved)} approved, {len(rejected)} rejected")

    if not settings.human_approval_required:
        logger.info("HUMAN_APPROVAL_REQUIRED=false → auto-approving all emails")
        return approved

    if not sys.stdin.isatty():
        logger.info("Non-interactive terminal detected → auto-approving all emails")
        return approved

    # CLI approval flow
    print("\n" + "═" * 60)
    print("  🧑  HUMAN-IN-THE-LOOP CHECKPOINT")
    print("═" * 60)

    if not approved:
        print("  No emails passed the Auditor. Exiting.")
        return []

    final_approved = []
    for i, email in enumerate(approved, 1):
        print(f"\n[{i}/{len(approved)}] To: {email.get('to_name')} | Project: {email.get('project')}")
        print(f"  Subject : {email.get('subject')}")
        print(f"  Hook    : {email.get('personalisation_hook')}")
        print(f"  Confidence: {email.get('confidence', 'N/A')}")
        print("\n  --- EMAIL BODY ---")
        print(email.get("body", ""))
        print("  --- END ---\n")

        try:
            choice = input("  Approve this email? [y/n/edit] → ").strip().lower()
        except EOFError:
            logger.info("Input stream closed during approval → auto-approving remaining emails")
            final_approved.extend(approved[i - 1 :])
            break
        if choice == "y":
            final_approved.append(email)
            print("  ✅  Approved")
        elif choice == "edit":
            print("  Paste edited body (end with a line containing only 'END'):")
            lines = []
            while True:
                line = input()
                if line == "END":
                    break
                lines.append(line)
            email["body"] = "\n".join(lines)
            final_approved.append(email)
            print("  ✅  Approved with edits")
        else:
            print("  ❌  Rejected")

    print(f"\n✅  {len(final_approved)} / {len(approved)} emails approved by human")
    return final_approved


# ── Main run function ─────────────────────────────────────────────────────────

def run_pipeline(search_query: Optional[str] = None) -> dict:
    """
    Run the full pipeline end-to-end.
    Returns a results dict with outputs from each stage.
    """
    logger.info("🚀  Starting Multi-Agent Research & Outreach Pipeline")

    crew, tasks = build_crew(search_query)

    # Phase 1–4: Scout → Researcher → Writer → Auditor
    logger.info("🤖  Kicking off CrewAI crew (Phases 1–4)...")
    raw_result = crew.kickoff()

    # The final task output is the Auditor's report
    audit_output = tasks[3].output.raw_output if hasattr(tasks[3], "output") else str(raw_result)

    # Phase: Human gate
    approved_emails = human_approval_gate(audit_output)

    results = {
        "scout_output": tasks[0].output.raw_output if hasattr(tasks[0], "output") else "",
        "research_output": tasks[1].output.raw_output if hasattr(tasks[1], "output") else "",
        "draft_emails": tasks[2].output.raw_output if hasattr(tasks[2], "output") else "",
        "audit_report": audit_output,
        "approved_emails": approved_emails,
        "schedule_output": "",
    }

    if approved_emails and len(approved_emails) > 0:
        # Phase 5: Scheduler (only runs if human approved ≥1 email)
        logger.info("📅  Running Scheduler agent for approved emails...")
        scheduler = build_scheduler_agent()
        schedule_task = Task(
            description=(
                f"Schedule follow-up calendar events for these approved emails:\n"
                f"{json.dumps(approved_emails, indent=2)}\n\n"
                "Create a Google Calendar event for each, 7 days from today."
            ),
            expected_output="A scheduling summary listing all events created.",
            agent=scheduler,
        )
        schedule_crew = Crew(
            agents=[scheduler],
            tasks=[schedule_task],
            process=Process.sequential,
            verbose=True,
        )
        schedule_result = schedule_crew.kickoff()
        results["schedule_output"] = str(schedule_result)
        logger.info("📅  Scheduling complete")
    else:
        logger.info("No approved emails — skipping scheduler")

    # Save results to logs/
    Path("logs").mkdir(exist_ok=True)
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(f"logs/run_{timestamp}.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"💾  Full results saved to {out_path}")

    return results


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else None
    results = run_pipeline(query)
    print(f"\n🎉  Pipeline complete. Approved emails: {len(results['approved_emails'])}")
