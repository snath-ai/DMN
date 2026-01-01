import os
import sys
from dotenv import load_dotenv
load_dotenv()

# Ensure we can import from src
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from lar.node import LLMNode, RouterNode, ToolNode
from lar.executor import GraphExecutor

# LiteLLM Helper: Map GOOGLE_API_KEY to GEMINI_API_KEY if needed
if os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.getenv("GOOGLE_API_KEY")

"""
Example 1: Simple Triage Bot
---------------------------
Concepts: 
- Linear Chains (Node A -> Node B)
- LLMNode configuration
- Basic Routing
"""

# 1. Define Nodes
classifier = LLMNode(
    model_name="gemini/gemini-2.5-pro",
    prompt_template="Classify the following request as 'BILLING' or 'TECHNICAL'. Request: {input}",
    output_key="classification",
    system_instruction="You are a triage assistant. Output only one word."
)

def billing_response(state):
    print("  [Billing Team] Processing refund...")
    return f"Billing ticket created for: {state.get('input')}"

billing_tool = ToolNode(
    tool_function=billing_response,
    input_keys=["__state__"],
    output_key="result",
    next_node=None
)

def tech_response(state):
    print("  [Tech Support] Processing bug report...")
    return f"Tech ticket created for: {state.get('input')}"

tech_tool = ToolNode(
    tool_function=tech_response,
    input_keys=["__state__"],
    output_key="result",
    next_node=None
)

# 2. Define Routing Logic
def route_request(state):
    # Normalize output to handle potential LLM whitespace
    cls = state.get("classification", "").strip().upper()
    if "BILLING" in cls: return "BILLING"
    if "TECHNICAL" in cls: return "TECHNICAL"
    return "TECHNICAL" # Default

router = RouterNode(
    decision_function=route_request,
    path_map={
        "BILLING": billing_tool,
        "TECHNICAL": tech_tool
    }
)

# 3. Connect the Graph
classifier.next_node = router

# 4. Run it
if __name__ == "__main__":
    executor = GraphExecutor()
    initial_state = {"input": "I was overcharged for my subscription."}
    
    print(f"--- Running Triage Agent with input: '{initial_state['input']}' ---")
    for step in executor.run_step_by_step(classifier, initial_state):
        print(f"Step {step['step']}: {step['node']} -> {step['outcome']}")
    
    print("\nFinal Result:", step['state_diff'])
