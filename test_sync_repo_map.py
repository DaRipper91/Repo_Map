import unittest
from unittest.mock import patch, MagicMock
import json
import sys
from pathlib import Path

# Ensure the current directory is in sys.path so we can import sync_repo_map
sys.path.append('.')
import sync_repo_map

class TestLoadHashes(unittest.TestCase):

    @patch('sync_repo_map.PREV_HASH')
    def test_load_hashes_file_not_exists(self, mock_prev_hash):
        # Configure the mock to simulate file not existing
        mock_prev_hash.exists.return_value = False

        result = sync_repo_map.load_hashes()

        self.assertEqual(result, {})
        mock_prev_hash.exists.assert_called_once()

    @patch('sync_repo_map.PREV_HASH')
    def test_load_hashes_valid_json(self, mock_prev_hash):
        # Configure the mock to simulate valid JSON content
        data = {"repo1": "hash1", "repo2": "hash2"}
        mock_prev_hash.exists.return_value = True
        mock_prev_hash.read_text.return_value = json.dumps(data)

        result = sync_repo_map.load_hashes()

        self.assertEqual(result, data)
        mock_prev_hash.exists.assert_called_once()
        mock_prev_hash.read_text.assert_called_once()

    @patch('sync_repo_map.PREV_HASH')
    def test_load_hashes_invalid_json(self, mock_prev_hash):
        # Configure the mock to simulate invalid JSON content
        mock_prev_hash.exists.return_value = True
        mock_prev_hash.read_text.return_value = "invalid json"

        result = sync_repo_map.load_hashes()

        self.assertEqual(result, {})
        mock_prev_hash.exists.assert_called_once()
        mock_prev_hash.read_text.assert_called_once()

if __name__ == '__main__':
    unittest.main()
