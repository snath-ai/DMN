import json
import inspect
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Set, List

def export_graph_to_json(
    start_node, 
    name: str = "My Agent", 
    description: str = "",
    agent_id: str = None,
    author: str = "User",
    version: str = "1.0.0"
) -> str:
    """
    Traverses a Lár graph starting from 'start_node' and serializes it to a 
    LARASpec-compliant JSON string.
    """
    
    # 1. Metadata & Versioning
    manifest = {
        "metadata": {
            "id": agent_id or str(uuid.uuid4()),
            "name": name,
            "description": description,
            "author": author,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "tags": []
        },
        "version": {
            "version": version,
            "changelog": []
        },
        "security": {
            "allow_env_access": True,
            "allowed_tools": []
        },
        "graph": {
            "start_node": "", # Will be set later
            "nodes": [],
            "edges": []
        },
        "env_vars": {}
    }

    # 2. Graph Traversal (BFS)
    # Map object IDs to node names (e.g., "node_1", "node_2")
    node_id_to_name = {}
    node_counter = 0

    def get_node_name(node):
        nonlocal node_counter
        if node is None:
            return None
        if id(node) not in node_id_to_name:
            node_counter += 1
            node_id_to_name[id(node)] = f"node_{node_counter}"
        return node_id_to_name[id(node)]

    # Pre-pass to assign names
    queue = [start_node]
    visited_ids = {id(start_node)}
    get_node_name(start_node) # Ensure start node gets a name

    while queue:
        current = queue.pop(0)
        
        neighbors = []
        if hasattr(current, "next_node") and current.next_node:
            neighbors.append(current.next_node)
        if hasattr(current, "path_map"): # RouterNode
            neighbors.extend(current.path_map.values())
        if hasattr(current, "default_node") and current.default_node: # RouterNode
            neighbors.append(current.default_node)
        if hasattr(current, "error_node") and current.error_node: # ToolNode
            neighbors.append(current.error_node)
            
        for neighbor in neighbors:
            if id(neighbor) not in visited_ids:
                visited_ids.add(id(neighbor))
                get_node_name(neighbor)
                queue.append(neighbor)

    # 3. Serialization Pass
    processing_queue = [start_node]
    processed_ids = set()
    
    # Set start node in manifest
    manifest["graph"]["start_node"] = get_node_name(start_node)

    while processing_queue:
        current = processing_queue.pop(0)
        if id(current) in processed_ids:
            continue
        processed_ids.add(id(current))
        
        node_name = get_node_name(current)
        node_type = current.__class__.__name__
        
        # Base Node Model
        node_model = {
            "id": node_name,
            "type": node_type,
            "position": {"x": 0, "y": 0} # Placeholder for auto-layout
        }
        
        # Type-specific attributes & Edges
        if node_type == "AddValueNode":
            node_model["key"] = current.key
            node_model["value"] = current.value
            
            if current.next_node:
                target_name = get_node_name(current.next_node)
                manifest["graph"]["edges"].append({
                    "source": node_name,
                    "target": target_name
                })
                processing_queue.append(current.next_node)
            
        elif node_type == "LLMNode":
            node_model["model_name"] = current.model_name
            node_model["prompt_template"] = current.prompt_template
            node_model["output_key"] = current.output_key
            if current.system_instruction:
                node_model["system_instruction"] = current.system_instruction
            
            if current.next_node:
                target_name = get_node_name(current.next_node)
                manifest["graph"]["edges"].append({
                    "source": node_name,
                    "target": target_name
                })
                processing_queue.append(current.next_node)
            
        elif node_type == "ToolNode":
            try:
                code = inspect.getsource(current.tool_function)
            except OSError:
                code = "# Could not retrieve source code."
            
            node_model["code"] = code
            node_model["function_name"] = current.tool_function.__name__
            node_model["input_keys"] = current.input_keys
            node_model["output_key"] = current.output_key
            
            # Add to allowed tools security list
            if current.tool_function.__name__ not in manifest["security"]["allowed_tools"]:
                manifest["security"]["allowed_tools"].append(current.tool_function.__name__)

            if current.next_node:
                target_name = get_node_name(current.next_node)
                manifest["graph"]["edges"].append({
                    "source": node_name,
                    "target": target_name
                })
                processing_queue.append(current.next_node)
            
        elif node_type == "RouterNode":
            try:
                code = inspect.getsource(current.decision_function)
            except OSError:
                code = "# Could not retrieve source code."
                
            node_model["code"] = code
            node_model["function_name"] = current.decision_function.__name__
            
            routes = {}
            for route_key, target_node in current.path_map.items():
                target_name = get_node_name(target_node)
                routes[route_key] = target_name
                
                # Add conditional edge
                manifest["graph"]["edges"].append({
                    "source": node_name,
                    "target": target_name,
                    "condition": route_key
                })
                
                if target_node: processing_queue.append(target_node)
            
            node_model["routes"] = routes
            
            if current.default_node:
                target_name = get_node_name(current.default_node)
                node_model["default_route"] = target_name # Spec uses default_route, not default_node
                
                # Add default edge (no condition implies default if router? Or explicit default?)
                # Spec usually implies default route is just another edge but handled by logic.
                # Let's add it as an edge without condition, or maybe we don't need to if routes cover it?
                # Actually, for RouterNode, the edges are derived from routes. 
                # The default route is a fallback. We should add an edge for it too?
                # Let's add it as an edge with condition="DEFAULT" or just rely on the node_model.
                # For visualization, we definitely need an edge.
                manifest["graph"]["edges"].append({
                    "source": node_name,
                    "target": target_name,
                    "condition": "DEFAULT" 
                })
                processing_queue.append(current.default_node)
            
        elif node_type == "ClearErrorNode":
            if current.next_node:
                target_name = get_node_name(current.next_node)
                manifest["graph"]["edges"].append({
                    "source": node_name,
                    "target": target_name
                })
                processing_queue.append(current.next_node)

        manifest["graph"]["nodes"].append(node_model)

    return json.dumps(manifest, indent=2)
