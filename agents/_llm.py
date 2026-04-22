from __future__ import annotations

import json
from typing import Any

from crewai.llms.base_llm import BaseLLM
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage


class LangChainGroqAdapter(BaseLLM):
    """
    Minimal CrewAI-compatible wrapper around a LangChain chat model.

    CrewAI only accepts a model string or a BaseLLM instance for `Agent.llm`.
    Passing a raw LangChain `ChatGroq` object causes CrewAI to fall back to its
    default provider resolution, which then asks for `OPENAI_API_KEY`.
    """

    llm_type: str = "custom"
    provider: str = "groq"
    client: Any = None

    def _coerce_messages(self, messages: str | list[dict[str, Any]]) -> list[Any]:
        if isinstance(messages, str):
            return [HumanMessage(content=messages)]

        converted: list[Any] = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content") or ""

            if role in {"user", "human"}:
                converted.append(HumanMessage(content=content))
                continue

            if role == "system":
                converted.append(SystemMessage(content=content))
                continue

            if role == "assistant":
                tool_calls = []
                for tool_call in message.get("tool_calls", []) or []:
                    function = tool_call.get("function", {})
                    raw_args = function.get("arguments") or {}
                    if isinstance(raw_args, str):
                        try:
                            raw_args = json.loads(raw_args)
                        except json.JSONDecodeError:
                            raw_args = {}
                    tool_calls.append(
                        {
                            "id": tool_call.get("id"),
                            "name": function.get("name"),
                            "args": raw_args,
                        }
                    )
                converted.append(AIMessage(content=content, tool_calls=tool_calls))
                continue

            if role == "tool":
                converted.append(
                    ToolMessage(
                        content=content,
                        tool_call_id=message.get("tool_call_id", ""),
                        name=message.get("name"),
                    )
                )
                continue

            converted.append(HumanMessage(content=content))

        return converted

    def _stringify_content(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
            return "\n".join(part for part in parts if part).strip()
        return str(content or "")

    def call(
        self,
        messages: str | list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        callbacks: list[Any] | None = None,
        available_functions: dict[str, Any] | None = None,
        from_task: Any | None = None,
        from_agent: Any | None = None,
        response_model: Any | None = None,
    ) -> str | Any:
        del callbacks, available_functions, from_task, from_agent, response_model

        runnable = self.client.bind_tools(tools) if tools else self.client
        response = runnable.invoke(
            self._coerce_messages(messages),
            stop=self.stop or None,
        )

        if getattr(response, "tool_calls", None):
            return [
                {
                    "id": tool_call.get("id") or f"call_{index}",
                    "type": "function",
                    "function": {
                        "name": tool_call.get("name", ""),
                        "arguments": json.dumps(tool_call.get("args", {})),
                    },
                }
                for index, tool_call in enumerate(response.tool_calls, start=1)
            ]

        return self._apply_stop_words(self._stringify_content(response.content))

    async def acall(
        self,
        messages: str | list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        callbacks: list[Any] | None = None,
        available_functions: dict[str, Any] | None = None,
        from_task: Any | None = None,
        from_agent: Any | None = None,
        response_model: Any | None = None,
    ) -> str | Any:
        return self.call(
            messages=messages,
            tools=tools,
            callbacks=callbacks,
            available_functions=available_functions,
            from_task=from_task,
            from_agent=from_agent,
            response_model=response_model,
        )


def normalize_agent_llm(llm, fallback_model: str):
    """
    Return a CrewAI-compatible LLM object for real runs and mocked tests.
    """
    if isinstance(llm, BaseLLM):
        return llm
    if isinstance(llm, str):
        return llm
    return LangChainGroqAdapter(
        model=fallback_model,
        provider="groq",
        temperature=getattr(llm, "temperature", None),
        client=llm,
    )
