from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ProviderName = Literal["gemini", "groq"]

SQL_GENERATION_PROMPT = """You are a SQL generator.

Use only the given schema.
Do not assume missing data.
If unrelated, return 'INVALID_QUERY'.

Schema:
{schema}

Query:
{user_query}"""


RESULT_SUMMARY_PROMPT = """You are a data analyst assistant.
Convert SQL query results into a clear, concise natural-language answer.

Rules:
- Be factual and only use the provided result rows.
- If rows are empty, say no matching records were found.
- Do not invent values.

User question:
{user_query}

SQL:
{sql}

Columns:
{columns}

Rows:
{rows}
"""


class LLMClient(Protocol):
    def generate_text(self, prompt: str) -> str:
        ...


def _post_json(url: str, payload: Dict[str, Any], headers: Dict[str, str], timeout: int = 60) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = Request(url=url, data=data, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM API HTTP error {exc.code}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"LLM API connection error: {exc}") from exc


@dataclass
class GeminiClient:
    api_key: str
    model: str = "gemini-1.5-flash"

    def generate_text(self, prompt: str) -> str:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
            },
        }
        data = _post_json(url=url, payload=payload, headers={"Content-Type": "application/json"})
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini returned no candidates.")
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise RuntimeError("Gemini returned empty content.")
        text = parts[0].get("text", "")
        return text.strip()


@dataclass
class GroqClient:
    api_key: str
    model: str = "llama-3.1-70b-versatile"

    def generate_text(self, prompt: str) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": self.model,
            "temperature": 0.1,
            "messages": [
                {"role": "user", "content": prompt},
            ],
        }
        data = _post_json(
            url=url,
            payload=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("Groq returned no choices.")
        text = choices[0].get("message", {}).get("content", "")
        return text.strip()


def _normalize_sql_output(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    if text.lower().startswith("sql"):
        text = text[3:].strip(": \n")
    if not text:
        return "INVALID_QUERY"
    return text


class LLMService:
    """
    Modular service for:
    1) natural language -> SQL
    2) SQL result -> natural language
    """

    def __init__(self, client: LLMClient):
        self.client = client

    @classmethod
    def from_provider(
        cls,
        provider: ProviderName,
        *,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> "LLMService":
        if provider == "gemini":
            key = api_key or os.getenv("GEMINI_API_KEY")
            if not key:
                raise ValueError("Missing Gemini API key. Set GEMINI_API_KEY or pass api_key.")
            client = GeminiClient(api_key=key, model=model or "gemini-1.5-flash")
            return cls(client=client)

        if provider == "groq":
            key = api_key or os.getenv("GROQ_API_KEY")
            if not key:
                raise ValueError("Missing Groq API key. Set GROQ_API_KEY or pass api_key.")
            client = GroqClient(api_key=key, model=model or "llama-3.1-70b-versatile")
            return cls(client=client)

        raise ValueError(f"Unsupported provider: {provider}")

    def natural_language_to_sql(self, *, schema: str, user_query: str) -> str:
        """
        Convert NL query to SQL using strict prompt policy.
        Returns SQL string or INVALID_QUERY.
        """
        prompt = SQL_GENERATION_PROMPT.format(schema=schema, user_query=user_query)
        raw = self.client.generate_text(prompt)
        sql = _normalize_sql_output(raw)
        if "INVALID_QUERY" in sql.upper():
            return "INVALID_QUERY"
        return sql

    def sql_result_to_natural_language(
        self,
        *,
        user_query: str,
        sql: str,
        columns: List[str],
        rows: List[Dict[str, Any]],
    ) -> str:
        """
        Convert raw SQL result rows into a concise natural-language answer.
        """
        prompt = RESULT_SUMMARY_PROMPT.format(
            user_query=user_query,
            sql=sql,
            columns=json.dumps(columns, ensure_ascii=True),
            rows=json.dumps(rows, ensure_ascii=True, default=str),
        )
        return self.client.generate_text(prompt).strip()
