# tests/test_llm.py

import pytest
from unittest.mock import patch, MagicMock
from lar import GraphExecutor, LLMNode, AddValueNode, GraphState, apply_diff 

# --- Mock Response Data ---
MOCK_LLM_RESPONSE = MagicMock()
MOCK_LLM_RESPONSE.choices = [
    MagicMock(message=MagicMock(content="Mocked response for testing purposes."))
]
MOCK_LLM_RESPONSE.usage = MagicMock(
    prompt_tokens=10,
    completion_tokens=20,
    total_tokens=30 
)

# NOTE: The helper functions (run_generated_code, judge_function) are NOT needed here.

# --- Tests ---
# CRITICAL FIX: The patch needs to target the function where it is imported (litellm.completion)
@patch('lar.node.completion', return_value=MOCK_LLM_RESPONSE)
def test_llm_node_integration(mock_completion):
    """
    Tests that the LLMNode correctly builds the prompt and extracts the response
    text and token metadata, without hitting the actual API.
    """
    
    # 1. Arrange: Setup the graph
    
    # FIX: Clear the cache *before* creating the LLMNode instances to ensure the mock is loaded.
    LLMNode._model_cache.clear() 

    initial_state = {"topic": "AI agents"}
    end_node = AddValueNode(key="completion_marker", value=True, next_node=None)
    
    start_node = LLMNode(
        model_name="gemini/gemini-2.5-pro",
        prompt_template="Explain the topic of {topic} in one short sentence.",
        output_key="llm_response",
        next_node=end_node
    )
    
    executor = GraphExecutor()
    
    # 2. Act: Run the graph
    audit_log = list(executor.run_step_by_step(
        start_node=start_node, 
        initial_state=initial_state 
    ))
    
    final_state_data = initial_state
    for step in audit_log:
        final_state_data = apply_diff(final_state_data, step["state_diff"])

    # 3. Assert: Check logic and mocking integrity
    
    # Assert that the mock function was called once (no real API call)
    mock_completion.assert_called_once()
    
    # Check that the mocked response was added to the state
    llm_response = final_state_data.get("llm_response")
    assert llm_response == "Mocked response for testing purposes."
    
    # Check that the token metadata was correctly logged by the LLMNode
    llm_step = audit_log[0]
    assert llm_step['run_metadata']['total_tokens'] == 30
    assert final_state_data.get("completion_marker") == True