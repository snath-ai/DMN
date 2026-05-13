from typing import Dict, Any, Optional


class TokenTracker:
    """
    Tracks token usage across different models during graph execution.
    
    This class aggregates token consumption data for cost tracking and
    observability, supporting multiple LLM providers simultaneously.
    """
    
    def __init__(self):
        """Initialize the TokenTracker with zero counts."""
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0
        self.total_tokens: int = 0
        self.tokens_by_model: Dict[str, int] = {}
    
    def add_tokens(self, metadata: Optional[Dict[str, Any]]) -> None:
        """
        Add token usage from a single node execution.
        
        Args:
            metadata (dict, optional): The run_metadata from an LLMNode execution,
                containing:
                - prompt_tokens (int): Tokens in the input
                - output_tokens (int): Tokens in the output
                - total_tokens (int): Sum of prompt + output
                - model (str): Model identifier (e.g., "gpt-4", "gemini-pro")
        """
        if not metadata or not isinstance(metadata, dict):
            return
        
        # Extract token counts (default to 0 if missing)
        prompt_tokens = metadata.get("prompt_tokens", 0)
        completion_tokens = metadata.get("output_tokens", 0)
        total = metadata.get("total_tokens", 0)
        model_name = metadata.get("model", "unknown")
        
        # Aggregate totals
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_tokens += total
        
        # Track per-model breakdown
        if model_name not in self.tokens_by_model:
            self.tokens_by_model[model_name] = 0
        self.tokens_by_model[model_name] += total
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get aggregated token statistics.
        
        Returns:
            dict: Summary containing:
                - total_prompt_tokens (int): Total input tokens
                - total_completion_tokens (int): Total output tokens
                - total_tokens (int): Total tokens across all models
                - tokens_by_model (dict): Breakdown by model name
        """
        return {
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "tokens_by_model": self.tokens_by_model.copy()
        }
    
    def reset(self) -> None:
        """Reset all counters (useful for reusing the tracker)."""
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.tokens_by_model = {}
