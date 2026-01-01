
import os
from lar import GraphExecutor, GraphState, LLMNode, RouterNode, ToolNode

# ==========================================
# 1. Define the Nodes (The Blueprints)
# ==========================================

# A. The Architect: breaks down the problem
architect = LLMNode(
    model_name="gemini/gemini-1.5-pro",
    prompt_template="""
    You are a Senior Software Architect.
    Analyze the user request: {input}
    
    If it's a coding task, output a step-by-step PLAN.
    If it's a question, just ANSWER it.
    
    Format your response as:
    TYPE: [CODE or Q&A]
    CONTENT: [Your Plan or Answer]
    """,
    output_key="architect_output"
)

# ... (omitted)

# C. The Engineer (The Builder)
engineer = LLMNode(
    model_name="gemini/gemini-1.5-flash",
    prompt_template="""
    You are a Software Engineer.
    Implement the following plan:
    {architect_output}
    
    Output the Python code block only.
    """,
    output_key="final_code"
)

# ... (wiring)

# Execution Loop
if __name__ == "__main__":
    # Setup Executor (Local or Remote)
    executor = GraphExecutor(log_dir="lar_logs")
    
    print("🚀 [Agentic IDE] Building 'Feature Implementation Agent'...")
    user_request = "Create a Python function to calculate Fibonacci series recursively."
    
    print(f"\nUser Input: {user_request}\n")
    
    # Run!
    for step in executor.run_step_by_step(architect, {"input": user_request}):
        node = step["node"]
        outcome = step["outcome"]
        print(f"  -> Executed {node} ({outcome})")
        
        if node == "LLMNode" and step.get("state_diff"):
             # Show what the AI thought
             diff = step["state_diff"]
             for k, v in diff.items():
                 preview = str(v)[:100].replace('\n', ' ')
                 print(f"     [Output ({k})]: {preview}...")

    print("\n✅ Done! The 'Code' was indeed the Graph.")
