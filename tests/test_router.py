# tests/test_router.py

import pytest
# Ensure all necessary utilities are imported
from lar import GraphExecutor, AddValueNode, RouterNode, GraphState, apply_diff 

# --- Define our "decision logic" ---
def number_router(state: GraphState) -> str:
    """Checks a 'number' in the state and returns a route key."""
    number = state.get("number", 0)
    if number > 10:
        return "greater"
    else:
        return "less_or_equal"

# --- Tests ---

def test_router_path_greater():
    """Tests that the router correctly takes the 'greater' path."""
    
    # 1. Arrange
    greater_node = AddValueNode(key="result", value="was_greater", next_node=None)
    less_node = AddValueNode(key="result", value="was_less", next_node=None)
    
    path_map = {
        "greater": greater_node,
        "less_or_equal": less_node
    }
    
    router = RouterNode(
        decision_function=number_router,
        path_map=path_map
    )
    
    executor = GraphExecutor()
    initial_state = {"number": 20}

    # 2. Act: Use run_step_by_step and rebuild the state
    audit_log = list(executor.run_step_by_step(
        start_node=router, 
        initial_state=initial_state
    ))
    
    # Reconstruct the final state from the log
    final_state_data = initial_state
    for step in audit_log:
        final_state_data = apply_diff(final_state_data, step["state_diff"])

    # 3. Assert
    # The graph must have run two steps (RouterNode -> AddValueNode)
    assert len(audit_log) == 2
    # We check that the 'greater_node' was run successfully
    assert final_state_data.get("result") == "was_greater"


def test_router_path_less():
    """Tests that the router correctly takes the 'less_or_equal' path."""
    
    # 1. Arrange
    greater_node = AddValueNode(key="result", value="was_greater", next_node=None)
    less_node = AddValueNode(key="result", value="was_less", next_node=None)
    
    path_map = {
        "greater": greater_node,
        "less_or_equal": less_node
    }
    
    router = RouterNode(
        decision_function=number_router,
        path_map=path_map
    )
    
    executor = GraphExecutor()
    initial_state = {"number": 5} # Number < 10

    # 2. Act: Use run_step_by_step and rebuild the state
    audit_log = list(executor.run_step_by_step(
        start_node=router, 
        initial_state=initial_state
    ))
    
    # Reconstruct the final state from the log
    final_state_data = initial_state
    for step in audit_log:
        final_state_data = apply_diff(final_state_data, step["state_diff"])

    # 3. Assert
    # The graph must have run two steps (RouterNode -> AddValueNode)
    assert len(audit_log) == 2
    # We check that the 'less_node' was run successfully
    assert final_state_data.get("result") == "was_less"