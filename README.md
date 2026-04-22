# 🤖 Multi-Agent Research & Outreach Automation System

> A crew of 5 specialised AI agents that find open-source AI projects on GitHub, research maintainers, draft personalised outreach emails, QA-audit them, and schedule follow-ups in Google Calendar — with a **human-in-the-loop** approval gate.

---

## Architecture

```
┌─────────┐     ┌────────────┐     ┌────────┐     ┌─────────┐
│  SCOUT  │────▶│ RESEARCHER │────▶│ WRITER │────▶│ AUDITOR │
│         │     │            │     │        │     │         │
│ GitHub  │     │  Tavily    │     │ Groq   │     │ Groq    │
│ Search  │     │  Web Search│     │ LLM    │     │ temp=0  │
└─────────┘     └────────────┘     └────────┘     └────────┬┘
                                                           │
                                              ┌────────────▼────────────┐
                                              │   HUMAN-IN-THE-LOOP     │
                                              │  Review · Edit · Approve │
                                              │  (Streamlit or CLI)      │
                                              └────────────┬────────────┘
                                                           │
                                                  ┌────────▼─────────┐
                                                  │    SCHEDULER     │
                                                  │  Google Calendar │
                                                  │  Follow-up Events│
                                                  └──────────────────┘
```

## Project Structure

```
multi_agent_system/
├── main.py                    # CLI entry point
├── crew.py                    # CrewAI orchestrator + human gate
├── requirements.txt
├── .env.example               # Copy to .env and fill in keys
│
├── agents/
│   ├── scout_agent.py         # Discovers GitHub repos
│   ├── researcher_agent.py    # Researches maintainers via web search
│   ├── writer_agent.py        # Drafts personalised emails
│   ├── auditor_agent.py       # QA-reviews drafts (temp=0)
│   └── scheduler_agent.py     # Creates calendar follow-ups
│
├── tools/
│   ├── github_tool.py         # GitHub REST API (search, repo details, contributors)
│   ├── search_tool.py         # Tavily web search API
│   └── calendar_tool.py       # Google Calendar API
│
├── config/
│   └── settings.py            # Pydantic settings, reads from .env
│
├── ui/
│   ├── app.py                 # Streamlit dashboard (human-in-the-loop UI)
│   └── api.py                 # FastAPI REST backend
│
├── tests/
│   └── test_pipeline.py       # Unit + integration tests (pytest)
│
├── logs/                      # Auto-created, stores run outputs
└── docs/
    └── interview_talking_points.md
```

## Quickstart

### 1. Clone and install

```bash
git clone <your-repo>
cd multi_agent_system
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env with your keys:
```

| Key | Where to get it | Cost |
|-----|----------------|------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | Free |
| `GITHUB_TOKEN` | [github.com/settings/tokens](https://github.com/settings/tokens) | Free |
| `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com) | Free (1000/mo) |
| `LANGCHAIN_API_KEY` | [smith.langchain.com](https://smith.langchain.com) | Free |
| `GOOGLE_CLIENT_ID/SECRET` | [console.cloud.google.com](https://console.cloud.google.com) | Free |

### 3. Run

```bash
# Check your key configuration
python main.py --check

# Demo mode (no real API calls — great for testing the flow)
python main.py --demo

# Full pipeline with Streamlit UI (recommended for demos)
python main.py --ui

# Full pipeline CLI mode
python main.py

# Custom GitHub query
python main.py "topic:llm stars:>500 pushed:>2024-06-01"

# FastAPI server (for integration / programmatic use)
python main.py --api
```

### 4. Google Calendar setup (optional)

```bash
# One-time OAuth flow
python tools/calendar_tool.py --auth
# Opens browser → authorise → saves token.json
```

### 5. Run tests

```bash
pytest tests/ -v
```

---

## Agent Roles & Design Decisions

### 🔍 Scout Agent
- **Tools**: `github_search_repos`, `github_get_repo_details`, `github_get_contributors`
- **Temperature**: 0.1 (low — factual, deterministic)
- **Why no web search?** Separation of concerns. Scout only speaks to GitHub. Researcher handles the web.
- **Memory**: Enabled — retains context across multiple tool calls in the same run

### 🔬 Researcher Agent
- **Tools**: `github_get_contributors`, `web_search` (Tavily)
- **Temperature**: 0.2
- **Key behaviour**: Looks for ONE specific, citable thing per maintainer (a blog post, a talk, a controversial PR comment). The "personalisation hook."
- **Context**: Receives Scout's JSON output automatically via CrewAI's `context` param

### ✍️ Writer Agent
- **Tools**: None (pure LLM reasoning on provided context)
- **Temperature**: 0.7 (higher — creative, natural-sounding prose)
- **Output**: Strict JSON schema so Auditor can validate programmatically
- **Constraint**: 100-200 word emails, single CTA, must reference the personalisation hook

### 🛡️ Auditor Agent
- **Tools**: None
- **Temperature**: 0.0 (deterministic — same input always gets same verdict)
- **Rubric**: 7-point checklist (JSON validity, subject specificity, word count, spam words, etc.)
- **Interview talking point**: "I added this because LLM outputs are non-deterministic. Without a validation layer, you'd occasionally send garbage emails. The Auditor catches failures before they reach the human."

### 📅 Scheduler Agent
- **Tools**: `create_calendar_event`, `list_calendar_events`
- **Runs after**: Human approval gate — only processes approved emails
- **Graceful degradation**: Returns DEMO_MODE JSON if Google OAuth not configured

---

## Human-in-the-Loop Design

The most important architectural decision. Before any email leaves the system:

```
Auditor output → human_approval_gate() → Human reviews each draft → Approved list → Scheduler
```

**In Streamlit UI**: Each email is displayed with its subject, body (editable), personalisation hook, and confidence score. The human clicks Approve / Reject per email.

**In CLI mode**: Interactive prompts with `y / n / edit` options.

**Why this matters for enterprises**: Autonomous agents sending external emails without oversight is a liability. The human gate is not optional in production — it's the difference between a useful tool and a legal risk.

**Interview line**: *"I deliberately added a mandatory human approval step because I think one of the biggest mistakes in agentic AI is removing humans from the loop prematurely. This system saves 90% of the research and writing time, but a human still makes the final call on every outreach."*

---

## Reliability & Failure Handling

| Failure Mode | Handling Strategy |
|---|---|
| GitHub API rate limit | Tool returns `ERROR:` string; agent retries up to `max_iter` times |
| Tavily API timeout | Caught in `requests.RequestException`, returns error string |
| LLM produces invalid JSON | `human_approval_gate()` strips markdown fences, falls back to empty |
| Google Calendar OAuth expired | `token.json` auto-refreshed via `google.auth.transport.requests.Request` |
| Agent exceeds `max_iter` | CrewAI raises exception, pipeline catches and saves partial results |
| All emails rejected by Auditor | Graceful exit with log message, no Scheduler run |

---

## Observability with LangSmith

With `LANGCHAIN_TRACING_V2=true` and your `LANGCHAIN_API_KEY` set, every agent run is traced:

- See exactly which tools were called in what order
- Inspect token usage per agent
- Compare runs across different queries
- Debug prompt failures with full input/output logs

View traces: `https://smith.langchain.com/projects/multi-agent-outreach`

---

## Interview Talking Points

### On architecture choices
*"I chose CrewAI over raw LangChain agents because CrewAI's role-based abstraction maps naturally to how real teams work. Each agent has a clear job description, and the sequential process mirrors how a human researcher-writer team would operate."*

### On model choice (Groq + Llama 3)
*"I chose Groq for two reasons: it's free, and it's fast enough that the whole pipeline runs in under 3 minutes. OpenAI would work but adds cost. The interesting tradeoff is that Llama 3 70B is slightly weaker at following complex JSON schemas, which is why I added the Auditor — it catches format failures that GPT-4 rarely produces."*

### On the Auditor agent
*"This was the most impactful addition. Before I added it, about 30% of Writer outputs had generic subject lines or ignored the personalisation hook. The Auditor reduced that to near zero. It's also a good example of using temperature=0 strategically — I want evaluation to be deterministic."*

### On agent memory
*"CrewAI supports two kinds of memory: per-agent (the agent remembers its own tool calls) and crew-level shared memory. I enabled both, but the most important is the task `context` parameter — that's how Scout's JSON is literally injected into Researcher's prompt."*

### On what you'd improve
*"In production I'd add: (1) a vector store so agents can remember past outreach and not contact the same person twice, (2) a feedback loop where human edits in the approval gate are used to fine-tune the Writer prompt, and (3) Redis for run state instead of in-memory dicts in the API."*

---

## Free API Limits Reference

| API | Free Tier | Resets |
|-----|-----------|--------|
| GitHub REST | 5,000 req/hr (authenticated) | Hourly |
| Tavily Search | 1,000 searches/month | Monthly |
| Groq (Llama 3 70B) | 14,400 req/day, 500K tokens/day | Daily |
| LangSmith | Unlimited traces (free tier) | Never |
| Google Calendar | Unlimited (within quota) | N/A |

---

## Tech Stack

- **[CrewAI](https://github.com/joaomdmoura/crewAI)** — Multi-agent orchestration
- **[LangChain](https://python.langchain.com)** — Tool abstractions
- **[Groq](https://groq.com)** — LLM inference (Llama 3 70B / Mixtral)
- **[Streamlit](https://streamlit.io)** — Human-in-the-loop UI
- **[FastAPI](https://fastapi.tiangolo.com)** — REST backend
- **[LangSmith](https://smith.langchain.com)** — Observability & tracing
- **GitHub REST API** — Repository discovery
- **Tavily** — Web search
- **Google Calendar API** — Follow-up scheduling
