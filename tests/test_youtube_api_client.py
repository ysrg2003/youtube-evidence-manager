import unittest
from unittest.mock import Mock

from src.youtube_api_client import YouTubeAPIError, YouTubeDataClient


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


class YouTubeDataClientTests(unittest.TestCase):
    def make_client(self, payload, status_code=200):
        session = Mock()
        session.get.return_value = FakeResponse(payload, status_code)
        return YouTubeDataClient("test-key", session=session, timeout=1), session

    def test_search_videos_builds_public_video_query(self):
        client, session = self.make_client({"items": []})
        response = client.search_videos("AI-assisted building", max_results=10)
        self.assertEqual(response, {"items": []})
        params = session.get.call_args.kwargs["params"]
        self.assertEqual(params["type"], "video")
        self.assertEqual(params["q"], "AI-assisted building")
        self.assertEqual(params["maxResults"], 10)
        self.assertEqual(params["key"], "test-key")

    def test_videos_batches_ids_in_one_request(self):
        client, session = self.make_client({"items": [{"id": "abc"}]})
        client.videos(["abc", "def"])
        params = session.get.call_args.kwargs["params"]
        self.assertEqual(params["id"], "abc,def")
        self.assertIn("statistics", params["part"])

    def test_comments_use_plain_text_and_bound_results(self):
        client, session = self.make_client({"items": []})
        client.comment_threads("abc", max_results=200)
        params = session.get.call_args.kwargs["params"]
        self.assertEqual(params["maxResults"], 100)
        self.assertEqual(params["textFormat"], "plainText")

    def test_missing_key_is_rejected_without_network(self):
        session = Mock()
        client = YouTubeDataClient("", session=session)
        with self.assertRaisesRegex(YouTubeAPIError, "not configured"):
            client.search_videos("test")
        session.get.assert_not_called()

    def test_api_errors_do_not_include_key(self):
        client, _ = self.make_client(
            {"error": {"message": "bad key", "errors": [{"reason": "keyInvalid"}]}},
            status_code=400,
        )
        with self.assertRaises(YouTubeAPIError) as caught:
            client.search_videos("test")
        self.assertIn("keyInvalid", str(caught.exception))
        self.assertNotIn("test-key", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
