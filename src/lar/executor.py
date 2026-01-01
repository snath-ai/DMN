import copy
import json
import os
import datetime
import uuid
from .node import BaseNode
from .state import GraphState
from .utils import compute_state_diff


class SecurityError(Exception):
    """Raised when a security policy (like Air-Gap) is violated."""
    pass

class GraphExecutor:
    """
    The "engine" that runs a Lár graph.
    
    For Air-Gap / Offline Mode support, please see Snath Enterprise:
    https://snath.ai/enterprise
    """
    def __init__(self, log_dir: str = "lar_logs", offline_mode: bool = False, user_id: str = None):
        self.log_dir = log_dir
        self.offline_mode = offline_mode
        self.user_id = user_id
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def _check_enterprise_policy(self, node, node_name: str):
        """
        Hook for Enterprise Security Policies (Air-Gap, PII Masking, etc).
        In OSS, this is a no-op.
        In Snath Enterprise, this enforces 21 CFR Part 11 compliance.
        """
        # Enterprise Hooks go here.
        # See: https://snath.ai/enterprise
        pass


    def _save_log(self, history: list, run_id: str, summary: dict = None):
        """Saves the execution history to a JSON file."""
        filename = f"{self.log_dir}/run_{run_id}.json"
        
        log_data = {
            "run_id": run_id,
            "user_id": self.user_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "steps": history,
            "summary": summary or {}
        }

        try:
            with open(filename, "w") as f:
                json.dump(log_data, f, indent=2)
            print(f"\n✅ [GraphExecutor] Audit log saved to: {filename}")
        except Exception as e:
            print(f"\n⚠️ [GraphExecutor] Failed to save log: {e}")


    def run_step_by_step(self, start_node: BaseNode, initial_state: dict, max_steps: int = 100):
        """
        Executes a graph step-by-step, yielding the history of each step as it completes.
        This generator pattern allows for real-time observability and "Flight Recording".

        Args:
            start_node (BaseNode): The entry point of the graph.
            initial_state (dict): The initial dictionary to populate the GraphState.
            max_steps (int, optional): Safety circuit breaker to prevent infinite loops. Defaults to 100.
        
        Yields:
            dict: An audit log entry containing:
                - step (int): Step index.
                - node (str): Class name of the executed node.
                - state_before (dict): Full state snapshot before execution.
                - state_diff (dict): What changed in this step (added/updated/removed).
                - run_metadata (dict): Token usage and model info.
                - outcome (str): "success" or "error".
        """
        state = GraphState(initial_state)
        current_node = start_node

        # Generate a unique ID for this run (UUIDv4)
        run_id = str(uuid.uuid4())
        history = [] # We keep a local copy to save at the end
        
        # Initialize token counters
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0

        step_index = 0
        while current_node is not None:
            node_name = current_node.__class__.__name__
            state_before = copy.deepcopy(state.get_all())
            
            log_entry = {
                "step": step_index,
                "node": node_name,
                "state_before": state_before,
                "state_diff": {},
                "run_metadata": {}, 
                "outcome": "pending"
            }
            
            try:
                # 2. Enterprise Policy Hook
                self._check_enterprise_policy(current_node, node_name)

                # 3. Execute the node
                next_node = current_node.execute(state)
                
                # Check if the node set an error in the state (graceful error handling)
                if state.get("last_error"):
                    log_entry["outcome"] = "error"
                    log_entry["error"] = state.get("last_error")
                    # If no error handler (next_node is None/ErrorNode), we consider it a failure step
                else:
                    log_entry["outcome"] = "success"
                
            except Exception as e:
                # 3. Handle a critical error
                print(f"  [GraphExecutor] CRITICAL ERROR in {node_name}: {e}")
                log_entry["outcome"] = "error"
                log_entry["error"] = str(e)
                next_node = None 
            
            # 4. Capture the state *after* the node runs
            state_after = copy.deepcopy(state.get_all())
            
             # Extract metadata
            if "__last_run_metadata" in state_after:
                metadata = state_after.pop("__last_run_metadata")
                log_entry["run_metadata"] = metadata
                
                # Aggregate tokens if present
                if metadata and isinstance(metadata, dict):
                    total_prompt_tokens += metadata.get("prompt_tokens", 0)
                    total_completion_tokens += metadata.get("output_tokens", 0)
                    total_tokens += metadata.get("total_tokens", 0)
            
            # 5. Clear metadata from the actual state so it doesn't persist
            state.set("__last_run_metadata", None)

            # 6. Compute the diff (now on the *cleaned* state_after)
            state_diff = compute_state_diff(state_before, state_after)
            log_entry["state_diff"] = state_diff

            # 7. Step Output Logging
            # Log the step metadata
            pass

            # Add to history and yield
            history.append(log_entry)
            yield log_entry
            
            
            '''# 7. Yield the log of this step and pause
            yield log_entry '''
            
            # 8. Resume on the next call
            current_node = next_node
            step_index += 1
            
            # --- CIRCUIT BREAKER ---
            if step_index >= max_steps:
                print(f"  [GraphExecutor] 🛑 CIRCUIT BREAKER TRIPPED: Exceeded {max_steps} steps.")
                
                # Log the termination event
                log_entry = {
                    "step": step_index,
                    "node": "CircuitBreaker",
                    "state_before": {},
                    "state_diff": {}, 
                    "run_metadata": {},
                    "outcome": "error",
                    "error": f"Maximum steps exceeded ({max_steps}). Infinite loop detected."
                }
                history.append(log_entry)
                yield log_entry
                break

        # --- AUTO-SAVE LOG ON FINISH ---
        summary = {
            "total_steps": step_index,
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens
        }
        self._save_log(history, run_id, summary)

    def save_to_file(self, filename: str, start_node: BaseNode, name: str = "My Agent"):
        """
        Serializes the graph logic starting from 'start_node' to a JSON file.
        This enables 'Write Once, Run Anywhere' deployment.
        """
        from .serializer import export_graph_to_json
        
        json_output = export_graph_to_json(start_node, name=name)
        
        with open(filename, "w") as f:
            f.write(json_output)
        
        print(f"\n📦 [GraphExecutor] Agent serialized to: {filename}")