"""Small, testable client for public YouTube Data API v3 reads.

This module intentionally does not implement publishing, uploads, or caption
track downloads. It returns public metadata and comments only.
"""
from __future__ import annotations

import os
from typing import Any, Iterable

import requests
from dotenv import load_dotenv


load_dotenv()

API_ROOT = "https://www.googleapis.com/youtube/v3"
DEFAULT_TIMEOUT = 30.0


class YouTubeAPIError(RuntimeError):
    """A sanitized YouTube API failure."""


class YouTubeDataClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        session: requests.Session | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.api_key = (api_key or os.getenv("YOUTUBE_API_KEY", "")).strip()
        self.session = session or requests.Session()
        self.timeout = timeout

    def _get(self, resource: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise YouTubeAPIError("YOUTUBE_API_KEY is not configured")
        request_params = dict(params)
        request_params["key"] = self.api_key
        response = self.session.get(
            f"{API_ROOT}/{resource.lstrip('/')}",
            params=request_params,
            timeout=self.timeout,
        )
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if response.status_code >= 400:
            error = payload.get("error", {}) if isinstance(payload, dict) else {}
            errors = error.get("errors", []) if isinstance(error, dict) else []
            reason = errors[0].get("reason") if errors and isinstance(errors[0], dict) else None
            message = error.get("message") if isinstance(error, dict) else None
            detail = ": ".join(str(value) for value in (reason, message) if value)
            raise YouTubeAPIError(f"YouTube API HTTP {response.status_code}{': ' + detail if detail else ''}")
        if not isinstance(payload, dict):
            raise YouTubeAPIError("YouTube API returned a non-object response")
        return payload

    def search_videos(self, query: str, *, max_results: int = 10, page_token: str | None = None) -> dict[str, Any]:
        query = query.strip()
        if not query:
            raise ValueError("query must not be empty")
        params: dict[str, Any] = {
            "part": "snippet",
            "type": "video",
            "q": query,
            "maxResults": max(1, min(int(max_results), 50)),
            "order": "relevance",
        }
        if page_token:
            params["pageToken"] = page_token
        return self._get("search", params)

    def videos(self, video_ids: Iterable[str]) -> dict[str, Any]:
        ids = [str(video_id).strip() for video_id in video_ids if str(video_id).strip()]
        if not ids:
            raise ValueError("video_ids must contain at least one ID")
        if len(ids) > 50:
            raise ValueError("YouTube accepts at most 50 video IDs per videos.list request")
        return self._get(
            "videos",
            {
                "part": "snippet,contentDetails,statistics,status",
                "id": ",".join(ids),
            },
        )

    def comment_threads(
        self,
        video_id: str,
        *,
        max_results: int = 20,
        page_token: str | None = None,
        order: str = "relevance",
    ) -> dict[str, Any]:
        video_id = video_id.strip()
        if not video_id:
            raise ValueError("video_id must not be empty")
        params: dict[str, Any] = {
            "part": "snippet,replies",
            "videoId": video_id,
            "maxResults": max(1, min(int(max_results), 100)),
            "textFormat": "plainText",
            "order": order if order in {"time", "relevance"} else "relevance",
        }
        if page_token:
            params["pageToken"] = page_token
        return self._get("commentThreads", params)
