# tests/test_core.py

import pytest
# Removed PrintStateNode import
from lar import GraphExecutor, AddValueNode, GraphState, apply_diff 

def test_simple_graph_execution():
    """
    Tests a simple, linear A -> B graph.
    - Node A (AddValueNode) adds a value.
    - Node B (AddValueNode) marks the end.
    Asserts that both values are in the final state.
    """
    
    # 1. Arrange: Set up the graph and executor
    initial_state = {"user": "Solo Developer"}
    
    # Define the nodes in reverse order, from end to start
    
    # Node B: The end of the graph (replaces PrintStateNode)
    # This node will run, add a final marker, then return None, ending the graph.
    end_node = AddValueNode(
        key="test_status",
        value="COMPLETED",
        next_node=None # CRITICAL: Signals the end of execution
    )
    
    # Node A: The start of the graph
    start_node = AddValueNode(
        key="message", 
        value="Hello Lár!", 
        next_node=end_node
    )
    
    executor = GraphExecutor()

    # 2. Act: Run the graph and capture the full audit log
    audit_log = list(executor.run_step_by_step(
        start_node=start_node, 
        initial_state=initial_state
    ))
    
    # Reconstruct the final state from the log
    final_state_data = initial_state
    for step in audit_log:
        final_state_data = apply_diff(final_state_data, step["state_diff"])

    # 3. Assert: Check if the graph did its job
    
    # The audit log must contain exactly two steps
    assert len(audit_log) == 2 
    
    # Check that the final state contains the values from both nodes
    assert final_state_data is not None
    assert final_state_data.get("user") == "Solo Developer"
    assert final_state_data.get("message") == "Hello Lár!"
    assert final_state_data.get("test_status") == "COMPLETED"