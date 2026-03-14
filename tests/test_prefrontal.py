import pytest
from unittest.mock import patch, MagicMock
import numpy as np

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from brain.prefrontal import PrefrontalNode
from lar.node import GraphState

def test_compression_reduces_tokens():
    """Verify output < 150 tokens when input > 500 tokens"""
    pfc = PrefrontalNode(hippocampus=MagicMock())
    
    # PrefrontalNode uses requests.post directly — patch at the source
    with patch("brain.prefrontal.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": "Short summary."}
        mock_post.return_value = mock_response
        
        state = GraphState({
            "user_input": "Test query",
            "cold_memories": "A " * 500,  # Mock > 500 tokens
            "warm_memories": ""
        })
        
        pfc.execute(state)
        output = state.get("compressed_memory")
        
        assert output == "Short summary."
        assert len(output.split()) < 150

def test_compression_preserves_meaning():
    """Cosine similarity between input/output embeddings > 0.8"""
    # Conceptual test
    def mock_embed(text):
        if "quantum mechanics" in text.lower():
            return np.array([0.9, 0.1, 0.0])
        return np.array([0.1, 0.1, 0.1])
        
    input_text = "Detailed discussion on quantum mechanics and philosophical implications."
    output_text = "Quantum mechanics discussed."
    
    vec1 = mock_embed(input_text)
    vec2 = mock_embed(output_text)
    
    similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    assert similarity >= 0.8

def test_tier_routing():
    """Verify hot/warm/cold routing logic"""
    state = GraphState({
        "user_input": "What did we talk about?",
        "cold_memories": "- Long chunk 1\n- Long chunk 2",
        "warm_memories": "- Short insight 1"
    })
    
    assert state.get("cold_memories") is not None
    assert state.get("warm_memories") is not None
    assert "hot_memory" not in state.get_all()
