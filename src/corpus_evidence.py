"""Bounded corpus evidence runner for the System Before Scale articles."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.evidence_manager import EvidenceCollectionError, EvidenceCollector, write_bundle
from src.gemini_analyzer import GeminiAPIError, GeminiAnalyzer, write_analysis
from src.youtube_api_client import YouTubeAPIError, YouTubeDataClient

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "before", "by", "can", "for",
    "from", "how", "i", "in", "into", "is", "it", "my", "of", "on", "or", "the",
    "that", "this", "to", "when", "why", "with", "you", "your",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]{3,}", value.lower())
        if token not in STOPWORDS
    }


def candidate_score(article: dict[str, Any], item: dict[str, Any]) -> tuple[int, int]:
    article_tokens = tokens(f"{article.get('title', '')} {article.get('section', '')}")
    snippet = item.get("snippet") or {}
    title = str(snippet.get("title") or "")
    description = str(snippet.get("description") or "")
    overlap = len(article_tokens & tokens(f"{title} {description}"))
    exact_title_bonus = 2 if tokens(title) & tokens(str(article.get("title") or "")) else 0
    return overlap + exact_title_bonus, overlap


def choose_candidate(article: dict[str, Any], items: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    candidates = []
    for item in items:
        video_id = (item.get("id") or {}).get("videoId")
        if not video_id:
            continue
        snippet = item.get("snippet") or {}
        score, overlap = candidate_score(article, item)
        candidates.append(
            {
                "video_id": video_id,
                "title": snippet.get("title"),
                "channel_title": snippet.get("channelTitle"),
                "published_at": snippet.get("publishedAt"),
                "description": snippet.get("description"),
                "score": score,
                "token_overlap": overlap,
                "source_url": f"https://www.youtube.com/watch?v={video_id}",
            }
        )
    candidates.sort(key=lambda value: (value["score"], value["token_overlap"]), reverse=True)
    return (candidates[0] if candidates else None), candidates


def is_quota_error(message: str) -> bool:
    lowered = message.lower()
    return "quotaexceeded" in lowered or "quota exceeded" in lowered or "daily limit" in lowered


def load_manifest(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    articles = data.get("articles") if isinstance(data, dict) else None
    if not isinstance(articles, list) or not articles:
        raise ValueError("manifest must contain a non-empty articles list")
    return articles


def write_summary(output_dir: Path, results: list[dict[str, Any]], stopped_reason: str | None) -> None:
    summary = {
        "schema_version": "1.0",
        "collected_at": utc_now(),
        "stopped_reason": stopped_reason,
        "counts": {},
        "results": results,
    }
    counts: dict[str, int] = {}
    for result in results:
        status = str(result.get("status"))
        counts[status] = counts.get(status, 0) + 1
    summary["counts"] = counts
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "corpus_results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# YouTube corpus evidence run",
        "",
        f"Collected at: `{summary['collected_at']}`",
        f"Stopped reason: `{stopped_reason or 'none'}`",
        "",
        "| Status | Count |",
        "|---|---:|",
    ]
    lines.extend(f"| `{key}` | {value} |" for key, value in sorted(counts.items()))
    lines.extend(["", "## Article results", "", "| ID | Section | Status | Selected video | Caption | Comments | Analysis |", "|---:|---|---|---|---|---:|---|"])
    for result in results:
        lines.append(
            "| {article_id} | {section} | `{status}` | {video_id} | `{caption_status}` | {comments} | `{analysis}` |".format(
                article_id=result.get("article_id"),
                section=result.get("section", ""),
                status=result.get("status"),
                video_id=result.get("selected_video_id") or "-",
                caption_status=result.get("caption_status") or "-",
                comments=result.get("comment_count", 0),
                analysis=result.get("analysis_status") or "-",
            )
        )
    if stopped_reason:
        lines.extend(["", f"> The run stopped before completing the manifest: `{stopped_reason}`"])
    (output_dir / "corpus_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    articles = load_manifest(Path(args.manifest))[: args.max_articles]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    state_path = output_dir / "corpus_state.json"
    state: dict[str, Any] = {}
    if args.resume and state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
    results: list[dict[str, Any]] = []
    client = YouTubeDataClient()
    collector = EvidenceCollector(client)
    analyzer = GeminiAnalyzer(model=args.gemini_model) if args.analyze else None
    stopped_reason: str | None = None

    for article in articles:
        article_id = int(article["article_id"])
        key = str(article_id)
        previous = state.get(key)
        if args.resume and isinstance(previous, dict) and previous.get("status") in {"complete", "partial", "no_search_results"}:
            results.append(previous)
            continue

        base = {
            "article_id": article_id,
            "title": article.get("title"),
            "section": article.get("section"),
            "filename": article.get("filename"),
            "query": article.get("youtube_query"),
            "started_at": utc_now(),
        }
        try:
            search_page = client.search_videos(str(article["youtube_query"]), max_results=args.search_results)
        except YouTubeAPIError as exc:
            message = str(exc)
            result = {**base, "status": "failed", "error": message}
            results.append(result)
            state[key] = result
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            if is_quota_error(message):
                stopped_reason = f"YouTube search quota error at article {article_id}"
                break
            continue

        selected, candidates = choose_candidate(article, search_page.get("items", []) or [])
        base["candidates"] = candidates[: args.search_results]
        if selected is None:
            result = {**base, "status": "no_search_results", "finished_at": utc_now()}
            results.append(result)
            state[key] = result
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            continue

        base["selected_video_id"] = selected["video_id"]
        base["selected_video_title"] = selected.get("title")
        bundle_dir = output_dir / f"article_{article_id:03d}"
        try:
            bundle = collector.collect(
                selected["video_id"],
                max_comments=args.max_comments,
                max_comment_pages=args.max_comment_pages,
                include_comments=not args.skip_comments,
            )
            bundle["article_context"] = {
                "article_id": article_id,
                "title": article.get("title"),
                "subtitle": article.get("subtitle"),
                "section": article.get("section"),
                "filename": article.get("filename"),
                "labels": article.get("labels", []),
                "search_description": article.get("search_description"),
                "search_query": article.get("youtube_query"),
                "candidate_score": selected.get("score"),
            }
            json_path, markdown_path = write_bundle(bundle, bundle_dir)
            result = {
                **base,
                "status": "complete" if bundle["caption"].get("status") == "available" else "partial",
                "finished_at": utc_now(),
                "evidence_json": str(json_path),
                "evidence_markdown": str(markdown_path),
                "caption_status": bundle["caption"].get("status"),
                "comment_count": len(bundle.get("comments") or []),
                "limitations": bundle.get("limitations") or [],
                "analysis_status": "not_requested",
            }
            if analyzer is not None:
                try:
                    analysis = analyzer.analyze(bundle)
                    analysis_json, analysis_markdown = write_analysis(analysis, markdown_path.parent)
                    result["analysis_status"] = "complete"
                    result["analysis_json"] = str(analysis_json)
                    result["analysis_markdown"] = str(analysis_markdown)
                except GeminiAPIError as exc:
                    result["analysis_status"] = "failed"
                    result["analysis_error"] = str(exc)
                    if is_quota_error(str(exc)):
                        stopped_reason = f"Gemini quota error at article {article_id}"
                        results.append(result)
                        state[key] = result
                        break
        except EvidenceCollectionError as exc:
            message = str(exc)
            result = {**base, "status": "failed", "finished_at": utc_now(), "error": message}
            if is_quota_error(message):
                stopped_reason = f"YouTube quota error at article {article_id}"
            results.append(result)
            state[key] = result
            if stopped_reason:
                break
            state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            continue

        results.append(result)
        state[key] = result
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if stopped_reason:
            break

    write_summary(output_dir, results, stopped_reason)
    return 1 if stopped_reason else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collect bounded YouTube evidence for the 50-article corpus.")
    parser.add_argument("--manifest", default="testdata/corpus_manifest.json")
    parser.add_argument("--output-dir", default="artifacts/corpus-evidence")
    parser.add_argument("--max-articles", type=int, default=50)
    parser.add_argument("--search-results", type=int, default=5)
    parser.add_argument("--max-comments", type=int, default=10)
    parser.add_argument("--max-comment-pages", type=int, default=1)
    parser.add_argument("--skip-comments", action="store_true")
    parser.add_argument("--analyze", action="store_true")
    parser.add_argument("--gemini-model", default=None)
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    parser.set_defaults(resume=True)
    return parser


if __name__ == "__main__":
    raise SystemExit(run(build_parser().parse_args()))
