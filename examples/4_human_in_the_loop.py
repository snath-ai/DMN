import os
import sys
from dotenv import load_dotenv
load_dotenv()
# LiteLLM Helper: Map GOOGLE_API_KEY to GEMINI_API_KEY if needed
if os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.getenv("GOOGLE_API_KEY")

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from lar.node import LLMNode, ToolNode, RouterNode
from lar.executor import GraphExecutor

"""
Example 4: Human-in-the-Loop Validation
--------------------------------------
Concepts:
- ToolNode as an "Input Node"
- Pausing for user feedback (simulated via Python input())
- Approval workflows
"""

# 1. Proposal Generator
proposal_bot = LLMNode(
    model_name="gemini/gemini-2.5-pro",
    prompt_template="Write a short tweet about: {topic}.",
    output_key="tweet_draft",
    system_instruction="You are a social media manager."
)

# 2. Human Review Tool (Blocking)
def human_review(state):
    draft = state.get("tweet_draft")
    print(f"\n--- ✋ HUMAN INTERVENTION REQUIRED ---")
    print(f"Draft Tweet: {draft}")
    print("------------------------------------")
    # In a real app, this would be an API wait/pause.
    # Here, we simulate it with CLI input.
    decision = input("Do you approve this tweet? (yes/no): ").strip().lower()
    return "APPROVED" if decision == "yes" else "REJECTED"

reviewer = ToolNode(
    tool_function=human_review,
    input_keys=["__state__"], # Access full state to read draft
    output_key="status", # Stores "APPROVED" or "REJECTED"
    next_node=None # Wired to router
)

# 3. Router
def route_approval(state):
    return state.get("status", "REJECTED")

publisher = ToolNode(
    tool_function=lambda x: f"Published: {x}",
    input_keys=["tweet_draft"],
    output_key="final_status",
    next_node=None
)

reject_handler = ToolNode(
    tool_function=lambda: "Tweet Rejected by User.",
    input_keys=[],
    output_key="final_status",
    next_node=None
)

router = RouterNode(
    decision_function=route_approval,
    path_map={
        "APPROVED": publisher,
        "REJECTED": reject_handler
    }
)

# Wiring
proposal_bot.next_node = reviewer
reviewer.next_node = router

if __name__ == "__main__":
    executor = GraphExecutor()
    print("--- Running Human-in-the-Loop Agent ---")
    
    # We use a loop here because input() is blocking in the CLI.
    # In a real server, you'd save state and resume later.
    for step in executor.run_step_by_step(proposal_bot, {"topic": "AI Agents"}):
        print(f"Step {step['step']}: {step['node']} -> {step['outcome']}")
