import os
import sys
from dotenv import load_dotenv
load_dotenv()
# LiteLLM Helper: Map GOOGLE_API_KEY to GEMINI_API_KEY if needed
if os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.getenv("GOOGLE_API_KEY")

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from lar.node import LLMNode, ToolNode, RouterNode, ClearErrorNode
from lar.executor import GraphExecutor

"""
Example 3: Self-Correction Loop
------------------------------
Concepts:
- Looping (Graph cycles)
- Error Handling
- 'ClearErrorNode' pattern
"""

# 1. Code Generator
coder = LLMNode(
    model_name="gemini/gemini-2.5-pro",
    prompt_template="Write a Python function named 'solve' that {task}. Output ONLY the code.",
    output_key="code",
    system_instruction="You are a Python expert. Do not use markdown blocks."
)

# 2. Code Tester (Simulated)
def execute_code(code):
    # Simulation: Fail if code contains "error"
    if "error" in code.lower():
        raise Exception("SyntaxError: Unexpected token 'error'")
    return "Success"

tester = ToolNode(
    tool_function=execute_code,
    input_keys=["code"],
    output_key="test_result",
    next_node=None, # Wired later
    error_node=None # Wired later
)

# 3. Judge (Router)
def judge_result(state):
    if state.get("last_error"):
        print(f"  [Judge]: Detected error: {state.get('last_error')}")
        return "RETRY"
    return "SUCCESS"

end_node = None # Use None to stop execution

# 4. Fixer (LLM)
fixer = LLMNode(
    model_name="gemini-1.5-pro",
    prompt_template="The code failed with error: {last_error}. Fix the code:\n{code}",
    output_key="code"
)

# 5. Connect the Graph (The Loop)
# Start -> Coder -> Tester -> Judge
#                       |-> (Success) -> End
#                       |-> (Retry) -> Fixer -> ClearError -> Tester

coder.next_node = tester

# Judge configuration
judge = RouterNode(
    decision_function=judge_result,
    path_map={
        "SUCCESS": None, # End
        "RETRY": fixer
    }
)
tester.next_node = judge
tester.error_node = judge # Jump to judge on exception

# Loop back
fixer.next_node = ClearErrorNode(next_node=tester)

# 6. Run
if __name__ == "__main__":
    executor = GraphExecutor()
    # We force a failure first by asking for code with 'error'
    initial_state = {"task": "prints the word 'error' (this will trigger the mock failure)"}
    
    print(f"--- Running Self-Correction Loop ---")
    for step in executor.run_step_by_step(coder, initial_state, max_steps=10):
        print(f"Step {step['step']}: {step['node']} -> {step['outcome']}")
