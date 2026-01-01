import os
import sys
from dotenv import load_dotenv
load_dotenv()
# LiteLLM Helper: Map GOOGLE_API_KEY to GEMINI_API_KEY if needed
if os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.getenv("GOOGLE_API_KEY")

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from lar.node import LLMNode, ToolNode, RouterNode, AddValueNode
from lar.executor import GraphExecutor

"""
Example 5: Fan-Out / Fan-In (Parallel Simulation)
------------------------------------------------
Concepts:
- Running multiple diverse tasks
- Aggregating results (Fan-In)
- Note: Lár executes sequentially, but this pattern
  simulates logical parallelism.
"""

# 1. Branch A: Fundamental Research
researcher_a = LLMNode(
    model_name="gemini/gemini-2.5-pro",
    prompt_template="Define '{topic}' in one sentence.",
    output_key="result_a"
)

# 2. Branch B: Technical Analysis
researcher_b = LLMNode(
    model_name="gemini/gemini-2.5-pro",
    prompt_template="Explain the technical difficulty of '{topic}' in one sentence.",
    output_key="result_b"
)

# 3. Branch C: Market Analysis
researcher_c = LLMNode(
    model_name="gemini/gemini-2.5-pro",
    prompt_template="What is the market size for '{topic}'? Give one number.",
    output_key="result_c"
)

# 4. Aggregator (Fan-In)
def aggregate(state):
    return (
        f"1. Definition: {state.get('result_a')}\n"
        f"2. Tech: {state.get('result_b')}\n"
        f"3. Market: {state.get('result_c')}"
    )

aggregator = ToolNode(
    tool_function=aggregate,
    input_keys=["__state__"],
    output_key="final_report",
    next_node=None
)

# Wiring the linear sequence (Fan-Out simulation)
# A -> B -> C -> Aggregator
researcher_a.next_node = researcher_b
researcher_b.next_node = researcher_c
researcher_c.next_node = aggregator

if __name__ == "__main__":
    executor = GraphExecutor()
    print("--- Running Fan-Out Agent (Quantum Computing) ---")
    for step in executor.run_step_by_step(researcher_a, {"topic": "Quantum Computing"}):
        print(f"Step {step['step']}: {step['node']}")
        if "final_report" in step['state_diff'].get("added", {}):
            print(f"\nReport:\n{step['state_diff']['added']['final_report']}")
