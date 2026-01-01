"""
Example: Lightweight support helper agent built with Lár.
The graph classifies the request, optionally gathers lightweight
context via a ToolNode, and then drafts a response with an LLMNode.
"""

import json
from typing import Dict, List, Tuple

from lar.executor import GraphExecutor
from lar.node import AddValueNode, LLMNode, RouterNode, ToolNode
from lar.state import GraphState

# --- Toy Knowledge Base -------------------------------------------------------
KnowledgeEntry = Tuple[str, str]
KNOWLEDGE_BASE: List[KnowledgeEntry] = [
    (
        "installation",
        "To install, run `pip install lar` and set your LLM provider keys (e.g., OPENAI_API_KEY).",
    ),
    (
        "quickstart",
        "Start from `lar/examples/1_simple_triage.py` to learn graph construction basics.",
    ),
    (
        "logging",
        "Execution traces are written to `lar_logs/run_<id>.json` via GraphExecutor.",
    ),
]


def retrieve_context(user_query: str) -> Dict[str, str]:
    """
    Very small keyword matcher that returns a relevant snippet.
    Returns a flat dict to satisfy ToolNode contract.
    """
    query_lower = user_query.lower()
    best_match: KnowledgeEntry | None = None

    for entry in KNOWLEDGE_BASE:
        title, _ = entry
        if title in query_lower:
            best_match = entry
            break

    if best_match is None and KNOWLEDGE_BASE:
        best_match = KNOWLEDGE_BASE[0]

    title, snippet = best_match
    return {"context_title": title, "context_snippet": snippet}


def route_on_intent(state: GraphState) -> str:
    """
    Router decision: if the classifier asked for retrieval, branch to the lookup tool.
    """
    intent_label = (state.get("intent_label") or "").lower()
    if "retrieve" in intent_label or "context" in intent_label:
        return "retrieve"
    return "direct"


def build_agent_graph(model_name: str = "gemini/gemini-1.5-flash") -> LLMNode:
    """
    Build the support helper graph using forward definition then explicit linking.
    """
    intent_classifier = LLMNode(
        model_name=model_name,
        prompt_template=(
            "You are an intent classifier.\n"
            "Label the user request as one of: 'direct' or 'retrieve'.\n"
            "If the user asks about installation, quickstart, or logging, pick 'retrieve'.\n"
            "User request: {user_query}\n"
            "Return only the single word label."
        ),
        output_key="intent_label",
        next_node=None,
    )

    context_lookup = ToolNode(
        tool_function=retrieve_context,
        input_keys=["user_query"],
        output_key=None,
        next_node=None,
    )

    respond_with_context = LLMNode(
        model_name=model_name,
        prompt_template=(
            "You are a concise support agent for the Lár framework.\n"
            "User request: {user_query}\n"
            "Context title: {context_title}\n"
            "Context snippet: {context_snippet}\n"
            "Provide a short, direct answer. If unsure, say so briefly."
        ),
        output_key="final_answer",
        next_node=None,
    )

    respond_direct = LLMNode(
        model_name=model_name,
        prompt_template=(
            "You are a concise support agent for the Lár framework.\n"
            "User request: {user_query}\n"
            "No additional context is available. Answer briefly and clearly."
        ),
        output_key="final_answer",
        next_node=None,
    )

    done = AddValueNode(key="final_status", value="COMPLETE", next_node=None)

    router = RouterNode(
        decision_function=route_on_intent,
        path_map={
            "retrieve": context_lookup,
            "direct": respond_direct,
        },
        default_node=respond_direct,
    )

    # --- Explicit linking ----------------------------------------------------
    intent_classifier.next_node = router
    context_lookup.next_node = respond_with_context
    respond_with_context.next_node = done
    respond_direct.next_node = done

    return intent_classifier


if __name__ == "__main__":
    # Example usage: run the graph step-by-step for observability.
    user_query = (
        "How do I install Lár and where do I see the execution logs after a run?"
    )
    initial_state: Dict[str, str] = {"user_query": user_query}

    start_node = build_agent_graph()
    executor = GraphExecutor()

    print("\n--- Running support helper agent ---")
    for step in executor.run_step_by_step(start_node, initial_state):
        print(json.dumps(step, indent=2))

