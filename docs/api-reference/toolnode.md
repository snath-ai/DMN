# API Reference: `ToolNode`

The `ToolNode` is the "hands" of your agent. It is a robust node that runs any plain Python function (a "tool").

This is how your agent interacts with the world:

- Running code (`run_generated_code`)

- Searching a database (`retrieve_relevant_chunks`)

- Calling an external API (`Google Search`)

- Modifying the state (`increment_retry_count`)

## Key Features

- **Robust**: It runs your tool inside a `try...except` block by default.

- **Resilient**: It supports two separate paths: `next_node` (for success) and `error_node` (for failure).

- **Stateful**: It dynamically gathers the arguments for your tool from the `GraphState` using the input_keys you provide.

- **Auditable**: If your tool fails, the `ToolNode` automatically catches the exception and saves the error message to `state.set("last_error", ...)` for your other nodes to read.

## Example Usage

First, define your "tool." It's just a simple Python function:

```python
def add_numbers(a: int, b: int) -> int:
    """A simple tool that adds two numbers."""
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("Inputs must be integers")
    return a + b
```

Then, wire it into your graph with a `ToolNode`:

```python
# The ToolNode will:
# 1. Get `state.get("num1")` and `state.get("num2")`
# 2. Call `add_numbers(num1, num2)`
# 3. Save the result to `state.set("sum_result", ...)`
add_node = ToolNode(
    tool_function=add_numbers,
    input_keys=["num1", "num2"],
    output_key="sum_result",
    next_node=success_node,
    error_node=failure_node # If the TypeError is raised
)
```

What it Does

- When execute(state) is called:

    1. It builds a list of inputs by getting each key from self.input_keys.

    2. It calls self.tool_function(*inputs).

- If it succeeds:

    1. It saves the return value to state.set(self.output_key, ...)

    2. It returns self.next_node.

- If it fails:

    1. It saves the exception message to state.set("last_error", ...)

    2. It returns self.error_node.
    

```__init__``` Parameters

| Parameter | Type | Required | Description|
|-----------|------|----|---------------|
| `tool_function` | `Callable` | Yes | The Python function you want to run.|
| `input_keys` | `List[str]` | Yes | A list of keys to read from the 'GraphState'. The values are passed to your tool as positional arguments in order.|
| `output_key` | `str` | Yes | The `GraphState` key to save the tool's return value to.|
| `next_node` | `BaseNode` | Yes | The node to run if the tool succeeds.|
| `error_node` | `BaseNode` | No | The node to run if the tool fails (raises an Exception). If None, the graph will stop.|