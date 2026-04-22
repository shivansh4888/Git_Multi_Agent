"""
tests/test_pipeline.py
──────────────────────
Unit and integration tests for the multi-agent pipeline.
Run with: pytest tests/ -v

Tests are structured in layers:
  1. Tool tests (mock API calls)
  2. Agent tests (mock LLM + tools)
  3. Pipeline integration tests (mock everything, test flow)
  4. Human gate tests
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest


# ─────────────────────────────────────────────────────────────────────────────
# 1. Tool Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestGitHubSearchTool:
    """Test GitHubSearchTool with mocked HTTP calls."""

    @patch("tools.github_tool.requests.get")
    def test_search_returns_structured_results(self, mock_get):
        from tools.github_tool import GitHubSearchTool

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "items": [
                {
                    "full_name": "owner/repo",
                    "description": "A great ML library",
                    "stargazers_count": 1500,
                    "forks_count": 200,
                    "language": "Python",
                    "topics": ["machine-learning", "nlp"],
                    "html_url": "https://github.com/owner/repo",
                    "owner": {"login": "owner", "type": "User"},
                    "pushed_at": "2024-03-01T00:00:00Z",
                }
            ]
        }
        mock_get.return_value = mock_resp

        tool = GitHubSearchTool()
        result = tool._run(query="topic:machine-learning stars:>500", max_results=5)
        data = json.loads(result)

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["full_name"] == "owner/repo"
        assert data[0]["stars"] == 1500

    @patch("tools.github_tool.requests.get")
    def test_search_handles_api_error(self, mock_get):
        from tools.github_tool import GitHubSearchTool
        import requests

        mock_get.side_effect = requests.RequestException("Rate limit exceeded")

        tool = GitHubSearchTool()
        result = tool._run(query="test", max_results=3)

        assert "ERROR" in result
        assert "Rate limit" in result

    @patch("tools.github_tool.requests.get")
    def test_max_results_capped_at_20(self, mock_get):
        from tools.github_tool import GitHubSearchTool

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"items": []}
        mock_get.return_value = mock_resp

        tool = GitHubSearchTool()
        tool._run(query="test", max_results=50)  # Should be capped

        # Check the actual request was made with per_page <= 20
        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["params"]["per_page"] <= 20


class TestGitHubContributorsTool:
    @patch("tools.github_tool.requests.get")
    def test_enriches_contributor_profiles(self, mock_get):
        from tools.github_tool import GitHubContributorsTool

        # First call: contributors list; subsequent calls: user profiles
        contributors_resp = MagicMock()
        contributors_resp.ok = True
        contributors_resp.json.return_value = [
            {"login": "alice", "html_url": "https://github.com/alice", "contributions": 42}
        ]

        user_resp = MagicMock()
        user_resp.ok = True
        user_resp.json.return_value = {
            "name": "Alice Smith",
            "email": "alice@example.com",
            "bio": "ML researcher",
            "twitter_username": "alice_ml",
            "blog": "https://alice.dev",
            "company": "OpenAI",
            "location": "San Francisco",
        }

        mock_get.side_effect = [contributors_resp, user_resp]

        tool = GitHubContributorsTool()
        result = tool._run(owner="owner", repo="repo", top_n=1)
        data = json.loads(result)

        assert data[0]["login"] == "alice"
        assert data[0]["name"] == "Alice Smith"
        assert data[0]["twitter"] == "alice_ml"


class TestTavilySearchTool:
    @patch("tools.search_tool.requests.post")
    def test_search_returns_structured_results(self, mock_post):
        from tools.search_tool import TavilySearchTool

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "answer": "Alice Smith is a researcher who...",
            "results": [
                {
                    "title": "Alice Smith's blog",
                    "url": "https://alice.dev/post",
                    "content": "I've been working on attention mechanisms...",
                    "score": 0.9,
                }
            ],
        }
        mock_post.return_value = mock_resp

        tool = TavilySearchTool()
        result = tool._run(query="Alice Smith ML researcher GitHub")
        data = json.loads(result)

        assert "answer" in data
        assert len(data["results"]) == 1
        assert data["results"][0]["score"] == 0.9

    @patch("tools.search_tool.requests.post")
    def test_handles_network_error(self, mock_post):
        from tools.search_tool import TavilySearchTool
        import requests

        mock_post.side_effect = requests.RequestException("Timeout")

        tool = TavilySearchTool()
        result = tool._run(query="test")

        assert "ERROR" in result


class TestCalendarTool:
    def test_demo_mode_when_no_token(self):
        from tools.calendar_tool import CreateCalendarEventTool

        tool = CreateCalendarEventTool()
        # Without a real OAuth token, should return DEMO_MODE response
        result = tool._run(
            title="Follow-up: Alice re ml-framework",
            description="Sent outreach email on 2024-03-01",
            attendee_email="alice@example.com",
            days_from_now=7,
        )
        data = json.loads(result)
        assert data["status"] == "DEMO_MODE"
        assert "would_create" in data


# ─────────────────────────────────────────────────────────────────────────────
# 2. Human Gate Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestHumanApprovalGate:
    def test_auto_approve_when_flag_disabled(self, monkeypatch):
        """When HUMAN_APPROVAL_REQUIRED=false, all approved emails pass through."""
        from config import get_settings
        settings = get_settings()
        original = settings.human_approval_required

        # Temporarily disable the flag
        monkeypatch.setattr(settings, "human_approval_required", False)

        from crew import human_approval_gate

        audit_json = json.dumps(
            {
                "approved": [
                    {
                        "to_name": "Alice",
                        "to_email": "alice@example.com",
                        "subject": "Re: your attention mechanism paper",
                        "body": "Hi Alice, I read your recent blog post about...",
                        "personalisation_hook": "blog post about attention",
                        "project": "ml-framework",
                        "confidence": 0.8,
                    }
                ],
                "rejected": [],
                "overall_quality_score": 0.8,
            }
        )

        result = human_approval_gate(audit_json)
        assert len(result) == 1
        assert result[0]["to_name"] == "Alice"

    def test_handles_malformed_audit_json(self, monkeypatch):
        from config import get_settings
        monkeypatch.setattr(get_settings(), "human_approval_required", False)
        from crew import human_approval_gate

        result = human_approval_gate("this is not JSON at all {{{")
        # Should not crash, should return empty list
        assert isinstance(result, list)

    def test_handles_markdown_wrapped_json(self, monkeypatch):
        from config import get_settings
        monkeypatch.setattr(get_settings(), "human_approval_required", False)
        from crew import human_approval_gate

        # LLMs often wrap JSON in markdown fences
        wrapped = "```json\n{\"approved\": [], \"rejected\": []}\n```"
        result = human_approval_gate(wrapped)
        assert isinstance(result, list)


class TestSettings:
    def test_accepts_legacy_model_env_name(self, monkeypatch):
        monkeypatch.setenv("MODEL", "llama-3.1-70b-versatile")
        monkeypatch.delenv("GROQ_MODEL", raising=False)

        from config.settings import Settings

        settings = Settings()
        assert settings.groq_model == "llama-3.1-70b-versatile"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Agent Construction Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAgentBuilders:
    """Verify agents are constructed correctly (without calling LLM)."""

    @patch("agents.scout_agent.ChatGroq")
    def test_scout_agent_has_correct_tools(self, mock_llm):
        from agents.scout_agent import build_scout_agent
        from tools import GitHubSearchTool, GitHubRepoDetailsTool, GitHubContributorsTool

        agent = build_scout_agent()

        tool_names = {t.name for t in agent.tools}
        assert "github_search_repos" in tool_names
        assert "github_get_repo_details" in tool_names
        assert "github_get_contributors" in tool_names

    @patch("agents.researcher_agent.ChatGroq")
    def test_researcher_agent_has_correct_tools(self, mock_llm):
        from agents.researcher_agent import build_researcher_agent

        agent = build_researcher_agent()
        tool_names = {t.name for t in agent.tools}
        assert "github_get_contributors" in tool_names
        assert "web_search" in tool_names

    @patch("agents.writer_agent.ChatGroq")
    def test_writer_agent_has_no_tools(self, mock_llm):
        """Writer should not have tools — it uses context from Researcher."""
        from agents.writer_agent import build_writer_agent

        agent = build_writer_agent()
        assert len(agent.tools) == 0

    @patch("agents.auditor_agent.ChatGroq")
    def test_auditor_uses_zero_temperature(self, mock_llm):
        """Auditor MUST use temp=0 for consistent evaluation."""
        from agents.auditor_agent import build_auditor_agent

        build_auditor_agent()
        call_kwargs = mock_llm.call_args[1]
        assert call_kwargs["temperature"] == 0.0

    @patch("agents.scheduler_agent.ChatGroq")
    def test_scheduler_has_calendar_tools(self, mock_llm):
        from agents.scheduler_agent import build_scheduler_agent

        agent = build_scheduler_agent()
        tool_names = {t.name for t in agent.tools}
        assert "create_calendar_event" in tool_names


# ─────────────────────────────────────────────────────────────────────────────
# 4. API Endpoint Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAPI:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from ui.api import app
        return TestClient(app)

    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_run_endpoint_creates_run(self, client):
        resp = client.post(
            "/run",
            json={"search_query": "topic:machine-learning stars:>100", "max_projects": 3},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "run_id" in data
        assert data["status"] in ("queued", "running")

    def test_status_unknown_run_returns_404(self, client):
        resp = client.get("/status/nonexistent")
        assert resp.status_code == 404

    def test_approve_unknown_run_returns_404(self, client):
        resp = client.post(
            "/approve/nonexistent",
            json={"approved_indices": [0]},
        )
        assert resp.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# Run marker
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
