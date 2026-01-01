from typing import List, Dict, Set
from pydantic import BaseModel
import networkx as nx
from .spec import AgentManifest, NodeType, RouterNodeModel, ToolNodeModel

class LintError(BaseModel):
    code: str
    message: str
    node_id: str = None
    severity: str = "error"  # error, warning

class AgentLinter:
    """
    The "Compiler" for Lár Agents.
    Sanity-checks the manifest before execution.
    """

    def lint(self, manifest: AgentManifest) -> List[LintError]:
        errors = []
        
        # 1. Build NetworkX Graph
        G = nx.DiGraph()
        node_ids = {n.id for n in manifest.graph.nodes}
        
        # Add nodes
        for node in manifest.graph.nodes:
            G.add_node(node.id, type=node.type)
            
        # Add edges
        for edge in manifest.graph.edges:
            if edge.source not in node_ids:
                errors.append(LintError(code="E001", message=f"Edge source '{edge.source}' does not exist.", severity="error"))
                continue
            if edge.target not in node_ids:
                errors.append(LintError(code="E002", message=f"Edge target '{edge.target}' does not exist.", severity="error"))
                continue
            G.add_edge(edge.source, edge.target)

        # 2. Check Start Node
        if manifest.graph.start_node not in node_ids:
            errors.append(LintError(code="E003", message=f"Start node '{manifest.graph.start_node}' does not exist.", severity="critical"))
            return errors # Cannot proceed without start node

        # 3. Cyclic Graph Detection
        # We allow cycles (loops), but we should warn if there are loops without clear exit conditions (heuristic).
        # For strict DAGs, we would use nx.is_directed_acyclic_graph(G).
        # Here, we just detect simple cycles for information/warning.
        try:
            cycles = list(nx.simple_cycles(G))
            if cycles:
                for cycle in cycles:
                    errors.append(LintError(
                        code="W001", 
                        message=f"Cycle detected: {' -> '.join(cycle)}. Ensure there is an exit condition.", 
                        severity="warning"
                    ))
        except Exception:
            pass # simple_cycles can be expensive on large graphs

        # 4. Orphan Detection (Unreachable from Start)
        # BFS from start node
        reachable = set(nx.descendants(G, manifest.graph.start_node))
        reachable.add(manifest.graph.start_node)
        
        for n_id in node_ids:
            if n_id not in reachable:
                errors.append(LintError(
                    code="W002", 
                    message=f"Node '{n_id}' is unreachable from the start node.", 
                    node_id=n_id,
                    severity="warning"
                ))

        # 5. Schema & Logic Validity
        for node in manifest.graph.nodes:
            # Router Checks
            if node.type == NodeType.ROUTER and isinstance(node, RouterNodeModel):
                for route_val, target_id in node.routes.items():
                    if target_id not in node_ids:
                        errors.append(LintError(
                            code="E004", 
                            message=f"Router '{node.id}' points to non-existent node '{target_id}' for route '{route_val}'.", 
                            node_id=node.id
                        ))
                if node.default_route and node.default_route not in node_ids:
                     errors.append(LintError(
                            code="E005", 
                            message=f"Router '{node.id}' has invalid default route '{node.default_route}'.", 
                            node_id=node.id
                        ))

            # Tool Checks
            if node.type == NodeType.TOOL and isinstance(node, ToolNodeModel):
                if not node.input_keys:
                     errors.append(LintError(
                            code="W003", 
                            message=f"Tool '{node.id}' ({node.tool_name}) has no input keys defined.", 
                            node_id=node.id,
                            severity="warning"
                        ))

        return errors
