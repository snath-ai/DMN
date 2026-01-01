
import os
import sys
from dotenv import load_dotenv
load_dotenv()
# LiteLLM Helper: Map GOOGLE_API_KEY to GEMINI_API_KEY if needed
if os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.getenv("GOOGLE_API_KEY")

sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from lar.node import LLMNode, ToolNode
from lar.executor import GraphExecutor

"""
Example 2: RAG Researcher
------------------------
Concepts:
- ToolNode for retrieval
- Context merging
- multi-step linear flow
"""

# Mock Vector DB
KNOWLEDGE_BASE = {
    "lar": "Lár is a Glass Box agent framework focused on auditability.",
    "python": "Python is a high-level programming language."
}

# 1. Retrieval Tool
def retrieve_docs(query):
    # Simple semantic search simulation
    query = query.lower()
    results = []
    for key, value in KNOWLEDGE_BASE.items():
        if key in query:
            results.append(value)
    
    if not results:
        return "No documents found."
    return "\n".join(results)

retriever = ToolNode(
    tool_function=retrieve_docs,
    input_keys=["query"],
    output_key="context", # Stores result in state['context']
    next_node=None # Wired later
)

# 2. Synthesizer LLM
synthesizer = LLMNode(
    model_name="gemini/gemini-2.5-pro",
    prompt_template="Using the context below, answer the user query.\n\nContext:\n{context}\n\nQuery: {query}",
    output_key="answer",
    next_node=None
)

# 3. Connect
retriever.next_node = synthesizer

# 4. Run
if __name__ == "__main__":
    executor = GraphExecutor()
    initial_state = {"query": "What is lar?"}
    
    print(f"--- Running RAG Agent with query: '{initial_state['query']}' ---")
    for step in executor.run_step_by_step(retriever, initial_state):
        print(f"Step {step['step']}: {step['node']}")
        if step['node'] == "LLMNode":
            print(f"  Answer: {step['state_diff']['added'].get('answer')}")
