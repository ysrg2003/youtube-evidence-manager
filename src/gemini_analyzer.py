"""Optional Gemini analysis for an evidence bundle.

The adapter is deliberately opt-in. It never publishes content and never
falls back to inventing citations when the model omits them.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TIMEOUT = 60.0
API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models"
REQUIRED_FIELDS = (
    "source_url",
    "summary",
    "claims",
    "experiences",
    "counterpoints",
    "verification_needed",
    "citations",
    "limitations",
    "confidence",
)


class GeminiAPIError(RuntimeError):
    """A sanitized Gemini API failure."""


def _strip_json_fences(text: str) -> str:
    text = text.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else text


def _default_analysis(source_url: str) -> dict[str, Any]:
    return {
        "source_url": source_url,
        "summary": "",
        "claims": [],
        "experiences": [],
        "counterpoints": [],
        "verification_needed": [],
        "citations": [],
        "limitations": [],
        "confidence": None,
    }


class GeminiAnalyzer:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str | None = None,
        session: requests.Session | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
        self.model = (model or os.getenv("GEMINI_MODEL", DEFAULT_MODEL)).strip()
        self.session = session or requests.Session()
        self.timeout = timeout

    def _prompt(self, bundle: dict[str, Any]) -> str:
        evidence = dict(bundle)
        evidence.pop("_title_for_filename", None)
        return (
            "Analyze the following YouTube evidence bundle. Return only valid JSON, with exactly "
            "these top-level fields: source_url, summary, claims, experiences, counterpoints, "
            "verification_needed, citations, limitations, confidence. Separate creator claims, "
            "caption text, and user-generated comments. Never treat a caption or comment as an "
            "independent fact. Every citation must be copied from source_url or an explicit URL "
            "present in the bundle; if no citation is available, return an empty citations array. "
            "Do not invent facts, links, quotations, or confidence evidence.\n\n"
            + json.dumps(evidence, ensure_ascii=False, indent=2)
        )

    def analyze(self, bundle: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise GeminiAPIError("GEMINI_API_KEY is not configured; omit --analyze or configure it first")
        if not self.model:
            raise GeminiAPIError("GEMINI_MODEL must not be empty")

        url = f"{API_ROOT}/{self.model}:generateContent"
        body = {
            "systemInstruction": {
                "parts": [
                    {
                        "text": (
                            "You are a careful research assistant. Preserve uncertainty and label "
                            "source types. Output JSON only."
                        )
                    }
                ]
            },
            "contents": [{"role": "user", "parts": [{"text": self._prompt(bundle)}]}],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }
        try:
            response = self.session.post(
                url,
                params={"key": self.api_key},
                json=body,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise GeminiAPIError(f"Gemini request failed: {exc}") from exc

        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if response.status_code >= 400:
            error = payload.get("error", {}) if isinstance(payload, dict) else {}
            message = error.get("message") if isinstance(error, dict) else None
            status = error.get("status") if isinstance(error, dict) else None
            detail = ": ".join(str(part) for part in (status, message) if part)
            raise GeminiAPIError(f"Gemini API HTTP {response.status_code}{': ' + detail if detail else ''}")

        try:
            text = payload["candidates"][0]["content"]["parts"][0]["text"]
            result = json.loads(_strip_json_fences(text))
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise GeminiAPIError("Gemini returned no valid JSON analysis") from exc
        if not isinstance(result, dict):
            raise GeminiAPIError("Gemini analysis must be a JSON object")

        normalized = _default_analysis(str(bundle.get("source_url", "")))
        normalized.update({key: result.get(key, default) for key, default in normalized.items()})
        normalized["source_url"] = str(bundle.get("source_url", result.get("source_url", "")))
        normalized["citations"] = result.get("citations") if isinstance(result.get("citations"), list) else []
        normalized["limitations"] = result.get("limitations") if isinstance(result.get("limitations"), list) else []
        return normalized


def render_analysis_markdown(analysis: dict[str, Any]) -> str:
    lines = [
        "# AI-assisted research analysis",
        "",
        "> هذا التحليل مساعد للمراجعة فقط. لا يحوّل المصدر أو captions أو التعليقات إلى حقائق مستقلة.",
        "",
        f"- **Source URL:** {analysis.get('source_url')}",
        f"- **Confidence:** {analysis.get('confidence')}",
        "",
        "## Summary",
        "",
        str(analysis.get("summary") or "No summary returned."),
    ]
    for key, title in (
        ("claims", "Claims"),
        ("experiences", "Experiences"),
        ("counterpoints", "Counterpoints"),
        ("verification_needed", "Verification needed"),
        ("citations", "Citations"),
        ("limitations", "Limitations"),
    ):
        lines.extend(["", f"## {title}", ""])
        values = analysis.get(key) or []
        if not isinstance(values, list) or not values:
            lines.append("None returned.")
            continue
        for value in values:
            if isinstance(value, dict):
                lines.append(f"- `{json.dumps(value, ensure_ascii=False, sort_keys=True)}`")
            else:
                lines.append(f"- {value}")
    return "\n".join(lines).rstrip() + "\n"


def write_analysis(analysis: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "analysis.json"
    markdown_path = output_dir / "analysis.md"
    json_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_analysis_markdown(analysis), encoding="utf-8")
    return json_path, markdown_path


__all__ = ["GeminiAPIError", "GeminiAnalyzer", "render_analysis_markdown", "write_analysis"]
