"""Collect and render reviewable evidence bundles for public YouTube videos."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any, Callable, Iterable

from src.youtube_api_client import YouTubeDataClient, YouTubeAPIError


VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")
SCHEMA_VERSION = "0.1"


class EvidenceCollectionError(RuntimeError):
    """Raised when a required evidence collection step cannot complete."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _source_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def _safe_filename(value: str, max_length: int = 60) -> str:
    value = re.sub(r'[\\/*?:"<>|#]', "", value).strip()
    value = re.sub(r"\s+", " ", value)
    return value[:max_length].rstrip(" ._") or "video"


def _caption_text(segments: Iterable[dict[str, Any]]) -> str:
    return "\n".join(str(segment.get("text", "")).strip() for segment in segments if str(segment.get("text", "")).strip())


def _comment_text(item: dict[str, Any]) -> dict[str, Any] | None:
    snippet = item.get("snippet") or {}
    top = snippet.get("topLevelComment") or {}
    top_snippet = top.get("snippet") or {}
    text = str(top_snippet.get("textDisplay") or top_snippet.get("textOriginal") or "").strip()
    if not text:
        return None
    replies = []
    for reply in (item.get("replies") or {}).get("comments", []) or []:
        reply_snippet = reply.get("snippet") or {}
        reply_text = str(reply_snippet.get("textDisplay") or reply_snippet.get("textOriginal") or "").strip()
        if reply_text:
            replies.append(
                {
                    "id": reply.get("id"),
                    "author": reply_snippet.get("authorDisplayName"),
                    "published_at": reply_snippet.get("publishedAt"),
                    "text": reply_text,
                    "label": "user_generated_comment",
                }
            )
    return {
        "id": top.get("id") or item.get("id"),
        "author": top_snippet.get("authorDisplayName"),
        "published_at": top_snippet.get("publishedAt"),
        "like_count": top_snippet.get("likeCount"),
        "text": text,
        "label": "user_generated_comment",
        "replies": replies,
    }


def _metadata(item: dict[str, Any]) -> dict[str, Any]:
    snippet = item.get("snippet") or {}
    details = item.get("contentDetails") or {}
    stats = item.get("statistics") or {}
    status = item.get("status") or {}
    return {
        "title": snippet.get("title"),
        "description": snippet.get("description"),
        "channel_id": snippet.get("channelId"),
        "channel_title": snippet.get("channelTitle"),
        "published_at": snippet.get("publishedAt"),
        "duration": details.get("duration"),
        "view_count": _as_int_or_none(stats.get("viewCount")),
        "like_count": _as_int_or_none(stats.get("likeCount")),
        "comment_count": _as_int_or_none(stats.get("commentCount")),
        "privacy_status": status.get("privacyStatus"),
    }


def _as_int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@dataclass
class EvidenceCollector:
    """Collect evidence without publishing or downloading the source video."""

    api_client: YouTubeDataClient
    transcript_fetcher: Callable[[str], tuple[list[dict[str, Any]], str]] | None = None

    def _fetch_captions(self, video_id: str) -> tuple[dict[str, Any], list[str]]:
        if self.transcript_fetcher is None:
            try:
                from youtube_subtitles_translator import fetch_transcript
            except Exception as exc:  # pragma: no cover - dependency/environment failure
                return (
                    {"status": "error", "language": None, "is_generated": None, "segment_count": 0, "text_sha256": "", "text": "", "error": str(exc)},
                    [f"caption adapter could not be loaded: {exc}"],
                )
            fetcher = fetch_transcript
        else:
            fetcher = self.transcript_fetcher

        try:
            segments, language = fetcher(video_id)
            text = _caption_text(segments)
            if not text:
                return (
                    {"status": "missing", "language": language, "is_generated": None, "segment_count": 0, "text_sha256": "", "text": ""},
                    ["caption transcript was empty"],
                )
            return (
                {
                    "status": "available",
                    "language": language,
                    "is_generated": None,
                    "segment_count": len(segments),
                    "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    "text": text,
                },
                [],
            )
        except Exception as exc:
            message = str(exc)
            status = "missing" if "No transcript" in message or "disabled" in message.lower() else "error"
            return (
                {"status": status, "language": None, "is_generated": None, "segment_count": 0, "text_sha256": "", "text": "", "error": message},
                [f"caption collection: {message}"],
            )

    def _fetch_comments(self, video_id: str, max_comments: int, max_pages: int) -> tuple[list[dict[str, Any]], list[str]]:
        comments: list[dict[str, Any]] = []
        limitations: list[str] = []
        if max_comments == 0:
            return comments, ["comment collection limit was set to zero"]
        page_token: str | None = None
        for _ in range(max(1, max_pages)):
            try:
                response = self.api_client.comment_threads(
                    video_id,
                    max_results=min(100, max(1, max_comments - len(comments))),
                    page_token=page_token,
                )
            except YouTubeAPIError as exc:
                message = str(exc)
                if "commentsDisabled" in message or "disabled" in message.lower():
                    limitations.append("comments are disabled or unavailable for this video")
                else:
                    limitations.append(f"comment collection: {message}")
                break
            for item in response.get("items", []) or []:
                parsed = _comment_text(item)
                if parsed:
                    comments.append(parsed)
                    if len(comments) >= max_comments:
                        break
            if len(comments) >= max_comments:
                break
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return comments, limitations

    def collect(
        self,
        video_id: str,
        *,
        max_comments: int = 100,
        max_comment_pages: int = 5,
        include_comments: bool = True,
    ) -> dict[str, Any]:
        video_id = video_id.strip()
        if not VIDEO_ID_PATTERN.fullmatch(video_id):
            raise ValueError("video_id must be an 11-character YouTube video ID")

        try:
            response = self.api_client.videos([video_id])
        except YouTubeAPIError as exc:
            raise EvidenceCollectionError(f"metadata collection failed: {exc}") from exc
        items = response.get("items", []) or []
        if not items:
            raise EvidenceCollectionError("YouTube returned no metadata for this video ID")

        caption, limitations = self._fetch_captions(video_id)
        comments: list[dict[str, Any]] = []
        if include_comments:
            comments, comment_limitations = self._fetch_comments(video_id, max_comments, max_comment_pages)
            limitations.extend(comment_limitations)
        else:
            limitations.append("comments were skipped by the operator")

        metadata = _metadata(items[0])
        title = metadata.get("title") or video_id
        return {
            "schema_version": SCHEMA_VERSION,
            "source_url": _source_url(video_id),
            "video_id": video_id,
            "metadata": metadata,
            "caption": caption,
            "comments": comments,
            "evidence_labels": ["creator_claim", "caption_text", "user_generated_comments"],
            "limitations": limitations,
            "collected_at": _utc_now(),
            "collection": {
                "metadata_source": "YouTube Data API v3",
                "caption_source": "youtube-transcript-api",
                "comment_count_collected": len(comments),
            },
            "_title_for_filename": title,
        }


