"""
main.py
───────
CLI entry point for the Multi-Agent Research & Outreach System.

Usage:
  python main.py                          # Run with default query
  python main.py "topic:llm stars:>500"  # Custom GitHub query
  python main.py --demo                  # Demo mode (no real API calls)
  python main.py --ui                    # Launch Streamlit UI
  python main.py --api                   # Launch FastAPI server
"""
import argparse
import sys
import os
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from loguru import logger

console = Console()


def print_banner():
    console.print(
        Panel.fit(
            "[bold cyan]Multi-Agent Research & Outreach System[/bold cyan]\n"
            "[dim]Scout → Researcher → Writer → Auditor → [bold]Human Gate[/bold] → Scheduler[/dim]",
            border_style="cyan",
            padding=(1, 4),
        )
    )


def check_env() -> bool:
    """Verify required environment variables are set."""
    required = {
        "GROQ_API_KEY": "Groq LLM (free at console.groq.com)",
        "GITHUB_TOKEN": "GitHub API (free at github.com/settings/tokens)",
        "TAVILY_API_KEY": "Tavily Search (free at app.tavily.com)",
    }
    optional = {
        "LANGCHAIN_API_KEY": "LangSmith tracing (free at smith.langchain.com)",
        "GOOGLE_CLIENT_ID": "Google Calendar integration",
    }

    table = Table(title="API Key Status", box=box.ROUNDED)
    table.add_column("Service", style="bold")
    table.add_column("Status")
    table.add_column("Note", style="dim")

    all_ok = True
    for key, label in required.items():
        val = os.getenv(key, "")
        ok = bool(val and not val.startswith("your_"))
        status = "[green]✓ Set[/green]" if ok else "[red]✗ Missing[/red]"
        table.add_row(label, status, f"env: {key}")
        if not ok:
            all_ok = False

    for key, label in optional.items():
        val = os.getenv(key, "")
        ok = bool(val and not val.startswith("your_"))
        status = "[green]✓ Set[/green]" if ok else "[yellow]○ Optional[/yellow]"
        table.add_row(label, status, f"env: {key}")

    console.print(table)
    return all_ok


def run_demo_mode():
    """
    Demo mode: runs the pipeline with mock data so you can test the
    UI and approval flow without burning real API credits.
    """
    console.print("\n[bold yellow]⚡ DEMO MODE — Using mock data[/bold yellow]\n")

    import json
    from crew import human_approval_gate

    # Simulate what the pipeline would produce
    mock_audit = {
        "approved": [
            {
                "to_name": "Andrej Karpathy",
                "to_email": None,
                "subject": "Your minbpe tokenizer — a question about the BPE merge strategy",
                "body": (
                    "Hi Andrej,\n\n"
                    "I just finished working through your minbpe implementation and I was struck "
                    "by your decision to implement BPE from scratch rather than wrapping tiktoken. "
                    "The educational clarity is remarkable — I've been using it to teach a team "
                    "of ML engineers who were struggling with the conceptual gap between theory "
                    "and implementation.\n\n"
                    "I'm building a tokenizer benchmark harness and would love to include minbpe. "
                    "Would you be open to a 20-minute chat about your plans for the project?\n\n"
                    "Best,\nAlex"
                ),
                "personalisation_hook": "minbpe BPE from-scratch implementation decision",
                "project": "karpathy/minbpe",
                "confidence": 0.82,
            },
            {
                "to_name": "Harrison Chase",
                "to_email": "harrison@langchain.dev",
                "subject": "LangGraph's interrupt() pattern — building on it for human-in-the-loop",
                "body": (
                    "Hi Harrison,\n\n"
                    "Your recent blog post on LangGraph's interrupt() pattern for human-in-the-loop "
                    "workflows directly unblocked a problem I'd been stuck on for two weeks. "
                    "The idea of checkpointing graph state before a sensitive action is elegant.\n\n"
                    "I'm extending this pattern for multi-agent email outreach — pausing before any "
                    "agent sends external communications. I'd love to share what I've built and "
                    "get your thoughts on the right abstraction layer. "
                    "Would a 20-min call work for you?\n\nThanks,\nAlex"
                ),
                "personalisation_hook": "LangGraph interrupt() blog post",
                "project": "langchain-ai/langgraph",
                "confidence": 0.78,
            },
        ],
        "rejected": [
            {
                "email": {"to_name": "Unknown Dev"},
                "reasons": ["Generic subject line", "No personalisation hook used in body"],
                "fix_instructions": "Reference a specific commit or blog post in the opening line.",
            }
        ],
        "overall_quality_score": 0.80,
    }

    console.print("[dim]Simulating Scout + Researcher + Writer + Auditor output...[/dim]")
    import time
    for step in ["🔍 Scout: Found 8 repositories", "🔬 Researcher: Built 5 maintainer dossiers",
                 "✍️  Writer: Drafted 3 personalised emails", "🛡️  Auditor: 2 approved, 1 rejected"]:
        time.sleep(0.4)
        console.print(f"  {step}")

    # Run through the human gate
    approved = human_approval_gate(json.dumps(mock_audit))

    console.print(f"\n[bold green]Demo complete. {len(approved)} email(s) approved.[/bold green]")
    console.print("\n[dim]In a real run, the Scheduler would now create Google Calendar follow-ups.[/dim]")


