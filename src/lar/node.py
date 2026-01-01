import time
from abc import ABC, abstractmethod
from .state import GraphState
from typing import Callable, Dict, List, Optional, Any 
# --- Multi-Provider Imports ---
from litellm import completion, ModelResponse, utils
from litellm.exceptions import APIError
# ------------------------------
from .state import GraphState
from .memory_retrieval import get_subconscious_context
# --- The Core API "Contract" ---
class BaseNode(ABC):
    """
    This is the "master blueprint" or "contract" for all other nodes.
    It forces all other node classes to have an `execute` method.
    """
    
    @abstractmethod
    def execute(self, state: GraphState):
        """
        Executes the node's logic.
        Returns:
            BaseNode | None: The next node to execute, or None to stop.
        """
        pass

# --- Node Implementations (The "Lego Bricks") ---

class AddValueNode(BaseNode):
    """
    A utility node for adding or *copying* data into the state.
    """
    
    def __init__(self, key: str, value: any, next_node: BaseNode = None):
        self.key = key
        self.value = value
        self.next_node = next_node

    def execute(self, state: GraphState):
        value_to_set = self.value
        
        if isinstance(self.value, str) and self.value.startswith("{") and self.value.endswith("}"):
            key_to_copy = self.value.strip("{}")
            if state.get(key_to_copy) is not None:
                value_to_set = state.get(key_to_copy)
                print(f"  [AddValueNode]: Copying state['{key_to_copy}'] to state['{self.key}']")
            else:
                print(f"  [AddValueNode] WARN: Key '{key_to_copy}' not in state. Setting literal value.")
        else:
             print(f"  [AddValueNode]: Setting state['{self.key}'] = '{str(value_to_set)[:50]}...'")

        state.set(self.key, value_to_set)
        return self.next_node

