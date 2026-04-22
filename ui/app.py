"""
ui/app.py
---------
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
    page_icon="OA",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --primary: #2563EB;
        --primary-deep: #1D4ED8;
        --primary-soft: #DBEAFE;
        --surface: rgba(255, 255, 255, 0.92);
        --surface-strong: #FFFFFF;
        --surface-alt: #F8FBFF;
        --page: #F8FAFC;
        --page-tint: #EFF6FF;
        --text: #0F172A;
        --muted: #64748B;
        --line: rgba(148, 163, 184, 0.24);
        --line-strong: rgba(37, 99, 235, 0.22);
        --success: #059669;
        --warning: #D97706;
        --danger: #DC2626;
        --shadow-soft: 0 14px 40px rgba(15, 23, 42, 0.06);
        --shadow-card: 0 18px 50px rgba(37, 99, 235, 0.08);
        --radius-xl: 28px;
        --radius-lg: 22px;
        --radius-md: 18px;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: var(--text);
    }

    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at top left, rgba(191, 219, 254, 0.55), transparent 26%),
            radial-gradient(circle at bottom right, rgba(219, 234, 254, 0.65), transparent 28%),
            linear-gradient(180deg, #F8FBFF 0%, #F8FAFC 100%);
    }

    [data-testid="stHeader"] {
        background: rgba(248, 250, 252, 0.72);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #F8FBFF 0%, #F1F7FF 100%);
        border-right: 1px solid rgba(191, 219, 254, 0.8);
    }

    .block-container {
        padding-top: 1.6rem;
        padding-bottom: 3rem;
        max-width: 1240px;
    }

    h1, h2, h3 {
        letter-spacing: -0.04em;
        color: var(--text);
    }

    .eyebrow {
        margin-bottom: 0.85rem;
        color: var(--primary);
        text-transform: uppercase;
        letter-spacing: 0.14em;
        font-size: 0.76rem;
        font-weight: 800;
    }

    .hero-shell {
        position: relative;
        overflow: hidden;
        margin-bottom: 1.25rem;
        padding: 2.2rem;
        border-radius: 32px;
        border: 1px solid rgba(191, 219, 254, 0.85);
        background:
            radial-gradient(circle at top right, rgba(191, 219, 254, 0.65), transparent 28%),
            linear-gradient(135deg, rgba(255,255,255,0.95), rgba(239,246,255,0.96));
        box-shadow: var(--shadow-card);
        animation: floatUp 0.6s ease-out both;
    }

    .hero-shell::before {
        content: "";
        position: absolute;
        width: 260px;
        height: 260px;
        right: -80px;
        top: -90px;
        border-radius: 999px;
        background: radial-gradient(circle, rgba(147, 197, 253, 0.34), transparent 68%);
    }

    .hero-title {
        margin: 0 0 0.85rem 0;
        max-width: 760px;
        font-size: clamp(2.4rem, 5vw, 4.3rem);
        line-height: 0.98;
        font-weight: 800;
    }

    .hero-copy {
        max-width: 760px;
        font-size: 1rem;
        line-height: 1.75;
        color: var(--muted);
    }

    .kpi-strip {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.95rem;
        margin-top: 1.55rem;
    }

    .kpi-card,
    .section-card,
    .timeline-card,
    .sidebar-brand,
    .email-shell,
    div[data-testid="stMetric"],
    div[data-testid="stExpander"] {
        background: var(--surface);
        border: 1px solid var(--line);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-soft);
        backdrop-filter: blur(12px);
    }

    .kpi-card {
        padding: 1rem 1.05rem;
        transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
    }

    .kpi-card:hover,
    .stage-chip:hover,
    .section-card:hover {
        transform: translateY(-2px);
        border-color: var(--line-strong);
        box-shadow: 0 18px 40px rgba(37, 99, 235, 0.09);
    }

    .kpi-label {
        margin-bottom: 0.55rem;
        color: var(--muted);
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
    }

    .kpi-value {
        font-size: 1.6rem;
        font-weight: 800;
        color: var(--text);
    }

    .section-card {
        padding: 1.15rem 1.15rem 1rem;
        margin-bottom: 1rem;
        transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
    }

    .section-title {
        margin-bottom: 0.35rem;
        font-size: 1.12rem;
        font-weight: 800;
        color: var(--text);
    }

    .section-copy {
        color: var(--muted);
        line-height: 1.68;
        font-size: 0.95rem;
    }

    .pipeline-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 0.82rem;
        margin: 0.7rem 0 1.15rem;
    }

    .stage-chip {
        padding: 0.95rem 0.9rem;
        text-align: center;
        border-radius: 20px;
        border: 1px solid var(--line);
        background: rgba(255, 255, 255, 0.8);
        box-shadow: var(--shadow-soft);
        transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
    }

    .stage-icon {
        display: block;
        margin-bottom: 0.32rem;
        font-size: 1.1rem;
        font-weight: 800;
        color: var(--primary);
    }

    .stage-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--text);
        font-weight: 800;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.52rem 0.85rem;
        border-radius: 999px;
        background: rgba(219, 234, 254, 0.7);
        border: 1px solid rgba(96, 165, 250, 0.35);
        color: var(--primary-deep);
        font-weight: 700;
        font-size: 0.86rem;
    }

    .sidebar-heading {
        margin-bottom: 0.6rem;
        color: var(--muted);
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        font-weight: 800;
    }

    .sidebar-brand {
        padding: 1rem 1rem 0.95rem;
        margin-bottom: 1rem;
        background: rgba(255,255,255,0.76);
    }

    .brand-mark {
        width: 44px;
        height: 44px;
        margin-bottom: 0.9rem;
        border-radius: 999px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #DBEAFE, #BFDBFE);
        color: var(--primary);
        font-size: 0.95rem;
        font-weight: 800;
        box-shadow: 0 10px 24px rgba(37, 99, 235, 0.12);
    }

    .brand-title {
        margin: 0;
        font-size: 1.65rem;
        font-weight: 800;
        color: var(--text);
        letter-spacing: -0.05em;
    }

    .brand-copy {
        margin-top: 0.35rem;
        color: var(--muted);
        font-size: 0.93rem;
        line-height: 1.58;
    }

    .api-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.68rem 0;
        border-bottom: 1px solid rgba(226, 232, 240, 0.95);
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

    .dot-ok { background: var(--success); }
    .dot-missing { background: #94A3B8; }

    .email-shell {
        padding: 1rem 1rem 0.6rem;
        background: rgba(255,255,255,0.92);
    }

    .code-shell {
        background: rgba(255,255,255,0.82);
        border: 1px solid var(--line);
        border-radius: 24px;
        padding: 0.45rem;
        box-shadow: var(--shadow-soft);
    }

    div[data-testid="stMetric"] {
        padding: 1rem 1rem 0.85rem;
    }

    div[data-testid="stExpander"] {
        overflow: hidden;
    }

    div[data-testid="stTextArea"] textarea,
    div[data-testid="stTextInput"] input,
    div[data-baseweb="select"] > div {
        border-radius: 18px !important;
        border: 1px solid var(--line) !important;
        background: #FFFFFF !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease !important;
    }

    div[data-testid="stTextArea"] textarea:focus,
    div[data-testid="stTextInput"] input:focus {
        border-color: rgba(37, 99, 235, 0.5) !important;
        box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.10) !important;
    }

    div.stButton > button {
        min-height: 3.05rem;
        border-radius: 999px;
        border: 1px solid rgba(191, 219, 254, 0.95);
        background: rgba(255, 255, 255, 0.95);
        color: var(--text);
        font-weight: 700;
        letter-spacing: -0.01em;
        transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, filter 0.18s ease;
    }

    div.stButton > button:hover {
        transform: translateY(-1px);
        border-color: rgba(96, 165, 250, 0.7);
        box-shadow: 0 14px 28px rgba(37, 99, 235, 0.10);
    }

    div.stButton > button[kind="primary"] {
        color: white;
        border: none;
        background: linear-gradient(135deg, #60A5FA 0%, #2563EB 60%, #1D4ED8 100%);
        box-shadow: 0 16px 30px rgba(37, 99, 235, 0.22);
    }

    div.stButton > button[kind="primary"]:hover {
        box-shadow: 0 18px 34px rgba(37, 99, 235, 0.26);
        filter: saturate(1.05);
    }

    .muted-note {
        color: var(--muted);
        font-size: 0.93rem;
        line-height: 1.68;
    }

    [data-testid="stCodeBlock"] {
        border-radius: 18px;
    }

    @keyframes floatUp {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @media (max-width: 980px) {
        .hero-shell {
            padding: 1.45rem;
        }

        .hero-title {
            font-size: 2.8rem;
        }

        .kpi-strip,
        .pipeline-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
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


def build_search_query(topic: str) -> str:
    cleaned_topic = " ".join(topic.strip().split())
    normalized_topic = cleaned_topic.lower().replace(" ", "-")
    if not normalized_topic:
        normalized_topic = "machine-learning"
    return f"topic:{normalized_topic} stars:>200 pushed:>2024-01-01"


with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-mark">OA</div>
            <div class="sidebar-heading">Workspace</div>
            <div class="brand-title">Outreach Atelier</div>
            <div class="brand-copy">
                A calm, modern control room for research-led outreach, approvals, and follow-up planning.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-heading">Search Brief</div>', unsafe_allow_html=True)
    topic = st.text_input(
        "Topic",
        value="machine learning",
        placeholder="Enter a topic like llm, fintech, robotics",
        help="This topic is converted into the GitHub search query used by the scout agent.",
    )
    search_query = build_search_query(topic)
    st.caption(f"Generated query: `{search_query}`")
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
            (
                f'<div class="api-row">'
                f'<div><span class="api-dot {dot_class}"></span>{label}</div>'
                f'<div style="color:#64748B;font-size:0.84rem;">{state}</div>'
                f"</div>"
            )
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
        <div class="hero-title">Research, draft, review, and follow up with a lighter, faster flow.</div>
        <div class="hero-copy">
            This workspace coordinates your scout, researcher, writer, auditor, and scheduler in a
            polished review loop. The interface stays minimal and bright, while the approval flow
            keeps every outbound step clear and easy to manage.
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

intro_left, intro_right = st.columns([1.7, 1])
with intro_left:
    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Search Direction</div>
            <div class="section-copy">
                Curate recently active repositories with signal, then move the strongest maintainer profiles
                into personalized outreach and a final human review.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with intro_right:
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
        crew.kickoff()

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

st.caption("Outreach Atelier · Modern light UI · Human approval before scheduling")
