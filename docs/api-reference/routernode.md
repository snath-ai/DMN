# API Reference: `RouterNode`

The `RouterNode` is the `"choice"` or `if/else` statement for your agent. It is a **100% deterministic** node that uses pure Python logic to decide where the agent should go next.

This is the key to building complex, auditable, multi-agent systems and loops.

## Key Features

- **Deterministic**: It's just a Python function. No AI, no "magic." It will do the same thing every time, given the same state.

- **Multi-Path**: It can route the agent down many different "assembly lines" (e.g., "BILLING" vs. "TECH_SUPPORT").

- **Loop-Capable**: By routing from a "Judge" node back to a "Tester" node, you can create powerful self-correcting loops.

## Example Usage

First, define your simple, stateless "logic" function:

```python
def judge_function(state: GraphState) -> str:
    """Reads the state and returns a string key."""
    if state.get("last_error"):
        return "failure_path" # This key must match the path_map
    else:
        return "success_path"
```

Then, wire it into your `RouterNode`:

```python
# The RouterNode reads the string from judge_function
# and uses it to pick the next node.
judge_node = RouterNode(
    decision_function=judge_function,
    path_map={
        "success_path": success_node,
        "failure_path": corrector_node
    },
    default_node=critical_fail_node # Optional: for safety
)
```

What it Does

When `execute(state)` is called:

1. It runs `route_key = self.decision_function(state).`

2. It looks up that `route_key` in `self.path_map`.

3. If found, it returns the corresponding node (e.g., `corrector_node`).

4. If not found, it returns the `default_node`.

5. If no default, it returns `None` and stops the graph.

```__init__``` Parameters


| Parameter | Type | Required | Description|
|-----------|------|----|---------------|
| `decision_function` | `Callable` | Yes | A Python function that takes a `GraphState` as input and returns a single `str` (the route key).|
| `path_map` | `Dict` | Yes | A dictionary that maps the string keys from your function to the `BaseNode` objects to run (e.g., `{"success_path": ...}`)|
| `default_node` | `BaseNode` | No | (Optional) A fallback node to run if the `decision_function` returns a key that is not in the `path_map`.|
