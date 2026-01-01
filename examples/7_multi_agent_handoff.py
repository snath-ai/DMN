import os
import sys
from dotenv import load_dotenv
load_dotenv()
# LiteLLM Helper: Map GOOGLE_API_KEY to GEMINI_API_KEY if needed
if os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.getenv("GOOGLE_API_KEY")

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from lar.node import LLMNode, RouterNode
from lar.executor import GraphExecutor

"""
Example 7: Multi-Agent Handoff
-----------------------------
Concepts:
- Specialized Personas (Writer vs Editor)
- Routing based on LLM output criteria
- Iterative Refinement
"""

# 1. Writer Agent
writer = LLMNode(
    model_name="gemini/gemini-2.5-pro",
    prompt_template="Write a short paragraph about: {topic}.",
    output_key="draft",
    system_instruction="You are a creative writer."
)

# 2. Editor Agent
editor = LLMNode(
    model_name="gemini/gemini-2.5-pro",
    prompt_template=(
        "Review this draft:\n{draft}\n\n"
        "If it is good, say 'PERFECT'. "
        "If it needs work, output the critique."
    ),
    output_key="editor_feedback",
    system_instruction="You are a strict editor."
)

# 3. Router logic
def check_feedback(state):
    feedback = state.get("editor_feedback", "").strip()
    if "PERFECT" in feedback:
        return "DONE"
    return "REWRITE"

# 4. Rewriter (Writer with feedback)
rewriter = LLMNode(
    model_name="gemini-1.5-pro",
    prompt_template="Rewrite this draft based on feedback: {editor_feedback}.\nOriginal: {draft}",
    output_key="draft", # Overwrite the draft
    system_instruction="You are a creative writer."
)

# Wiring
writer.next_node = editor

handoff_router = RouterNode(
    decision_function=check_feedback,
    path_map={
        "DONE": None,    # End
        "REWRITE": rewriter
    }
)
editor.next_node = handoff_router

# Loop: Rewriter -> Editor
rewriter.next_node = editor

if __name__ == "__main__":
    executor = GraphExecutor()
    print("--- Running Writer/Editor Cycle ---")
    # We limit steps to avoid infinite arguments between writer/editor
    for step in executor.run_step_by_step(writer, {"topic": "The Moon"}, max_steps=6):
        print(f"Step {step['step']} ({step['node']}):")
        if step['node'] == "LLMNode":
            print(f"  > Output: {list(step['state_diff']['added'].values())[0][:50]}...")
