"""
Tests for the Lár DMN brain layer:
  - Hippocampus (save_memory, recall, save_warm_memory, warm limit)
  - PrefrontalNode (return type contract, compression, empty-input bypass)
  - MemoryTiers (hot rolling buffer — tested for DMN-specific behaviour)
"""
import json
import sys
import os
from unittest.mock import MagicMock, patch, call

import pytest

# conftest.py adds ../src to sys.path; nothing extra needed for lar.* or brain.*
from brain.hippocampus import Hippocampus
from brain.prefrontal import PrefrontalNode
from brain.memory_tiers import MemoryTiers
from lar.node import BaseNode
from lar.state import GraphState


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

        # Verify the signature matches the content
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


# ==================================================================
# PrefrontalNode — return type contract and compression behaviour
# ==================================================================

class TestPrefrontalNode:
    def _make_pfc(self, next_node=None):
        mock_hippo = MagicMock()
        mock_hippo.recall.return_value = "Cold chunk 1\nCold chunk 2"
        mock_hippo.recall_warm.return_value = "Warm summary"
        return PrefrontalNode(hippocampus=mock_hippo, next_node=next_node), mock_hippo

    def test_execute_returns_none_when_next_node_is_none(self):
        pfc, _ = self._make_pfc(next_node=None)
        with patch("brain.prefrontal.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={"response": "Summary."}),
            )
            mock_post.return_value.raise_for_status.return_value = None
            state = GraphState({"user_input": "hello"})
            result = pfc.execute(state)
        assert result is None

    def test_execute_returns_next_node(self):
        mock_next = MagicMock(spec=BaseNode)
        pfc, _ = self._make_pfc(next_node=mock_next)
        with patch("brain.prefrontal.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={"response": "Summary."}),
            )
            mock_post.return_value.raise_for_status.return_value = None
            state = GraphState({"user_input": "hello"})
            result = pfc.execute(state)
        assert result is mock_next

    def test_execute_not_returning_graph_state(self):
        """PrefrontalNode.execute must never return a GraphState object."""
        pfc, _ = self._make_pfc()
        with patch("brain.prefrontal.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={"response": "ok"}),
            )
            mock_post.return_value.raise_for_status.return_value = None
            state = GraphState({"user_input": "test"})
            result = pfc.execute(state)
        assert not isinstance(result, GraphState)

    def test_execute_sets_compressed_memory_in_state(self):
        pfc, _ = self._make_pfc()
        with patch("brain.prefrontal.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={"response": "Compressed."}),
            )
            mock_post.return_value.raise_for_status.return_value = None
            state = GraphState({"user_input": "query"})
            pfc.execute(state)
        assert state.get("compressed_memory") == "Compressed."

    def test_execute_empty_user_input_bypasses_llm(self):
        pfc, _ = self._make_pfc()
        with patch("brain.prefrontal.requests.post") as mock_post:
            state = GraphState({"user_input": ""})
            result = pfc.execute(state)
            mock_post.assert_not_called()
        assert result is None

    def test_execute_no_memories_bypasses_llm(self):
        mock_hippo = MagicMock()
        mock_hippo.recall.return_value = ""
        mock_hippo.recall_warm.return_value = ""
        pfc = PrefrontalNode(hippocampus=mock_hippo)

        with patch("brain.prefrontal.requests.post") as mock_post:
            state = GraphState({"user_input": "hello"})
            pfc.execute(state)
            mock_post.assert_not_called()

    def test_execute_compression_failure_sets_empty_string(self):
        pfc, _ = self._make_pfc()
        with patch("brain.prefrontal.requests.post") as mock_post:
            mock_post.side_effect = ConnectionError("Ollama down")
            state = GraphState({"user_input": "query"})
            pfc.execute(state)
        assert state.get("compressed_memory") == ""

    def test_execute_calls_recall_with_user_input(self):
        pfc, mock_hippo = self._make_pfc()
        with patch("brain.prefrontal.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={"response": "ok"}),
            )
            mock_post.return_value.raise_for_status.return_value = None
            state = GraphState({"user_input": "my query"})
            pfc.execute(state)
        mock_hippo.recall.assert_called_once_with(query="my query", max_memories=10)
        mock_hippo.recall_warm.assert_called_once_with(query="my query", max_memories=3)


# ==================================================================
# MemoryTiers — DMN-specific hot memory behaviour
# ==================================================================

class TestMemoryTiersDMN:
    def test_hot_memory_bounded_to_configured_size(self):
        tiers = MemoryTiers(hot_memory_size=3)
        lines = [f'{{"role": "user", "content": "msg {i}"}}\n' for i in range(8)]

        mock_file = MagicMock()
        mock_file.__enter__ = lambda s: s
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_file.readlines.return_value = lines

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", return_value=mock_file):
                history = tiers.get_hot_memory("dummy.jsonl")

        result_lines = [l for l in history.split("\n") if l.strip()]
        assert len(result_lines) == 3

    def test_hot_memory_returns_most_recent_lines(self):
        tiers = MemoryTiers(hot_memory_size=2)
        lines = [f'{{"role": "user", "content": "msg {i}"}}\n' for i in range(5)]

        mock_file = MagicMock()
        mock_file.__enter__ = lambda s: s
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_file.readlines.return_value = lines

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", return_value=mock_file):
                history = tiers.get_hot_memory("dummy.jsonl")

        result_lines = [l for l in history.split("\n") if l.strip()]
        assert "msg 4" in result_lines[-1]

    def test_hot_memory_empty_file_returns_empty(self):
        tiers = MemoryTiers(hot_memory_size=5)
        with patch("os.path.exists", return_value=False):
            result = tiers.get_hot_memory("nofile.jsonl")
        assert result == ""
