"""
ui/app.py
─────────
Streamlit dashboard — the human-in-the-loop interface.
Run with: streamlit run ui/app.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import streamlit as st

# Allow imports from parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_settings

settings = get_settings()

st.set_page_config(
    page_title="Outreach Atelier",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Cormorant+Garamond:wght@600;700&display=swap');

    :root {
        --paper: #f7f4ee;
        --card: rgba(255, 255, 255, 0.84);
        --card-strong: #fffdf9;
        --ink: #1f2937;
        --muted: #6b7280;
        --line: rgba(120, 113, 108, 0.18);
        --accent: #8c6a43;
        --accent-deep: #5f4630;
        --accent-soft: #e9dfd2;
        --good: #2f6f4f;
        --warn: #b7791f;
        --bad: #b2453d;
        --shadow: 0 16px 40px rgba(72, 52, 36, 0.08);
        --radius: 22px;
    }

    html, body, [class*="css"] {
        font-family: 'Manrope', sans-serif;
        color: var(--ink);
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at top left, rgba(201, 172, 139, 0.18), transparent 26%),
            linear-gradient(180deg, #faf7f2 0%, #f4efe7 100%);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f2ece4 0%, #eee6dc 100%);
        border-right: 1px solid var(--line);
    }

    [data-testid="stHeader"] {
        background: rgba(247, 244, 238, 0.72);
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1220px;
    }

    h1, h2, h3 {
        letter-spacing: -0.03em;
        color: #1a1d21;
    }

    .eyebrow {
        text-transform: uppercase;
        letter-spacing: 0.18em;
        font-size: 0.74rem;
        font-weight: 800;
        color: var(--accent);
        margin-bottom: 0.8rem;
    }

    .hero-shell {
        background: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(249,244,236,0.96));
        border: 1px solid rgba(140, 106, 67, 0.16);
        border-radius: 28px;
        padding: 2.4rem 2.2rem 2rem;
        box-shadow: var(--shadow);
        position: relative;
        overflow: hidden;
        margin-bottom: 1.25rem;
    }

    .hero-shell:before {
        content: "";
        position: absolute;
        right: -80px;
        top: -70px;
        width: 220px;
        height: 220px;
        border-radius: 999px;
        background: radial-gradient(circle, rgba(140, 106, 67, 0.17), transparent 62%);
    }

    .hero-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 4rem;
        line-height: 0.92;
        margin: 0 0 0.8rem 0;
        color: #241c16;
    }

    .hero-copy {
        max-width: 780px;
        font-size: 1.04rem;
        line-height: 1.7;
        color: #4b5563;
    }

    .kpi-strip {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.9rem;
        margin-top: 1.4rem;
    }

    .kpi-card, .section-card, .timeline-card {
        background: var(--card);
        backdrop-filter: blur(16px);
        border: 1px solid var(--line);
        border-radius: var(--radius);
        box-shadow: var(--shadow);
    }

    .kpi-card {
        padding: 1rem 1.05rem;
    }

    .kpi-label {
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--muted);
        margin-bottom: 0.55rem;
    }

    .kpi-value {
        font-size: 1.6rem;
        font-weight: 800;
        color: #1f2937;
    }

    .section-card {
        padding: 1.15rem 1.15rem 1rem;
        margin-bottom: 1rem;
    }

    .section-title {
        font-size: 1.15rem;
        font-weight: 800;
        margin-bottom: 0.35rem;
        color: #231f1b;
    }

    .section-copy {
        color: var(--muted);
        line-height: 1.6;
        font-size: 0.95rem;
    }

    .pipeline-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 0.8rem;
        margin: 0.6rem 0 1.1rem;
    }

    .stage-chip {
        background: rgba(255,255,255,0.7);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 0.95rem 0.9rem;
        text-align: center;
    }

    .stage-icon {
        display: block;
        font-size: 1.3rem;
        margin-bottom: 0.25rem;
    }

    .stage-label {
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: #5f4630;
        font-weight: 800;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        border-radius: 999px;
        padding: 0.45rem 0.8rem;
        background: rgba(140, 106, 67, 0.08);
        border: 1px solid rgba(140, 106, 67, 0.18);
        color: #5f4630;
        font-weight: 700;
        font-size: 0.86rem;
    }

    .sidebar-heading {
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        color: #7c6854;
        margin-bottom: 0.6rem;
        font-weight: 800;
    }

    .sidebar-brand {
        background: rgba(255,255,255,0.62);
        border: 1px solid var(--line);
        border-radius: 22px;
        padding: 1rem 1rem 0.95rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow);
    }

    .brand-title {
        font-family: 'Cormorant Garamond', serif;
        font-size: 2rem;
        margin: 0;
        color: #271f18;
    }

    .brand-copy {
        margin-top: 0.35rem;
        color: #6b6258;
        font-size: 0.93rem;
        line-height: 1.55;
    }

    .api-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.65rem 0;
        border-bottom: 1px solid rgba(120, 113, 108, 0.12);
    }

    .api-row:last-child {
        border-bottom: 0;
    }

    .api-dot {
        width: 0.72rem;
        height: 0.72rem;
        border-radius: 999px;
        display: inline-block;
        margin-right: 0.55rem;
    }

    .dot-ok { background: #6b8f63; }
    .dot-missing { background: #d7b08d; }

    .email-shell {
        background: rgba(255,255,255,0.9);
        border: 1px solid var(--line);
        border-radius: 24px;
        padding: 1rem 1rem 0.6rem;
        box-shadow: var(--shadow);
    }

    .code-shell {
        background: #fbfaf8;
        border: 1px solid rgba(120, 113, 108, 0.14);
        border-radius: 22px;
        padding: 0.4rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.8);
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 1rem 1rem 0.85rem;
        box-shadow: var(--shadow);
    }

    div[data-testid="stExpander"] {
        border: 1px solid var(--line);
        border-radius: 22px;
        background: rgba(255,255,255,0.82);
        box-shadow: var(--shadow);
    }

    div[data-testid="stTextArea"] textarea,
    div[data-baseweb="select"] > div,
    div[data-testid="stTextInput"] input {
        background: rgba(255,255,255,0.9);
    }

    div.stButton > button {
        border-radius: 16px;
        min-height: 3rem;
        font-weight: 800;
        letter-spacing: 0.01em;
        border: 1px solid rgba(95, 70, 48, 0.18);
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #8c6a43, #6a4c31);
        color: white;
        border: none;
        box-shadow: 0 14px 30px rgba(106, 76, 49, 0.22);
    }

    .muted-note {
        color: var(--muted);
        font-size: 0.93rem;
        line-height: 1.65;
    }

    @media (max-width: 980px) {
        .hero-title { font-size: 2.9rem; }
        .kpi-strip, .pipeline-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

defaults = {
    "pipeline_running": False,
    "pipeline_complete": False,
    "approved_emails": [],
    "audit_report": None,
    "results": None,
    "schedule_done": False,
    "schedule_result": "",
    "email_decisions": {},
    "email_edits": {},
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def api_ok(attr: str) -> bool:
    value = getattr(settings, attr, "")
    return bool(value and not value.startswith("your_"))


with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-heading">Workspace</div>
            <div class="brand-title">Outreach Atelier</div>
            <div class="brand-copy">
                A refined command center for research-led outreach, approvals, and follow-up planning.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-heading">Search Brief</div>', unsafe_allow_html=True)
    search_query = st.text_area(
        "GitHub Search Query",
        value="topic:machine-learning stars:>200 pushed:>2024-01-01",
        height=88,
        label_visibility="collapsed",
        help="Standard GitHub search query used by the scout agent.",
    )
    max_projects = st.slider(
        "Max projects to scout",
        3,
        20,
        settings.max_projects_to_scout,
    )

    st.markdown('<div class="sidebar-heading">Service Readiness</div>', unsafe_allow_html=True)
    status_items = [
        ("Groq LLM", "groq_api_key"),
        ("GitHub", "github_token"),
        ("Tavily Search", "tavily_api_key"),
        ("LangSmith", "langchain_api_key"),
        ("Google Calendar", "google_client_id"),
    ]
    rows = []
    for label, attr in status_items:
        dot_class = "dot-ok" if api_ok(attr) else "dot-missing"
        state = "Ready" if api_ok(attr) else "Optional / Missing"
        rows.append(
            f"""
            <div class="api-row">
                <div><span class="api-dot {dot_class}"></span>{label}</div>
                <div style="color:#7c6854;font-size:0.84rem;">{state}</div>
            </div>
            """
        )
    st.markdown(
        f'<div class="section-card">{"".join(rows)}</div>',
        unsafe_allow_html=True,
    )

    if api_ok("langchain_api_key"):
        st.markdown(
            f"[Open LangSmith Project](https://smith.langchain.com/projects/{settings.langchain_project})"
        )

st.markdown(
    """
    <div class="hero-shell">
        <div class="eyebrow">Human Guided Multi-Agent Workflow</div>
        <div class="hero-title">Research, draft, review, and follow up with taste.</div>
        <div class="hero-copy">
            This studio coordinates your scout, researcher, writer, auditor, and scheduler in a
            single light-weight review flow. You keep the final say on every outbound message,
            while the agents do the heavy lifting behind the scenes.
        </div>
        <div class="kpi-strip">
            <div class="kpi-card"><div class="kpi-label">Pipeline</div><div class="kpi-value">5 Agents</div></div>
            <div class="kpi-card"><div class="kpi-label">Review Mode</div><div class="kpi-value">Human Gate</div></div>
            <div class="kpi-card"><div class="kpi-label">Source Mix</div><div class="kpi-value">GitHub + Web</div></div>
            <div class="kpi-card"><div class="kpi-label">Output</div><div class="kpi-value">Draft + Follow-up</div></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="pipeline-grid">
        <div class="stage-chip"><span class="stage-icon">01</span><span class="stage-label">Scout</span></div>
        <div class="stage-chip"><span class="stage-icon">02</span><span class="stage-label">Researcher</span></div>
        <div class="stage-chip"><span class="stage-icon">03</span><span class="stage-label">Writer</span></div>
        <div class="stage-chip"><span class="stage-icon">04</span><span class="stage-label">Auditor</span></div>
        <div class="stage-chip"><span class="stage-icon">05</span><span class="stage-label">Scheduler</span></div>
    </div>
    """,
    unsafe_allow_html=True,
)

top_left, top_right = st.columns([4, 1.2])
with top_left:
    run_btn = st.button(
        "Run Full Pipeline",
        type="primary",
        disabled=st.session_state.pipeline_running,
        use_container_width=True,
    )
with top_right:
    reset_btn = st.button("Reset Workspace", use_container_width=True)
    if reset_btn:
        for key, value in defaults.items():
            st.session_state[key] = value
        st.rerun()

st.markdown(
    """
    <div class="section-card">
        <div class="section-title">Search Direction</div>
        <div class="section-copy">
            Curate recently active repositories with signal, then move the best maintainer profiles
            into personalized outreach and a final human review.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="status-pill">Query in use: {search_query}</div>',
    unsafe_allow_html=True,
)

