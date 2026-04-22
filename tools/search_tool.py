"""
tools/search_tool.py
Wraps the Tavily Search API as a LangChain tool.
The Researcher agent uses this to find public info about maintainers.

Free tier: 1000 searches/month — https://app.tavily.com
"""
from __future__ import annotations

import json
from typing import Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from config import get_settings

settings = get_settings()

TAVILY_URL = "https://api.tavily.com/search"


class TavilySearchInput(BaseModel):
    query: str = Field(..., description="Search query string.")
    max_results: int = Field(5, description="Number of results to return.")
    search_depth: str = Field(
        "basic",
        description="'basic' (faster) or 'advanced' (more thorough, uses more quota).",
    )


class TavilySearchTool(BaseTool):
    """
    Search the web using Tavily.
    Researcher agent uses this to look up maintainers, their talks, blog posts,
    Twitter presence, LinkedIn, company info, etc.
    """

    name: str = "web_search"
    description: str = (
        "Search the web for public information about a person or topic. "
        "Use for finding maintainer blogs, tweets, conference talks, LinkedIn, etc. "
        "Input: a natural language query string."
    )
    args_schema: Type[BaseModel] = TavilySearchInput

    def _run(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
    ) -> str:
        payload = {
            "api_key": settings.tavily_api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_answer": True,   # Tavily summarises results for you
            "include_raw_content": False,
        }
        try:
            resp = requests.post(TAVILY_URL, json=payload, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            output = {
                "answer": data.get("answer", ""),
                "results": [
                    {
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "content": r.get("content", "")[:400],
                        "score": r.get("score"),
                    }
                    for r in data.get("results", [])
                ],
            }
            return json.dumps(output, indent=2)
        except requests.RequestException as e:
            return f"ERROR: Tavily request failed — {e}"

    async def _arun(self, *args, **kwargs):
        raise NotImplementedError
