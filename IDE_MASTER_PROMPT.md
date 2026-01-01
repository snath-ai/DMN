# Lár Framework - Master Context
> **Note to AI**: You are coding with **Lár**, a graph-based agent framework that treats "Code as the Graph".
> Before generating any code, you MUST ingest this context.

## Core Principles
1.  **Strict Typing**: Every Node and Function MUST have Pydantic/Python type hints.
2.  **Explicit Linking**: Connect nodes using `.next_node = target` or `RouterNode(path_map={...})`.
3.  **No "Magic"**: Do not assume global state. Use `state.get()` and `state.set()`.
4.  **No Hidden Prompts**: All prompts must be visible in the `prompt_template` argument.

## Code Patterns to Follow

### 1. Defining a Node
```python
from lar import LLMNode

architect = LLMNode(
    model_name="gemini/gemini-1.5-pro",
    prompt_template="Analyze {input}...",
    output_key="plan"
)
```

### 2. Defining a Tool
```python
from lar import ToolNode

def my_tool(state):
    return "result"

tool = ToolNode(
    tool_function=my_tool,
    input_keys=["__state__"],
    output_key="result",
    next_node=None
)
```

### 3. Defining a Router
```python
from lar import RouterNode

def decide(state):
    return "go_left"

router = RouterNode(
    decision_function=decide,
    path_map={
        "go_left": left_node,
        "go_right": right_node
    }
)
```

## Running Agents
Always include a `if __name__ == "__main__":` block that uses `GraphExecutor` to run the graph instantly for verification.