if run_btn:
    st.session_state.pipeline_running = True
    st.session_state.pipeline_complete = False
    st.session_state.schedule_done = False
    st.session_state.schedule_result = ""

    from crew import build_crew

    st.markdown("### Pipeline Activity")
    progress_bar = st.progress(0, text="Preparing your agents...")
    log_area = st.empty()
    log_lines: list[str] = []

    def log(message: str) -> None:
        log_lines.append(message)
        log_area.code("\n".join(log_lines[-24:]), language=None)

    try:
        log("Refining search brief and assembling the crew.")
        progress_bar.progress(8, text="Building the workflow...")
        crew, tasks = build_crew(search_query, max_projects=max_projects)

        log(f"Scout will evaluate up to {max_projects} candidate repositories.")
        progress_bar.progress(22, text="Scout and researcher are working...")
        raw_result = crew.kickoff()

        progress_bar.progress(82, text="Auditor is finalizing the draft review...")
        log("Auditor is checking specificity, structure, and tone.")
        time.sleep(0.4)

        audit_raw = ""
        if hasattr(tasks[3], "output") and tasks[3].output:
            audit_raw = tasks[3].output.raw_output or ""

        try:
            clean = audit_raw.strip().lstrip("```json").rstrip("```").strip()
            st.session_state.audit_report = json.loads(clean)
        except Exception:
            st.session_state.audit_report = {
                "approved": [],
                "rejected": [],
                "overall_quality_score": 0,
                "_parse_error": audit_raw[:500],
            }

        st.session_state.results = {
            "scout_output": getattr(tasks[0].output, "raw_output", "") if hasattr(tasks[0], "output") else "",
            "research_output": getattr(tasks[1].output, "raw_output", "") if hasattr(tasks[1], "output") else "",
            "draft_emails": getattr(tasks[2].output, "raw_output", "") if hasattr(tasks[2], "output") else "",
            "audit_report": audit_raw,
        }

        progress_bar.progress(100, text="Review-ready")
        log("The draft set is ready for your approval.")
        st.session_state.pipeline_complete = True
    except Exception as exc:
        st.error(f"Pipeline error: {exc}")
        log(f"ERROR: {exc}")
    finally:
        st.session_state.pipeline_running = False

    st.rerun()

