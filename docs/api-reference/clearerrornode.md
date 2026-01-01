[← Return to API Reference](../api-reference/utilities.md)

# ClearErrorNode

A "janitor" node designed for self-correction loops. Its only job is to remove the `last_error` key from the state, allowing a retry loop to proceed cleanly.

## Import

```python
from lar.node import ClearErrorNode
```

## Constructor

```python
ClearErrorNode(
    next_node: BaseNode = None
)
```

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `next_node` | `BaseNode` | The node to transition to after clearing the error (usually the node you want to retry). |

## Usage Pattern: The Retry Loop

This node is typically placed *after* a Router detects an error and *before* the Agent retries the task.

```python
# 1. The Retry Target
generator = LLMNode(...)

# 2. Cleanup Node
cleaner = ClearErrorNode(next_node=generator)

# 3. Router logic
def check_error(state):
    if state.get("last_error"):
        return "RETRY"
    return "SUCCESS"

router = RouterNode(
    decision_function=check_error,
    path_map={
        "RETRY": cleaner, # Go to cleaner, then back to generator
        "SUCCESS": end_node
    }
)
```
