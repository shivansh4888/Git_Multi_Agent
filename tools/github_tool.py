"""
tools/github_tool.py
Wraps the GitHub REST API as a LangChain-compatible tool.
The Scout agent uses this to discover trending open-source AI projects.
"""
from __future__ import annotations

import json
from typing import Optional, Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from config import get_settings

settings = get_settings()

GITHUB_API = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {settings.github_token}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


# ── Input schemas (so agents know what args to pass) ──────────────────────────

class SearchReposInput(BaseModel):
    query: str = Field(
        ...,
        description=(
            "GitHub search query string. E.g. "
            "'topic:machine-learning stars:>500 pushed:>2024-01-01'"
        ),
    )
    max_results: int = Field(5, description="Max number of repos to return (1-20).")


class GetRepoDetailsInput(BaseModel):
    owner: str = Field(..., description="GitHub username or org name.")
    repo: str = Field(..., description="Repository name.")


class GetContributorsInput(BaseModel):
    owner: str = Field(..., description="GitHub username or org name.")
    repo: str = Field(..., description="Repository name.")
    top_n: int = Field(3, description="Return the top-N contributors.")


# ── Tool implementations ───────────────────────────────────────────────────────

class GitHubSearchTool(BaseTool):
    """Search GitHub for repositories matching a query."""

    name: str = "github_search_repos"
    description: str = (
        "Search GitHub repositories. Use this to find trending open-source AI projects. "
        "Input should be a GitHub search query string."
    )
    args_schema: Type[BaseModel] = SearchReposInput

    def _run(self, query: str, max_results: int = 5) -> str:
        max_results = min(max_results, 20)
        url = f"{GITHUB_API}/search/repositories"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": max_results,
        }
        try:
            resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
            resp.raise_for_status()
            items = resp.json().get("items", [])
            results = []
            for item in items:
                results.append(
                    {
                        "full_name": item["full_name"],
                        "description": item.get("description", ""),
                        "stars": item["stargazers_count"],
                        "forks": item["forks_count"],
                        "language": item.get("language"),
                        "topics": item.get("topics", []),
                        "url": item["html_url"],
                        "owner_login": item["owner"]["login"],
                        "owner_type": item["owner"]["type"],
                        "pushed_at": item.get("pushed_at"),
                    }
                )
            return json.dumps(results, indent=2)
        except requests.RequestException as e:
            return f"ERROR: GitHub API request failed — {e}"

    async def _arun(self, *args, **kwargs):  # async stub
        raise NotImplementedError


class GitHubRepoDetailsTool(BaseTool):
    """Fetch detailed metadata for a single GitHub repository."""

    name: str = "github_get_repo_details"
    description: str = (
        "Fetch detailed information (README excerpt, open issues, license, etc.) "
        "for a specific GitHub repo given owner and repo name."
    )
    args_schema: Type[BaseModel] = GetRepoDetailsInput

    def _run(self, owner: str, repo: str) -> str:
        try:
            repo_url = f"{GITHUB_API}/repos/{owner}/{repo}"
            readme_url = f"{GITHUB_API}/repos/{owner}/{repo}/readme"

            repo_resp = requests.get(repo_url, headers=HEADERS, timeout=10)
            repo_resp.raise_for_status()
            data = repo_resp.json()

            # Fetch README (base64 encoded by GitHub)
            readme_text = ""
            try:
                readme_resp = requests.get(readme_url, headers=HEADERS, timeout=10)
                if readme_resp.ok:
                    import base64

                    content = readme_resp.json().get("content", "")
                    readme_text = base64.b64decode(content).decode("utf-8", errors="ignore")[:800]
            except Exception:
                pass

            return json.dumps(
                {
                    "full_name": data["full_name"],
                    "description": data.get("description"),
                    "stars": data["stargazers_count"],
                    "open_issues": data["open_issues_count"],
                    "license": data.get("license", {}).get("name") if data.get("license") else None,
                    "homepage": data.get("homepage"),
                    "topics": data.get("topics", []),
                    "readme_excerpt": readme_text[:600],
                },
                indent=2,
            )
        except requests.RequestException as e:
            return f"ERROR: {e}"

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError


class GitHubContributorsTool(BaseTool):
    """Get top contributors of a repository and their public profile info."""

    name: str = "github_get_contributors"
    description: str = (
        "Get the top contributors for a GitHub repository. "
        "Returns their login, profile URL, email (if public), and company."
    )
    args_schema: Type[BaseModel] = GetContributorsInput

    def _run(self, owner: str, repo: str, top_n: int = 3) -> str:
        try:
            url = f"{GITHUB_API}/repos/{owner}/{repo}/contributors"
            params = {"per_page": top_n}
            resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
            resp.raise_for_status()
            contributors = resp.json()

            enriched = []
            for c in contributors[:top_n]:
                login = c["login"]
                user_resp = requests.get(
                    f"{GITHUB_API}/users/{login}", headers=HEADERS, timeout=10
                )
                user_data = user_resp.json() if user_resp.ok else {}
                enriched.append(
                    {
                        "login": login,
                        "name": user_data.get("name"),
                        "email": user_data.get("email"),
                        "company": user_data.get("company"),
                        "bio": user_data.get("bio"),
                        "twitter": user_data.get("twitter_username"),
                        "blog": user_data.get("blog"),
                        "location": user_data.get("location"),
                        "profile_url": c["html_url"],
                        "contributions": c["contributions"],
                    }
                )
            return json.dumps(enriched, indent=2)
        except requests.RequestException as e:
            return f"ERROR: {e}"

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError
