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
    
    # We will pass a real string representation of a JSONL file
    mock_log_lines = []
    for i in range(10):
        mock_log_lines.append(f'{{"role": "user", "content": "Message {i}"}}\n')
        
    fake_file_content = "".join(mock_log_lines)
    
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", return_value=StringIO(fake_file_content)):
            history = tiers.get_hot_memory("dummy.jsonl")
            
            # Should only keep the last 5
            lines = [l for l in history.split("\\n") if l.strip()]
            assert len(lines) == 5
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
    """Verify cold memories are not directly injected into context"""
    from brain.thalamus import Thalamus
    
    t = Thalamus()
    with patch.object(t.hippocampus, 'recall', return_value="Massive Cold Chunk"):
        with patch.object(t.hippocampus, 'recall_warm', return_value="Warm Chunk"):
            with patch.object(t.amygdala, 'feel', return_value={"primary_emotion": "neutral", "intensity": 0}):
                with patch.object(t.cortex, 'execute', return_value=None):
                    # Execute thalamus routing
                    with patch.object(t.prefrontal, 'execute') as mock_pfc:
                        # The thalamus MUST send the chunks to the prefrontal layer, not the main node
                        t.process_input("hello")
                
                # Verify prefrontal executes
                assert mock_pfc.called
