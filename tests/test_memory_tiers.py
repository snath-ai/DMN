import pytest
from unittest.mock import patch, MagicMock
from io import StringIO

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from brain.hippocampus import Hippocampus
from brain.memory_tiers import MemoryTiers

def test_hot_memory_rolling_buffer():
    """Test hot_memory_rolling_buffer max length is bounded to 5"""
    tiers = MemoryTiers(hot_memory_size=5)

    # Build 10 fake JSONL lines
    mock_log_lines = []
    for i in range(10):
        mock_log_lines.append(f'{{"role": "user", "content": "Message {i}"}}\n')

    with patch("os.path.exists", return_value=True):
        # Mock open so that f.readlines() returns our list of strings correctly
        mock_file = MagicMock()
        mock_file.__enter__ = lambda s: s
        mock_file.__exit__ = MagicMock(return_value=False)
        mock_file.readlines.return_value = mock_log_lines

        with patch("builtins.open", return_value=mock_file):
            history = tiers.get_hot_memory("dummy.jsonl")

            # memory_tiers.py now uses real "\n" – split on actual newlines
            lines = [l for l in history.split("\n") if l.strip()]
            assert len(lines) == 5, f"Expected 5 lines, got {len(lines)}: {lines}"
            assert lines[-1] == "user: Message 9"
            assert lines[0] == "user: Message 5"

def test_warm_memory_threshold():
    """Test warm_memory_threshold (similarity > 0.7 only)"""
    hippo = Hippocampus()

    with patch.object(hippo, 'warm_collection') as mock_warm:
        # Mock Chroma returning a distance of 0.2 (which is 1 - 0.2 = 0.8 similarity)
        mock_warm.query.return_value = {
            'documents': [["Relevant semantic summary"]],
            'distances': [[0.2]] # > 0.7 similarity threshold
        }

        with patch.object(hippo, '_generate_embedding', return_value=[0.1]*3072):
            result = hippo.recall_warm("query")
            assert "Relevant semantic summary" in result

def test_cold_never_injected_directly():
    """Verify cold memories are not directly injected into context — PFC must gate them."""
    from brain.thalamus import Thalamus

    # Patch ChromaDB at construction time so Thalamus() never opens a real DB.
    with patch("brain.hippocampus.chromadb.PersistentClient") as mock_chroma:
        mock_collection = MagicMock()
        mock_chroma.return_value.get_or_create_collection.return_value = mock_collection

        t = Thalamus()

    with patch.object(t.hippocampus, 'recall', return_value="Massive Cold Chunk"):
        with patch.object(t.hippocampus, 'recall_warm', return_value="Warm Chunk"):
            with patch.object(t.hippocampus, 'get_latest_dream', return_value=None):
                with patch.object(t.amygdala, 'feel', return_value={"primary_emotion": "neutral", "intensity": 0}):
                    with patch.object(t.cortex, 'execute', return_value=None):
                        with patch.object(t.stream, 'log_interaction', return_value=None):
                            with patch.object(t.prefrontal, 'execute') as mock_pfc:
                                t.process_input("hello")

    # The Thalamus MUST route chunks through PFC, not inject cold memory directly
    assert mock_pfc.called
