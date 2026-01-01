# tests/test_tool.py

import pytest
# CRITICAL: Added apply_diff for state reconstruction
from lar import GraphExecutor, ToolNode, AddValueNode, GraphState, apply_diff 

# --- Define some "tools" to test ---

def add_numbers(a: int, b: int) -> int:
    """A simple tool that succeeds."""
    return a + b

def failing_tool():
    """A simple tool that always fails."""
    raise ValueError("This tool was designed to fail")

# --- Tests ---

def test_tool_success_path():
    """Tests that the ToolNode runs a function and saves the output."""
    
    # 1. Arrange
    
    # Define the destination node
    success_node = AddValueNode(key="status", value="success", next_node=None)
    
    # Define the tool node
    tool = ToolNode(
        tool_function=add_numbers,
        input_keys=["num1", "num2"],  # Will read state.get("num1") and state.get("num2")
        output_key="sum_result",     # Will write to state.set("sum_result", ...)
        next_node=success_node,
        error_node=None              # We don't expect an error
    )
    
    executor = GraphExecutor()
    initial_state = {"num1": 10, "num2": 5}

    # 2. Act: Use run_step_by_step and rebuild the state
    audit_log = list(executor.run_step_by_step(
        start_node=tool, 
        initial_state=initial_state
    ))
    
    # Reconstruct the final state from the log
    final_state_data = initial_state
    for step in audit_log:
        final_state_data = apply_diff(final_state_data, step["state_diff"])

    # 3. Assert
    # Check that the graph ran two steps (ToolNode -> AddValueNode)
    assert len(audit_log) == 2
    # Check that the tool's output was saved
    assert final_state_data.get("sum_result") == 15
    # Check that the success_node was run
    assert final_state_data.get("status") == "success"


def test_tool_failure_path():
    """Tests that the ToolNode routes to the error_node on failure."""
    
    # 1. Arrange
    
    # Define the destination nodes
    success_node = AddValueNode(key="status", value="success", next_node=None)
    error_node = AddValueNode(key="status", value="failed", next_node=None)
    
    # Define the tool node
    tool = ToolNode(
        tool_function=failing_tool,
        input_keys=[],              # No inputs
        output_key="never_set",     # This key should not be set
        next_node=success_node,     # This node should not be run
        error_node=error_node       # This node *should* be run
    )
    
    executor = GraphExecutor()
    initial_state = {}

    # 2. Act: Use run_step_by_step and rebuild the state
    audit_log = list(executor.run_step_by_step(
        start_node=tool, 
        initial_state=initial_state
    ))
    
    # Reconstruct the final state from the log
    final_state_data = initial_state
    for step in audit_log:
        final_state_data = apply_diff(final_state_data, step["state_diff"])

    # 3. Assert
    # Check that the graph ran two steps (ToolNode -> ErrorNode)
    assert len(audit_log) == 2
    # Check that the error_node was run
    assert final_state_data.get("status") == "failed"
    # Check that the success output was never set
    assert final_state_data.get("never_set") is None
    # Check that the error message was saved to the state by ToolNode
    assert "This tool was designed to fail" in final_state_data.get("last_error")