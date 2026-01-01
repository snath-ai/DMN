"""
Mini swarm example inspired by the corporate swarm pattern.
One LLM sets strategy, routers prune or execute branches, and workers
perform cheap increments. Demonstrates a dynamic computation graph
controlled by a single LLM decision.
"""

from typing import Callable, Dict
import time

from lar.executor import GraphExecutor
from lar.node import AddValueNode, LLMNode, RouterNode, ToolNode
from lar.state import GraphState


def make_worker(next_node: AddValueNode) -> ToolNode:
    """
    Worker increments total_completed to simulate work.
    """

    def do_work(total_completed: int) -> Dict[str, int]:
        return {"total_completed": (total_completed or 0) + 1}

    return ToolNode(
        tool_function=do_work,
        input_keys=["total_completed"],
        output_key=None,
        next_node=next_node,
    )


def make_manager(
    level: int, max_depth: int, next_node_success: AddValueNode
) -> RouterNode | ToolNode:
    """
    Recursive manager that either executes its branch or prunes it
    based on strategy in the state.
    """
    if level >= max_depth:
        return make_worker(next_node_success)

    right_branch = make_manager(level + 1, max_depth, next_node_success)
    left_branch = make_manager(level + 1, max_depth, right_branch)

    def decide(state: GraphState) -> str:
        strategy = (state.get("strategy") or "BLITZSCALING").upper()
        if strategy == "AUSTERITY":
            # Prune every other branch to simulate savings
            return "PRUNE" if (state.get("_prune_toggle") or 0) % 2 == 0 else "EXECUTE"
        return "EXECUTE"

    def toggle_prune(state: GraphState) -> None:
        state.set("_prune_toggle", (state.get("_prune_toggle") or 0) + 1)

    def decision_with_toggle(state: GraphState) -> str:
        toggle_prune(state)
        return decide(state)

    return RouterNode(
        decision_function=decision_with_toggle,
        path_map={"EXECUTE": left_branch, "PRUNE": right_branch},
        default_node=right_branch,
    )


def build_swarm(
    model_name: str = "gemini/gemini-1.5-flash",
    depth: int = 3,
    use_stub_ceo: bool = False,
) -> RouterNode | LLMNode | ToolNode:
    """
    Build a mini-swarm graph with one LLM CEO and a prunable hierarchy.
    If use_stub_ceo is True, replace the LLM with a ToolNode stub that sets strategy.
    """
    end_node = AddValueNode(key="final_status", value="DONE", next_node=None)
    head_manager = make_manager(level=1, max_depth=depth, next_node_success=end_node)

    if use_stub_ceo:
        def stub_strategy(market_condition: str) -> Dict[str, str]:
            # simple heuristic: if "tight" or "uncertain" then austerity
            lower = (market_condition or "").lower()
            strategy = "AUSTERITY" if ("tight" in lower or "uncertain" in lower) else "BLITZSCALING"
            return {"strategy": strategy}

        return ToolNode(
            tool_function=stub_strategy,
            input_keys=["market_condition"],
            output_key=None,
            next_node=head_manager,
        )

    ceo = LLMNode(
        model_name=model_name,
        prompt_template=(
            "You are the CEO. Read the market and output exactly one word:\n"
            "- BLITZSCALING (grow fast)\n"
            "- AUSTERITY (conserve)\n"
            "Market: {market_condition}"
        ),
        output_key="strategy",
        next_node=head_manager,
    )

    return ceo


if __name__ == "__main__":
    executor = GraphExecutor()
    start = build_swarm(use_stub_ceo=True)

    scenario = {
        "market_condition": "Funding is tight and demand is uncertain; conserve cash.",
        "total_completed": 0,
    }

    print("\n--- Running mini swarm ---")
    t0 = time.time()
    steps = list(executor.run_step_by_step(start, scenario))
    duration = time.time() - t0

    print(f"Steps executed: {len(steps)}")
    print(f"Duration: {duration:.2f}s")
    if steps:
        final_state = steps[-1]["state_diff"].get("updated", {})
        print(f"State diff (last step): {final_state}")

