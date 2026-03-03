import unittest
from unittest.mock import patch
import json
import base64
import sync_changelogs

class TestFetchChangelog(unittest.TestCase):

    @patch('sync_changelogs.run')
    def test_fetch_changelog_invalid_json(self, mock_run):
        # Mock run to return invalid JSON
        mock_run.return_value = "invalid json"

        result = sync_changelogs.fetch_changelog("user", "repo")

        self.assertIsNone(result)
        mock_run.assert_called_once()

    @patch('sync_changelogs.run')
    def test_fetch_changelog_valid_json(self, mock_run):
        # Mock run to return valid JSON with base64 content
        content = "Changelog content"
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        mock_run.return_value = json.dumps({"content": encoded_content})

        result = sync_changelogs.fetch_changelog("user", "repo")

        self.assertEqual(result, content)
        mock_run.assert_called_once()

    @patch('sync_changelogs.run')
    def test_fetch_changelog_run_returns_none(self, mock_run):
        # Mock run to return None
        mock_run.return_value = None

        result = sync_changelogs.fetch_changelog("user", "repo")

        self.assertIsNone(result)
        mock_run.assert_called_once()

if __name__ == '__main__':
    unittest.main()
