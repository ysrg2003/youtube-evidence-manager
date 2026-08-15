import unittest
from unittest.mock import Mock

from src.gemini_analyzer import GeminiAPIError, GeminiAnalyzer


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload


class GeminiAnalyzerTests(unittest.TestCase):
    def test_missing_key_is_rejected_without_network(self):
        session = Mock()
        analyzer = GeminiAnalyzer("", session=session)
        with self.assertRaisesRegex(GeminiAPIError, "not configured"):
            analyzer.analyze({"source_url": "https://example.test/video"})
        session.post.assert_not_called()

    def test_parses_structured_json_and_preserves_source_url(self):
        session = Mock()
        session.post.return_value = FakeResponse(
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": '{"summary":"Summary","claims":[],"experiences":[],"counterpoints":[],"verification_needed":[],"citations":[],"limitations":[],"confidence":0.4}'
                                }
                            ]
                        }
                    }
                ]
            }
        )
        analyzer = GeminiAnalyzer("test-key", session=session, model="test-model")
        result = analyzer.analyze({"source_url": "https://youtube.test/watch?v=abc"})
        self.assertEqual(result["source_url"], "https://youtube.test/watch?v=abc")
        self.assertEqual(result["summary"], "Summary")
        self.assertEqual(result["citations"], [])
        params = session.post.call_args.kwargs["params"]
        self.assertEqual(params["key"], "test-key")

    def test_api_error_does_not_include_key(self):
        session = Mock()
        session.post.return_value = FakeResponse(
            {"error": {"status": "PERMISSION_DENIED", "message": "invalid project"}},
            status_code=403,
        )
        analyzer = GeminiAnalyzer("test-key", session=session)
        with self.assertRaises(GeminiAPIError) as caught:
            analyzer.analyze({"source_url": "https://example.test/video"})
        self.assertIn("PERMISSION_DENIED", str(caught.exception))
        self.assertNotIn("test-key", str(caught.exception))

    def test_invalid_model_output_is_rejected(self):
        session = Mock()
        session.post.return_value = FakeResponse(
            {"candidates": [{"content": {"parts": [{"text": "not json"}]}}]}
        )
        analyzer = GeminiAnalyzer("test-key", session=session)
        with self.assertRaisesRegex(GeminiAPIError, "valid JSON"):
            analyzer.analyze({"source_url": "https://example.test/video"})


if __name__ == "__main__":
    unittest.main()
