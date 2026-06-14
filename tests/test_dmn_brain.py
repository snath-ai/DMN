"""
Tests for the Lár DMN brain layer:
  - Hippocampus (save_memory, recall, save_warm_memory, warm limit)
"""
import json
import os
from unittest.mock import MagicMock, patch

import pytest

from brain.hippocampus import Hippocampus


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _mock_chromadb_client():
    """Returns a MagicMock that mimics the chromadb.PersistentClient interface."""
    mock_collection = MagicMock()
    mock_collection.count.return_value = 0
    mock_collection.get.return_value = {"ids": []}

    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    return mock_client, mock_collection


# ==================================================================
# Hippocampus
# ==================================================================

class TestHippocampusSaveMemory:
    @patch("brain.hippocampus.chromadb.PersistentClient")
    def test_save_memory_writes_json_journal(self, mock_chroma, tmp_path):
        mock_client, _ = _mock_chromadb_client()
        mock_chroma.return_value = mock_client

        dreams = str(tmp_path / "dreams.json")
        hippo = Hippocampus(dreams_path=dreams, chroma_path=str(tmp_path / "chroma"))

        hippo.save_memory("First memory", [0.1, 0.2], {"source": "test"})

        with open(dreams) as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["content"] == "First memory"

    @patch("brain.hippocampus.chromadb.PersistentClient")
    def test_save_memory_journal_entry_is_hmac_signed(self, mock_chroma, tmp_path):
        """D3 — every durable artifact must carry hmac_hex (v2.3.4+)."""
        import hmac as _hmac
        import hashlib

        mock_client, _ = _mock_chromadb_client()
        mock_chroma.return_value = mock_client

        dreams = str(tmp_path / "dreams.json")
        hippo = Hippocampus(dreams_path=dreams, chroma_path=str(tmp_path / "chroma"))
        hippo.save_memory("Signed memory", [0.1], {"source": "test"})

        with open(dreams) as f:
            data = json.load(f)

        entry = data[0]
        assert "hmac_hex" in entry, "Journal entry must carry hmac_hex (D3)"

        from brain.hippocampus import _JOURNAL_HMAC_KEY
        expected = _hmac.new(
            _JOURNAL_HMAC_KEY,
            "Signed memory".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        assert entry["hmac_hex"] == expected, "hmac_hex signature mismatch"

    @patch("brain.hippocampus.chromadb.PersistentClient")
    def test_save_memory_appends_to_journal(self, mock_chroma, tmp_path):
        mock_client, _ = _mock_chromadb_client()
        mock_chroma.return_value = mock_client

        dreams = str(tmp_path / "dreams.json")
        hippo = Hippocampus(dreams_path=dreams, chroma_path=str(tmp_path / "chroma"))

        hippo.save_memory("Entry 1", [0.1], {})
        hippo.save_memory("Entry 2", [0.2], {})

        with open(dreams) as f:
            data = json.load(f)

        assert len(data) == 2
        assert data[1]["content"] == "Entry 2"

    @patch("brain.hippocampus.chromadb.PersistentClient")
    def test_save_memory_calls_chromadb_add(self, mock_chroma, tmp_path):
        mock_client, mock_collection = _mock_chromadb_client()
        mock_chroma.return_value = mock_client

        hippo = Hippocampus(
            dreams_path=str(tmp_path / "dreams.json"),
            chroma_path=str(tmp_path / "chroma"),
        )
        hippo.save_memory("vector memory", [0.3, 0.4], {})
        mock_collection.add.assert_called_once()

    @patch("brain.hippocampus.chromadb.PersistentClient")
    def test_save_memory_empty_text_is_noop(self, mock_chroma, tmp_path):
        mock_client, mock_collection = _mock_chromadb_client()
        mock_chroma.return_value = mock_client

        dreams = str(tmp_path / "dreams.json")
        hippo = Hippocampus(dreams_path=dreams, chroma_path=str(tmp_path / "chroma"))

        hippo.save_memory("", [], {})
        mock_collection.add.assert_not_called()
        assert not os.path.exists(dreams)


class TestHippocampusRecall:
    @patch("brain.hippocampus.chromadb.PersistentClient")
    def test_recall_formats_results_with_dash_prefix(self, mock_chroma, tmp_path):
        mock_client, mock_collection = _mock_chromadb_client()
        mock_chroma.return_value = mock_client

        mock_collection.query.return_value = {
            "documents": [["doc one", "doc two"]],
            "ids": [["id1", "id2"]],
        }

        hippo = Hippocampus(
            dreams_path=str(tmp_path / "dreams.json"),
            chroma_path=str(tmp_path / "chroma"),
        )

        with patch.object(hippo, "_generate_embedding", return_value=[0.1, 0.2]):
            result = hippo.recall(query="some query", max_memories=2)

        assert "- doc one" in result
        assert "- doc two" in result

    @patch("brain.hippocampus.chromadb.PersistentClient")
    def test_recall_no_embedding_returns_empty(self, mock_chroma, tmp_path):
        mock_client, _ = _mock_chromadb_client()
        mock_chroma.return_value = mock_client

        hippo = Hippocampus(
            dreams_path=str(tmp_path / "dreams.json"),
            chroma_path=str(tmp_path / "chroma"),
        )

        with patch.object(hippo, "_generate_embedding", return_value=None):
            result = hippo.recall(query="test query")

        assert result == ""

    @patch("brain.hippocampus.chromadb.PersistentClient")
    def test_recall_no_query_returns_latest_dream(self, mock_chroma, tmp_path):
        mock_client, _ = _mock_chromadb_client()
        mock_chroma.return_value = mock_client

        dreams = str(tmp_path / "dreams.json")
        json.dump([{"content": "last dream"}], open(dreams, "w"))

        hippo = Hippocampus(dreams_path=dreams, chroma_path=str(tmp_path / "chroma"))
        result = hippo.recall()
        assert result == "last dream"


class TestHippocampusWarmMemory:
    @patch("brain.hippocampus.chromadb.PersistentClient")
    def test_save_warm_memory_calls_collection_add(self, mock_chroma, tmp_path):
        mock_client, mock_collection = _mock_chromadb_client()
        mock_chroma.return_value = mock_client

        hippo = Hippocampus(
            dreams_path=str(tmp_path / "dreams.json"),
            chroma_path=str(tmp_path / "chroma"),
        )
        hippo.save_warm_memory("Warm summary", [0.1, 0.2], {})
        mock_collection.add.assert_called()

    @patch("brain.hippocampus.chromadb.PersistentClient")
    def test_save_warm_memory_prunes_when_over_500(self, mock_chroma, tmp_path):
        mock_client, mock_collection = _mock_chromadb_client()
        mock_chroma.return_value = mock_client
        mock_collection.count.return_value = 501
        mock_collection.get.return_value = {"ids": ["old_id_1", "old_id_2"]}

        hippo = Hippocampus(
            dreams_path=str(tmp_path / "dreams.json"),
            chroma_path=str(tmp_path / "chroma"),
        )
        hippo.save_warm_memory("Overflow entry", [0.5], {})
        mock_collection.delete.assert_called_once_with(ids=["old_id_1"])

    @patch("brain.hippocampus.chromadb.PersistentClient")
    def test_save_warm_memory_empty_text_is_noop(self, mock_chroma, tmp_path):
        mock_client, mock_collection = _mock_chromadb_client()
        mock_chroma.return_value = mock_client

        hippo = Hippocampus(
            dreams_path=str(tmp_path / "dreams.json"),
            chroma_path=str(tmp_path / "chroma"),
        )
        hippo.save_warm_memory("", [0.1], {})
        mock_collection.add.assert_not_called()

    @patch("brain.hippocampus.chromadb.PersistentClient")
    def test_recall_warm_formats_results(self, mock_chroma, tmp_path):
        mock_client, mock_collection = _mock_chromadb_client()
        mock_chroma.return_value = mock_client
        mock_collection.query.return_value = {"documents": [["Warm insight"]]}

        hippo = Hippocampus(
            dreams_path=str(tmp_path / "dreams.json"),
            chroma_path=str(tmp_path / "chroma"),
        )
        with patch.object(hippo, "_generate_embedding", return_value=[0.1]):
            result = hippo.recall_warm(query="insight query")

        assert "Warm insight" in result

    @patch("brain.hippocampus.chromadb.PersistentClient")
    def test_recall_warm_no_query_returns_empty(self, mock_chroma, tmp_path):
        mock_client, _ = _mock_chromadb_client()
        mock_chroma.return_value = mock_client

        hippo = Hippocampus(
            dreams_path=str(tmp_path / "dreams.json"),
            chroma_path=str(tmp_path / "chroma"),
        )
        assert hippo.recall_warm(query=None) == ""