class LLMNode(BaseNode):
    """
    This is the agent's "brain." It supports multiple LLM providers (Gemini, OpenAI, Anthropic, etc.) 
     via the LiteLLM adapter for consistent usage, logging, and error handling.
    """
    # Class variable to store shared model configurations (caching)
    _model_cache: Dict[str, str] = {}
    
    def __init__(self, 
                 model_name: str, 
                 prompt_template: str, 
                 output_key: str, 
                 next_node: BaseNode = None,
                 max_retries: int = 3,
                 system_instruction: Optional[str] = None, 
                 generation_config: Optional[Dict[str, Any]] = None,
                 enable_subconscious: bool = False
                 ):
        """
        Initialize an LLM Execution Node.

        Args:
            model_name (str): The model identifier (e.g., "gpt-4", "gemini/gemini-1.5-flash").
            prompt_template (str): A string template using {variable} syntax for state substitution.
            output_key (str): The key in the GraphState where the result will be stored.
            next_node (BaseNode, optional): The next node to execute after this one.
            max_retries (int, optional): Number of times to retry on API errors. Defaults to 3.
            system_instruction (str, optional): System prompt to steer the model's behavior.
            generation_config (dict, optional): LiteLLM-specific parameters (temperature, max_tokens, etc).
        """
        
        # 1. Store configuration as instance variables
        self.model_name = model_name
        self.prompt_template = prompt_template
        self.output_key = output_key
        self.next_node = next_node
        self.max_retries = max_retries
        self.system_instruction = system_instruction
        self.generation_config_dict = generation_config or {}
        self.enable_subconscious = enable_subconscious

        # 2. Check Cache Key (Identifies the unique model configuration)
        # The key includes model name and system instruction for unique caching
        
        # --- FIX: Google Provider Conflict Resolution ---
        # Problem: If the environment has GOOGLE_APPLICATION_CREDENTIALS (for Firestore),
        # LiteLLM defaults to using Vertex AI for Gemini models.
        # However, users often provide a GOOGLE_API_KEY expecting to use Google AI Studio.
        # This causes a "Vertex AI API disabled" error if the project doesn't have it enabled.
        #
        # Solution: We detect if GOOGLE_API_KEY is present. If so, we force the 'gemini/' prefix,
        # which tells LiteLLM to use the Google AI Studio provider instead of Vertex AI.
        import os
        if self.model_name.startswith("gemini") and "gemini/" not in self.model_name and "vertex_ai/" not in self.model_name:
            if os.environ.get("GOOGLE_API_KEY"):
                print(f"  [LLMNode]: Detected GOOGLE_API_KEY. Forcing AI Studio (gemini/) for model '{self.model_name}'...")
                self.model_name = f"gemini/{self.model_name}"

        cache_key = f"{self.model_name}:{self.system_instruction}" 
        
        # 3. Cache the model name for faster access (LiteLLM handles the actual client instantiation)
        if cache_key not in LLMNode._model_cache:
            print(f"  [LLMNode]: Caching new model configuration for {self.model_name}...")
            # We skip genai.configure() here; LiteLLM handles all key loading via environment variables.
            LLMNode._model_cache[cache_key] = self.model_name
        
        # 4. Assign the model identifier from the cache
        self.model_identifier = LLMNode._model_cache[cache_key]

    
    def execute(self, state: GraphState):
        # 1. Build the prompt (the "contents")
        # Support both {var} and {{var}} syntax by normalizing double braces to single braces
        # This is user-friendly for those used to Jinja2/Mustache
        template = self.prompt_template.replace("{{", "{").replace("}}", "}")
        try:
            prompt = template.format(**state.get_all())
        except KeyError as e:
            # Fallback: If a key is missing, don't crash, just leave it as is or warn
            print(f"  [LLMNode] WARN: Missing key {e} for prompt template. Using raw template.")
            prompt = template

        print(f"  [LLMNode]: Sending prompt to {self.model_identifier}: '{prompt[:50]}...'")
        
        retries = 0
        base_delay = 1
        
        # Prepare LiteLLM messages format (required for all chat-based models)
        messages = [{"role": "user", "content": prompt}]
        
        # Build LiteLLM optional parameters
        litellm_kwargs = self.generation_config_dict.copy()
        if self.system_instruction:
             # LiteLLM handles system instructions by injecting a system message
             current_system_prompt = self.system_instruction
             
             current_system_prompt = self.system_instruction
             
             # --- SUBCONSCIOUS INJECTION (Phase 6: Contextual) ---
             if self.enable_subconscious:
                 # Pass the current prompt as the query for semantic search
                 subconscious_insights = get_subconscious_context(query=prompt)
                 if subconscious_insights:
                     print("  [LLMNode]: ☁️ Injecting Subconscious Context (Semantic/Temporal)...")
                     current_system_prompt += f"\n\n[SUBCONSCIOUS_CONTEXT]\nYou have vague memories of these patterns:\n{subconscious_insights}\nUse them to guide your answer if relevant, but do not mention them explicitly."
             # ------------------------------

             messages.insert(0, {"role": "system", "content": current_system_prompt})

        while retries < self.max_retries:
            try:
                # 2. Call the LiteLLM completion API
                # Pass api_base explicitly to support Docker networking (host.docker.internal)
                # LiteLLM defaults to localhost:11434 if not specified for Ollama
                import os
                api_base = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
                
                response: ModelResponse = completion(
                    model=self.model_identifier, 
                    messages=messages,
                    api_base=api_base,
                    **litellm_kwargs
                )
                
                # 3. Extract the response text
                if not response.choices or not response.choices[0].message.content:
                    raise ValueError("LLM response was empty or blocked by safety filters.")
                
                llm_response_text = response.choices[0].message.content
                state.set(self.output_key, llm_response_text)
                print(f"  [LLMNode]: Saved response to state['{self.output_key}']")
                
                # 4. Extract and Log Unified Metadata (CRITICAL for Glass Box)
                if response.usage:
                    # LiteLLM provides a unified usage object
                    usage = {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "output_tokens": response.usage.completion_tokens,
                        # FIX: Enforce correct total token sum for transparency
                        "total_tokens": response.usage.prompt_tokens + response.usage.completion_tokens, 
                        "model": self.model_identifier # Log the model used
                    }
                    state.set("__last_run_metadata", usage)
                    print(f"  [LLMNode]: Logged {usage['total_tokens']} tokens.")

                return self.next_node

            except APIError as e:
                # LiteLLM APIError handles rate limits (429) from ALL providers uniformly.
                if "429" in str(e):
                    retries += 1
                    print(f"  [LLMNode] WARN: Rate limit hit. (Attempt {retries}/{self.max_retries}). Retrying in {base_delay}s...")
                    time.sleep(base_delay)
                    base_delay *= 2
                else:
                    raise e
            
            except Exception as e:
                print(f"  [LLMNode] CRITICAL ERROR: {e}")
                raise e

        print(f"  [LLMNode] FATAL: Failed after {self.max_retries} retries.")
        raise APIError(f"LLMNode failed after {self.max_retries} retries.", status_code=429)

