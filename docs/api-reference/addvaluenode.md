[← Return to API Reference](../api-reference/utilities.md)

# AddValueNode

A utility node for injecting data or copying values within the state. It is useful for setting flags, default values, or aliasing keys.

## Import

```python
from lar.node import AddValueNode
```

## Constructor

```python
AddValueNode(
    key: str, 
    value: Any, 
    next_node: BaseNode = None
)
```

| Parameter | Type | Description |
| :--- | :--- | :--- |
| `key` | `str` | The key in the state dictionary to set/overwrite. |
| `value` | `Any` | The value to assign. Supports dynamic state references using `{key_name}` syntax. |
| `next_node` | `BaseNode` | The next node to execute in the graph. |

## Usage Examples

### 1. Setting a Static Flag
```python
mark_success = AddValueNode(
    key="status",
    value="SUCCESS",
    next_node=None
)
```

### 2. Copying State Variables (Aliasing)
You can copy one state key to another using `{}` syntax. This is useful for reshaping data before passing it to a tool.

```python
# Copies state["llm_output"] -> state["final_answer"]
alias_node = AddValueNode(
    key="final_answer",
    value="{llm_output}",
    next_node=next_step
)
```
