# The 6 Lár Primitives (The "Lego Bricks")

**`Lár` is not a heavy, complex framework. It is a tiny, powerful engine with 6 core "primitives." You can combine these "Lego bricks" to build any agent, from a simple chatbot to a complex, multi-agent orchestrator.**

- The `GraphExecutor`

**What it is**: The "Engine" or "Conveyor Belt."

**Job**: A simple `generator` that runs one node at a time. It's the "dumb" loop that powers the "smart" nodes. It is also the "flight data recorder" that `yields` the audit log for each step.

- The `GraphState`

**What it is**: The "Memory" or "Clipboard."

**Job**: A simple Python object (a dictionary wrapper) that is passed to every node. It's how nodes share information. `LLMNode` writes to it, `ToolNode` reads from it, and `RouterNode` makes decisions with it.

- The `LLMNode`

**What it is**: The "Brain" or "Thinker."

**Job**: This node calls a generative model (like Gemini). It's where reasoning, writing, or classification happens. Our `LLMNode` is resilient—it has built-in exponential backoff to automatically retry on `429 rate-limit errors`. It also logs token usage for cost auditing.


- The `ToolNode`

**What it is**: The "Engine" or "Conveyor Belt."

**Job**: This node runs any simple Python function. This is how your agent interacts with the world: running code, searching a database, calling an API, or even running a local `FAISS` search. It has separate `next_node` and `error_node` paths, making it robust.

- The `RouterNode`

**What it is**: The "Choice" or "Manager."

**Job**: This is your `if/else` statement. It runs a simple, deterministic Python function (a `decision_function`) that reads the `GraphState` and returns a string (e.g., `"success"`). The `RouterNode` then uses this string to pick the next node from its `path_map`.


- The `"Utility" Nodes`

**What they are**: Simple "helper" bricks.

`AddValueNode`: Adds/copies data to the state. It's the perfect "final" node to copy `{draft_answer}` to `{final_answer}`.

`ClearErrorNode`: A "janitor" node. Its only job is to set `last_error` to `None`, which is critical for building self-correcting loops.