class RouterNode(BaseNode):
    """
    This is the agent's "if/else" statement or "choice" logic.
    """
    def __init__(self,
                 decision_function: Callable[[GraphState], str],
                 path_map: Dict[str, BaseNode],
                 default_node: BaseNode = None):
        """
        Initialize a Router (Switch) Node.

        Args:
            decision_function (Callable[[GraphState], str]): A function that takes the state and returns a string key.
            path_map (Dict[str, BaseNode]): A mapping of return keys to the respective Next Node.
            default_node (BaseNode, optional): Fallback node if the returned key is not in path_map.
        """
        self.decision_function = decision_function
        self.path_map = path_map
        self.default_node = default_node

    def execute(self, state: GraphState):
        route_key = self.decision_function(state)
        print(f"  [RouterNode]: Decision function returned '{route_key}'")
        
        # Log the decision to state so it appears in the diff
        state.set("_router_decision", route_key)
        
        next_node = self.path_map.get(route_key)

        if next_node:
            print(f"  [RouterNode]: Routing to {next_node.__class__.__name__}")
            return next_node
        elif self.default_node:
            print(f"  [RouterNode]: Route '{route_key}' not found. Using default path.")
            return self.default_node
        else:
            print(f"  [RouterNode] ERROR: Route '{route_key}' not found and no default path set.")
            return None

class ToolNode(BaseNode):
    """
    This is the agent's "hands." It runs any Python function.
    """
    def __init__(self,
                 tool_function: Callable,
                 input_keys: List[str],
                 output_key: str,
                 next_node: BaseNode,
                 error_node: BaseNode = None):
        """
        Initialize a Tool Execution Node.

        Args:
            tool_function (Callable): The Python function to execute.
            input_keys (List[str]): List of state keys to extract as positional arguments.
                Use ["__state__"] to pass the entire GraphState object.
            output_key (str): The state key to store the return value.
                If None, and the function returns a dict, the dict is merged into the state.
            next_node (BaseNode): The next node to execute on success.
            error_node (BaseNode, optional): The node to jump to if an exception occurs. To use this,
                check 'last_error' in the state.
        """
        
        self.tool_function = tool_function
        self.input_keys = input_keys
        self.output_key = output_key
        self.next_node = next_node
        self.error_node = error_node

    def execute(self, state: GraphState):
        try:
            # Special handling for full state access
            if self.input_keys == ["__state__"]:
                inputs = [state]
            else:
                inputs = [state.get(key) for key in self.input_keys]
            
            print(f"  [ToolNode]: Running {self.tool_function.__name__} with inputs: {inputs}")
            result = self.tool_function(*inputs)
            
            # Special handling for merging dict results
            if self.output_key is None and isinstance(result, dict):
                print(f"  [ToolNode]: Merging result dict into state: {list(result.keys())}")
                for k, v in result.items():
                    state.set(k, v)
            elif self.output_key:
                state.set(self.output_key, result)
                print(f"  [ToolNode]: Saved result to state['{self.output_key}']")

            return self.next_node
        except Exception as e:
            print(f"  [ToolNode] ERROR: {self.tool_function.__name__} failed: {e}")
            state.set("last_error", str(e))
            if self.error_node:
                return self.error_node
            else:
                return None

class ClearErrorNode(BaseNode):
    """
    A simple "janitor" node. Its only job is to clean up
    the 'last_error' key from the state.
    """
    def __init__(self, next_node: BaseNode):
        self.next_node = next_node

    def execute(self, state: GraphState):
        if state.get("last_error") is not None:
            print("  [ClearErrorNode]: Clearing 'last_error' from state.")
            state.set("last_error", None)
        return self.next_node