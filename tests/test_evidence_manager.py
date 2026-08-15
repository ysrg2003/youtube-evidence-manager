import json
import tempfile
import unittest
from pathlib import Path

from src.evidence_manager import EvidenceCollector, write_bundle


class FakeAPIClient:
    def __init__(self, comments=None):
        self.comments = comments or []
        self.comment_calls = 0

    def videos(self, video_ids):
        return {
            "items": [
                {
                    "id": video_ids[0],
                    "snippet": {
                        "title": "A test video",
                        "description": "Description",
                        "channelId": "channel-1",
                        "channelTitle": "Test Channel",
                        "publishedAt": "2026-01-01T00:00:00Z",
                    },
                    "contentDetails": {"duration": "PT1M2S"},
                    "statistics": {"viewCount": "42", "likeCount": "7", "commentCount": "1"},
                    "status": {"privacyStatus": "public"},
                }
            ]
        }

    def comment_threads(self, video_id, *, max_results=20, page_token=None):
        self.comment_calls += 1
        return {"items": self.comments, "nextPageToken": None}


class EvidenceManagerTests(unittest.TestCase):
    video_id = "dQw4w9WgXcQ"

    def test_collects_metadata_caption_and_comments(self):
        comment = {
            "id": "thread-1",
            "snippet": {
                "topLevelComment": {
                    "id": "comment-1",
                    "snippet": {
                        "authorDisplayName": "Reader",
                        "publishedAt": "2026-01-02T00:00:00Z",
                        "textDisplay": "Useful comment",
                        "likeCount": 2,
                    },
                }
            },
        }
        collector = EvidenceCollector(
            FakeAPIClient([comment]),
            transcript_fetcher=lambda _: ([{"start": 0, "duration": 1, "text": "Hello world"}], "en"),
        )
        bundle = collector.collect(self.video_id, max_comments=10)
        self.assertEqual(bundle["metadata"]["title"], "A test video")
        self.assertEqual(bundle["caption"]["status"], "available")
        self.assertEqual(bundle["caption"]["segment_count"], 1)
        self.assertEqual(bundle["comments"][0]["label"], "user_generated_comment")
        self.assertEqual(bundle["comments"][0]["text"], "Useful comment")

    def test_caption_failure_is_recorded_without_losing_metadata(self):
        collector = EvidenceCollector(
            FakeAPIClient(),
            transcript_fetcher=lambda _: (_ for _ in ()).throw(RuntimeError("No transcript available")),
        )
        bundle = collector.collect(self.video_id, include_comments=False)
        self.assertEqual(bundle["caption"]["status"], "missing")
        self.assertEqual(bundle["metadata"]["title"], "A test video")
        self.assertIn("comments were skipped", " ".join(bundle["limitations"]))

    def test_bundle_writes_json_and_markdown_without_private_filename_field(self):
        collector = EvidenceCollector(
            FakeAPIClient(),
            transcript_fetcher=lambda _: ([{"start": 0, "duration": 1, "text": "Hello"}], "en"),
        )
        bundle = collector.collect(self.video_id, include_comments=False)
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path, markdown_path = write_bundle(bundle, Path(temp_dir))
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertTrue(json_path.exists())
            self.assertTrue(markdown_path.exists())
            self.assertNotIn("_title_for_filename", payload)
            self.assertIn("Evidence brief", markdown_path.read_text(encoding="utf-8"))

    def test_invalid_video_id_is_rejected(self):
        with self.assertRaises(ValueError):
            EvidenceCollector(FakeAPIClient()).collect("short")


if __name__ == "__main__":
    unittest.main()