def main():
    print_banner()

    parser = argparse.ArgumentParser(
        description="Multi-Agent Research & Outreach System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py
  python main.py "topic:llm stars:>300 pushed:>2024-06-01"
  python main.py --demo
  python main.py --ui
  python main.py --api --port 8001
        """,
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="GitHub search query (default: topic:machine-learning stars:>200 pushed:>2024-01-01)",
    )
    parser.add_argument("--demo", action="store_true", help="Run in demo mode (no real API calls)")
    parser.add_argument("--ui", action="store_true", help="Launch Streamlit UI")
    parser.add_argument("--api", action="store_true", help="Launch FastAPI server")
    parser.add_argument("--port", type=int, default=8000, help="Port for FastAPI server")
    parser.add_argument("--check", action="store_true", help="Check API key configuration")
    args = parser.parse_args()

    # Load .env
    from dotenv import load_dotenv
    load_dotenv()

    if args.check:
        check_env()
        return

    if args.ui:
        console.print("[cyan]Launching Streamlit UI...[/cyan]")
        os.execv(
            sys.executable,
            [sys.executable, "-m", "streamlit", "run", "ui/app.py"],
        )
        return

    if args.api:
        console.print(f"[cyan]Launching FastAPI server on port {args.port}...[/cyan]")
        import uvicorn
        uvicorn.run("ui.api:app", host="0.0.0.0", port=args.port, reload=True)
        return

    if args.demo:
        run_demo_mode()
        return

    # Real pipeline run — check env first
    console.print()
    env_ok = check_env()
    console.print()

    if not env_ok:
        console.print(
            "[bold red]❌  Missing required API keys. "
            "Copy .env.example to .env and fill in your keys.[/bold red]\n"
            "Run [cyan]python main.py --demo[/cyan] to test without real keys."
        )
        sys.exit(1)

    # Configure loguru
    from config import get_settings
    settings = get_settings()
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)
    logger.add("logs/run_{time}.log", rotation="10 MB", retention="7 days")

    console.print("[bold]Starting pipeline...[/bold] (this takes 2-5 minutes)\n")

    from crew import run_pipeline
    results = run_pipeline(args.query)

    # Summary
    table = Table(title="Pipeline Results", box=box.ROUNDED)
    table.add_column("Stage", style="bold")
    table.add_column("Status")
    table.add_column("Details")

    approved = results.get("approved_emails", [])
    table.add_row("Scout", "[green]✓[/green]", "GitHub repos discovered")
    table.add_row("Researcher", "[green]✓[/green]", "Maintainer dossiers built")
    table.add_row("Writer", "[green]✓[/green]", "Email drafts created")
    table.add_row("Auditor", "[green]✓[/green]", "QA review complete")
    table.add_row("Human Gate", "[green]✓[/green]", f"{len(approved)} email(s) approved")
    table.add_row(
        "Scheduler",
        "[green]✓[/green]" if results.get("schedule_output") else "[yellow]○[/yellow]",
        "Calendar events created" if results.get("schedule_output") else "Skipped (no approvals)",
    )

    console.print(table)
    console.print(f"\n[bold green]✅  Run complete![/bold green]")
    console.print("[dim]Full output saved to logs/ directory.[/dim]")


if __name__ == "__main__":
    main()
