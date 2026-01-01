
"""
⚠️ WARNING: THIS SCRIPT DEMONSTRATES HOW LANGCHAIN/LANGGRAPH FAILS THE SWARM TEST

THE FLAW: "The Recursion Limit in Graph Architectures"
------------------------------------------------------
1. Even in modern LangGraph, the `MessageGraph` or `create_react_agent` has a safety limit.
2. Default `recursion_limit` is often 25.
3. Our swarm requires 64+ steps.
4. RESULT: Crash at Step 25.

"""
import os
import sys



import sys
try:
    from langgraph.graph import StateGraph, END
    from typing import TypedDict, Annotated
    import operator
except ImportError:
    print("❌ LangGraph not installed.")
    sys.exit(1)

# 1. Define State
class AgentState(TypedDict):
    count: int

# 2. Define Node (The Loop)
def worker_node(state: AgentState):
    print(f" -> Step {state['count']}")
    return {"count": state['count'] + 1}

# 3. Build Graph
workflow = StateGraph(AgentState)
workflow.add_node("worker", worker_node)
workflow.set_entry_point("worker")

# Define the edge: If count < 60, go back to worker. Else END.
# This forces a loop.
def should_continue(state: AgentState):
    if state["count"] < 60:
        return "worker"
    return END

workflow.add_conditional_edges("worker", should_continue)

app = workflow.compile()

print("🚀 Starting LangGraph Raw Engine Test...")
print("   Attempting 60 steps (Engine Default Limit: 25)")

# 4. Run to Crash
try:
    # recursion_limit defaults to 25.
    result = app.invoke({"count": 0}, config={"recursion_limit": 25})
    print("✅ Success! (This should not happen)")
except Exception as e:
    print(f"\n💥 CRASH CONFIRMED: {e}")
    print("   LangGraph Engine stopped execution due to Recursion Limit.")
