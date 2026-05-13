"""
Lár: A "Define-by-Run" Agentic Framework.

This file makes the core classes and utilities available for easy import
by any developer who runs `pip install lar-engine`.
"""
__version__ = "2.1.0"

from .state import GraphState
from .node import (
    BaseNode,
    AddValueNode,
    LLMNode,
    RouterNode,
    ToolNode,
    ClearErrorNode,
    BatchNode,
    HumanJuryNode,
    FunctionalNode,
    ReduceNode,
    node,
)
from .adaptive import AdaptiveNode, DynamicNode, TopologyValidator
from .compliance import BranchTriageNode
from .executor import GraphExecutor
from .logger import AuditLogger
from .tracker import TokenTracker
from .utils import compute_state_diff, apply_diff
from .formatter import build_log_table, summarize_diff
from .serializer import export_graph_to_json

__all__ = [
    "GraphState",
    "GraphExecutor",
    "AuditLogger",
    "TokenTracker",
    "BaseNode",
    "AddValueNode",
    "LLMNode",
    "RouterNode",
    "ToolNode",
    "ClearErrorNode",
    "BatchNode",
    "HumanJuryNode",
    "FunctionalNode",
    "ReduceNode",
    "node",
    "AdaptiveNode",
    "DynamicNode",
    "TopologyValidator",
    "BranchTriageNode",
    "compute_state_diff",
    "apply_diff",
    "build_log_table",
    "summarize_diff",
    "export_graph_to_json",
    "__version__",
]
