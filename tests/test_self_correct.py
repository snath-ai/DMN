# tests/test_self_correct.py

import pytest
from unittest.mock import patch, MagicMock
from lar import (
    GraphExecutor, apply_diff, LLMNode, 
    ToolNode, RouterNode, AddValueNode, GraphState, ClearErrorNode
)
# Ensure helper functions for running code are imported/defined here

# --- Define Judge Function (CRITICAL FIX) ---
def judge_function(state: GraphState) -> str:
    """Checks the state for 'last_error' to determine if correction is needed."""
    if state.get("last_error"):
        return "failure"
    else:
        return "success"
        
# --- Define Tool Function (CRITICAL FIX) ---
def run_generated_code(code_string: str) -> str:
    # Your required tool logic for testing code execution
    # NOTE: You must place the full, actual logic here, including stripping fences and exec().
    try:
        # Example of simplified success logic for testing the graph flow
        if code_string.startswith("```python"):
            code_string = code_string.split("\n", 1)[1].rsplit("\n", 1)[0]

        local_scope = {}
        exec(code_string, {}, local_scope)
        func = local_scope['add_five']
        result = func(10)
        
        if result != 15:
             raise ValueError("Logic failed")
        return "Success!"
    except Exception as e:
        raise e


# --- Mock Response Data and Sequence ---
FIRST_MOCK_CONTENT = "```python\ndef add_five(x)\n    return x + 5\n```" 
SECOND_MOCK_CONTENT = "```python\ndef add_five(x):\n    return x + 5\n```" 

MOCK_RESPONSE_1 = MagicMock(
    choices=[MagicMock(message=MagicMock(content=FIRST_MOCK_CONTENT))],
    usage=MagicMock(prompt_tokens=20, completion_tokens=80, total_tokens=100)
)
MOCK_RESPONSE_2 = MagicMock(
    choices=[MagicMock(message=MagicMock(content=SECOND_MOCK_CONTENT))],
    usage=MagicMock(prompt_tokens=40, completion_tokens=60, total_tokens=100)
)

MOCK_RESPONSE_SEQUENCE = [MOCK_RESPONSE_1, MOCK_RESPONSE_2]


@patch('lar.node.completion', side_effect=MOCK_RESPONSE_SEQUENCE)
def test_self_correcting_agent_loop(mock_completion):
    """
    Tests the full self-correction cycle using mocked LLM responses.
    """
    
    # 1. ARRANGE: Define all nodes sequentially inside the function scope

    # CRITICAL FIX: Clear the cache *before* creating the LLMNode instances
    LLMNode._model_cache.clear() 

    # --- Destination Nodes ---
    success_node = AddValueNode(key="final_status", value="SUCCESS", next_node=None)
    critical_fail_node = AddValueNode(key="final_status", value="CRITICAL_FAILURE", next_node=None)

    # --- The "Corrector" Node (LLM) ---
    corrector_node = LLMNode(
        model_name="gemini/gemini-2.5-pro", prompt_template="Fix code: {code_string}",
        output_key="code_string", next_node=None  
    )

    # --- The "Judge" Node (Router) ---
    judge_node = RouterNode(
        decision_function=judge_function, 
        path_map={"success": success_node, "failure": corrector_node},
        default_node=critical_fail_node
    )
    
    # --- The "Tester" Node (Tool) ---
    tester_node = ToolNode(
        tool_function=run_generated_code, 
        input_keys=["code_string"], output_key="test_result",     
        next_node=judge_node, error_node=judge_node         
    )
    
    # --- The "Writer" Node (LLM) ---
    writer_node = LLMNode(
        model_name="gemini/gemini-2.5-pro",
        prompt_template="Write broken function.", output_key="code_string",
        next_node=tester_node  
    )
    
    # --- The "Janitor" Node ---
    clear_error_node = ClearErrorNode(next_node=tester_node)

    # --- Create the Loop (Final Wiring Step) ---
    corrector_node.next_node = clear_error_node 

    # 2. ACT: Run the agent
    executor = GraphExecutor()
    initial_state = {"task": "Create a function to add 5"}
    
    audit_log = list(executor.run_step_by_step(
        start_node=writer_node, initial_state=initial_state
    ))
    
    final_state_data = initial_state
    for step in audit_log:
        final_state_data = apply_diff(final_state_data, step["state_diff"])

    # 3. ASSERT: Check the integrity of the loop and final state
    assert final_state_data.get("test_result") == "Success!"
    assert final_state_data.get("final_status") == "SUCCESS"
    assert len(audit_log) == 8
    assert mock_completion.call_count == 2