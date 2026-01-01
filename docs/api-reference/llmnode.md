# API Reference: `LLMNode`

The `LLMNode` is the "brain" of your agent. It is a resilient, state-aware node that calls a generative AI model (like Google's Gemini) to perform a reasoning task.

It automatically formats your prompt with data from the `GraphState` and writes the model's text output back to the state.

## Key Features

- Resilient: Automatically retries on `429` (rate-limit) errors with exponential backoff.

- Cost Auditing: Automatically logs `prompt_tokens`, `output_tokens`, and `total_tokens` to the `run_metadata` in the history log.

- Stateful: Uses Python's `format()` string method to dynamically populate your prompt with any value from the `GraphState`.

## Example Usage

```python
# The LLMNode reads `task` from the state
planner_node = LLMNode(
    model_name="gemini/gemini-2.5-pro",
    prompt_template="You are a planner. Your task is: {task}",
    output_key="plan", # Saves the result to state["plan"]
    next_node=...
)
```
`__init__`  Parameters

| Parameter | Type | Required | Description|
|-----------|------|----|---------------|
| `model_name` | `str` | Yes | The name of the model (e.g., `"gemini-2.5-pro"`). |
| `prompt_template` | `str` | Yes | An f-string compatible template. Keys in `{braces}` will be filled from the GraphState. |
| `output_key` | `str` | Yes | The key to save the LLM's text response to in the `GraphState` (e.g., `"draft_answer"`). |
| `next_node` | `BaseNode`| Yes | The next node to run after this one successfully completes. |
| `max_retries` | `int` | No | The number of times to retry on a 429 error. Default: 3. |
