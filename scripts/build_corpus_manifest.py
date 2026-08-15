from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def build(index: Path, corpus_dir: Path, output: Path) -> None:
    row_pattern = re.compile(r'^\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*`([^`]+)`\s*\|$')
    rows = []
    for line in index.read_text(encoding='utf-8').splitlines():
        match = row_pattern.match(line)
        if not match:
            continue
        map_id, title, section, filename = match.groups()
        article_path = corpus_dir / filename
        article_text = article_path.read_text(encoding='utf-8') if article_path.exists() else ''
        subtitle_match = re.search(r'^\*\*Subtitle:\*\*\s*(.+)$', article_text, flags=re.MULTILINE)
        description_match = re.search(r'^\*\*Search description:\*\*\s*(.+)$', article_text, flags=re.MULTILINE)
        labels_match = re.search(r'^\*\*Suggested labels:\*\*\s*(.+)$', article_text, flags=re.MULTILINE)
        subtitle = subtitle_match.group(1).strip() if subtitle_match else ''
        search_description = description_match.group(1).strip() if description_match else ''
        labels = [item.strip() for item in (labels_match.group(1).split(',') if labels_match else []) if item.strip()]
        query = re.sub(r'[^A-Za-z0-9\s&-]', ' ', title)
        query = re.sub(r'\s+', ' ', query).strip()
        rows.append({
            'article_id': int(map_id),
            'title': title,
            'subtitle': subtitle,
            'section': section,
            'filename': filename,
            'labels': labels,
            'search_description': search_description,
            'youtube_query': query,
            'evidence_policy': 'discover_public_video_then_collect_metadata_caption_and_limited_comments',
        })
    if len(rows) != 50:
        raise SystemExit(f'Expected 50 article rows, found {len(rows)}')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({'schema_version': '1.0', 'articles': rows}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'wrote {len(rows)} articles to {output}')


def main() -> int:
    parser = argparse.ArgumentParser(description='Build the 50-article YouTube evidence manifest.')
    parser.add_argument('--index', type=Path, required=True)
    parser.add_argument('--corpus-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('testdata/corpus_manifest.json'))
    args = parser.parse_args()
    build(args.index, args.corpus_dir, args.output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