def render_markdown(bundle: dict[str, Any]) -> str:
    metadata = bundle.get("metadata") or {}
    caption = bundle.get("caption") or {}
    lines = [
        f"# Evidence brief: {metadata.get('title') or bundle.get('video_id')}",
        "",
        "> هذا التقرير يجمع مواد قابلة للمراجعة؛ لا يعتبر كلام المتحدث أو التعليقات حقيقة مستقلة، ولا ينشر أي محتوى تلقائيًا.",
        "",
        f"- **Source URL:** {bundle.get('source_url')}",
        f"- **Video ID:** `{bundle.get('video_id')}`",
        f"- **Collected at:** {bundle.get('collected_at')}",
        f"- **Schema:** `{bundle.get('schema_version')}`",
        "",
        "## Metadata",
        "",
        "| Field | Value |",
        "|---|---|",
    ]
    for key, label in (
        ("channel_title", "Channel"),
        ("channel_id", "Channel ID"),
        ("published_at", "Published at"),
        ("duration", "Duration"),
        ("view_count", "Views"),
        ("like_count", "Likes"),
        ("comment_count", "Comments on YouTube"),
        ("privacy_status", "Privacy status"),
    ):
        lines.append(f"| {label} | {metadata.get(key)} |")

    lines.extend(
        [
            "",
            "## Captions",
            "",
            f"- **Status:** `{caption.get('status')}`",
            f"- **Language:** `{caption.get('language')}`",
            f"- **Generated:** `{caption.get('is_generated')}`",
            f"- **Segments:** `{caption.get('segment_count')}`",
            f"- **Text SHA-256:** `{caption.get('text_sha256')}`",
        ]
    )
    if caption.get("text"):
        lines.extend(["", "### Caption text", "", caption["text"]])
    if caption.get("error"):
        lines.extend(["", f"> Caption note: {caption['error']}"])

    lines.extend(["", "## Public comments", ""])
    comments = bundle.get("comments") or []
    if not comments:
        lines.append("No public comments were collected.")
    for index, comment in enumerate(comments, start=1):
        author = escape(str(comment.get("author") or "Unknown author"))
        text = escape(str(comment.get("text") or "")).replace("\n", "  \n")
        lines.extend([f"### {index}. {author}", "", f"> {text}", ""])
        for reply in comment.get("replies") or []:
            lines.append(f"- Reply by **{escape(str(reply.get('author') or 'Unknown author'))}**: {escape(str(reply.get('text') or ''))}")

    lines.extend(["", "## Evidence labels", "", ", ".join(f"`{label}`" for label in bundle.get("evidence_labels") or [])])
    lines.extend(["", "## Limitations", ""])
    limitations = bundle.get("limitations") or []
    if limitations:
        lines.extend(f"- {limitation}" for limitation in limitations)
    else:
        lines.append("No collection limitation was recorded.")
    return "\n".join(lines).rstrip() + "\n"


def write_bundle(bundle: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    title = _safe_filename(str(bundle.get("_title_for_filename") or bundle.get("video_id")))
    video_id = bundle["video_id"]
    bundle_dir = output_dir / f"{title}_{video_id}"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    clean_bundle = {key: value for key, value in bundle.items() if not key.startswith("_")}
    json_path = bundle_dir / "evidence.json"
    markdown_path = bundle_dir / "evidence.md"
    json_path.write_text(json.dumps(clean_bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(clean_bundle), encoding="utf-8")
    return json_path, markdown_path


def collect_and_write(
    video_id: str,
    output_dir: Path,
    *,
    max_comments: int = 100,
    max_comment_pages: int = 5,
    include_comments: bool = True,
    api_key: str | None = None,
) -> tuple[dict[str, Any], tuple[Path, Path]]:
    collector = EvidenceCollector(YouTubeDataClient(api_key=api_key))
    bundle = collector.collect(
        video_id,
        max_comments=max_comments,
        max_comment_pages=max_comment_pages,
        include_comments=include_comments,
    )
    return bundle, write_bundle(bundle, output_dir)


__all__ = [
    "EvidenceCollectionError",
    "EvidenceCollector",
    "collect_and_write",
    "render_markdown",
    "write_bundle",
]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit("Use python -m src.evidence_cli")


# Keep the import visible for type-checkers and callers that used the old module.
_ = escape
