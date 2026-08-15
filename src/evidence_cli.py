"""Command-line entry point for the YouTube evidence manager."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.evidence_manager import EvidenceCollectionError, EvidenceCollector, write_bundle
from src.gemini_analyzer import GeminiAPIError, GeminiAnalyzer, write_analysis
from src.youtube_api_client import YouTubeDataClient


VIDEO_ID_PATTERN = __import__("re").compile(r"^[A-Za-z0-9_-]{11}$")


def extract_video_id(value: str) -> str | None:
    value = value.strip()
    if VIDEO_ID_PATTERN.fullmatch(value):
        return value
    try:
        parsed = urlparse(value)
    except ValueError:
        return None
    hostname = (parsed.hostname or "").lower()
    if hostname.startswith("www."):
        hostname = hostname[4:]
    if hostname.startswith("m."):
        hostname = hostname[2:]
    if hostname == "youtu.be":
        candidate = parsed.path.strip("/").split("/")[0]
        return candidate if VIDEO_ID_PATTERN.fullmatch(candidate) else None
    if hostname in {"youtube.com", "youtube-nocookie.com"}:
        path = [part for part in parsed.path.split("/") if part]
        if path and path[0] in {"embed", "shorts", "v", "e"} and len(path) > 1:
            candidate = path[1]
            return candidate if VIDEO_ID_PATTERN.fullmatch(candidate) else None
        candidate = parse_qs(parsed.query).get("v", [""])[0]
        return candidate if VIDEO_ID_PATTERN.fullmatch(candidate) else None
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Collect reviewable YouTube metadata, captions, and public comments."
    )
    parser.add_argument("video", help="YouTube video URL or bare 11-character video ID")
    parser.add_argument("--output-dir", default="artifacts/evidence", help="Directory for evidence bundles")
    parser.add_argument("--max-comments", type=int, default=100, help="Maximum top-level comments to collect")
    parser.add_argument("--max-comment-pages", type=int, default=5, help="Maximum comment API pages")
    parser.add_argument("--skip-comments", action="store_true", help="Skip public comment collection")
    parser.add_argument("--analyze", action="store_true", help="Run optional Gemini analysis after collection")
    parser.add_argument("--gemini-model", default=None, help="Gemini model override; otherwise GEMINI_MODEL is used")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    video_id = extract_video_id(args.video)
    if not video_id:
        print("[ERROR] Input is not a valid YouTube video URL or 11-character video ID.", file=sys.stderr)
        return 2
    if args.max_comments < 0:
        print("[ERROR] --max-comments must be zero or greater.", file=sys.stderr)
        return 2
    if args.max_comment_pages < 1:
        print("[ERROR] --max-comment-pages must be at least 1.", file=sys.stderr)
        return 2

    try:
        collector = EvidenceCollector(YouTubeDataClient())
        bundle = collector.collect(
            video_id,
            max_comments=args.max_comments,
            max_comment_pages=args.max_comment_pages,
            include_comments=not args.skip_comments,
        )
        json_path, markdown_path = write_bundle(bundle, Path(args.output_dir))
        print(f"Evidence JSON: {json_path}")
        print(f"Evidence Markdown: {markdown_path}")

        if args.analyze:
            analysis = GeminiAnalyzer(model=args.gemini_model).analyze(bundle)
            analysis_json, analysis_markdown = write_analysis(analysis, markdown_path.parent)
            print(f"Analysis JSON: {analysis_json}")
            print(f"Analysis Markdown: {analysis_markdown}")
    except (EvidenceCollectionError, GeminiAPIError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # keep CLI failures visible without dumping secrets
        print(f"[ERROR] Unexpected failure: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