if st.session_state.pipeline_complete and st.session_state.audit_report:
    report = st.session_state.audit_report
    approved_drafts = report.get("approved", [])
    rejected_drafts = report.get("rejected", [])
    quality_score = report.get("overall_quality_score", 0)

    st.markdown("## Review Desk")
    stat_a, stat_b, stat_c, stat_d = st.columns(4)
    stat_a.metric("Auditor Approved", len(approved_drafts))
    stat_b.metric("Auditor Rejected", len(rejected_drafts))
    stat_c.metric("Quality Score", f"{quality_score:.0%}")
    stat_d.metric("Ready For You", len(approved_drafts))

    if approved_drafts:
        st.markdown("### Curated Drafts")
        st.markdown(
            '<div class="muted-note">Review each message, refine the body if needed, and approve only the ones you would actually send.</div>',
            unsafe_allow_html=True,
        )

        for i, email in enumerate(approved_drafts):
            confidence = float(email.get("confidence", 0.5))
            conf_label = "High" if confidence > 0.7 else ("Medium" if confidence > 0.4 else "Low")
            with st.expander(
                f"{i + 1}. {email.get('to_name', 'Unknown')} • {email.get('project', 'No project')} • {conf_label} confidence",
                expanded=(i == 0),
            ):
                col_a, col_b = st.columns([2.2, 1])
                with col_a:
                    st.markdown(f"**Subject**  \n{email.get('subject', '')}")
                    st.markdown(f"**Recipient**  \n{email.get('to_email') or 'Email not available'}")
                    st.markdown(f"**Personalization Hook**  \n_{email.get('personalisation_hook', '')}_")
                    edited_body = st.text_area(
                        "Email Body",
                        value=st.session_state.email_edits.get(i, email.get("body", "")),
                        height=220,
                        key=f"body_{i}",
                    )
                    st.session_state.email_edits[i] = edited_body
                with col_b:
                    st.markdown(
                        f"""
                        <div class="section-card">
                            <div class="section-title">Decision Panel</div>
                            <div class="section-copy">Confidence score: <strong>{confidence:.0%}</strong></div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    decision = st.radio(
                        "Decision",
                        options=["Undecided", "Approve", "Reject"],
                        index=0,
                        key=f"decision_{i}",
                    )
                    st.session_state.email_decisions[i] = decision

    if rejected_drafts:
        with st.expander(f"Auditor Rejections ({len(rejected_drafts)})"):
            for rejected in rejected_drafts:
                name = rejected.get("email", {}).get("to_name", "Unknown")
                reasons = ", ".join(rejected.get("reasons", []))
                st.markdown(f"**{name}**")
                st.caption(reasons or "No rejection details provided.")
                st.caption(f"Fix instructions: {rejected.get('fix_instructions', '')}")

    submit_btn = st.button("Confirm Approvals and Schedule Follow-ups", type="primary")
    if submit_btn:
        final_approved = []
        for i, email in enumerate(approved_drafts):
            if st.session_state.email_decisions.get(i) == "Approve":
                approved_email = dict(email)
                approved_email["body"] = st.session_state.email_edits.get(i, email.get("body", ""))
                final_approved.append(approved_email)

        st.session_state.approved_emails = final_approved

        if final_approved:
            with st.spinner(f"Scheduling {len(final_approved)} follow-up reminder(s)..."):
                from crew import build_scheduler_agent
                from crewai import Crew, Process, Task

                scheduler = build_scheduler_agent()
                schedule_task = Task(
                    description=(
                        "Schedule follow-up calendar events for these approved emails:\n"
                        f"{json.dumps(final_approved, indent=2)}\n\n"
                        "Create one Google Calendar event per email, 7 days from today."
                    ),
                    expected_output="A scheduling summary.",
                    agent=scheduler,
                )
                schedule_crew = Crew(
                    agents=[scheduler],
                    tasks=[schedule_task],
                    process=Process.sequential,
                    verbose=True,
                )
                schedule_result = schedule_crew.kickoff()
                st.session_state.schedule_done = True
                st.session_state.schedule_result = str(schedule_result)

            st.success(f"{len(final_approved)} email(s) approved and handed to the scheduler.")
        else:
            st.warning("No emails were approved, so nothing was scheduled.")

if st.session_state.schedule_done:
    st.markdown("## Scheduling Summary")
    st.markdown('<div class="code-shell">', unsafe_allow_html=True)
    st.code(st.session_state.schedule_result or "No scheduling output available.", language="json")
    st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.results:
    st.markdown("## Output Archive")
    tab1, tab2, tab3, tab4 = st.tabs(["Scout", "Researcher", "Writer", "Auditor"])
    with tab1:
        st.code(st.session_state.results.get("scout_output", "No output"), language="json")
    with tab2:
        st.code(st.session_state.results.get("research_output", "No output"), language="json")
    with tab3:
        st.code(st.session_state.results.get("draft_emails", "No output"), language="json")
    with tab4:
        st.code(st.session_state.results.get("audit_report", "No output"), language="json")

st.caption("Outreach Atelier · CrewAI workflow · Human approval before scheduling")
