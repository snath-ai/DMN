import os
import sys
from dotenv import load_dotenv
load_dotenv()
# LiteLLM Helper: Map GOOGLE_API_KEY to GEMINI_API_KEY if needed
if os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.getenv("GOOGLE_API_KEY")

import json
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from lar.node import LLMNode, ToolNode
from lar.executor import GraphExecutor

"""
Example 6: Structured JSON Output
--------------------------------
Concepts:
- Enforcing strict output formats
- Post-processing LLM strings into dicts
"""

# 1. JSON Generator
extractor = LLMNode(
    model_name="gemini/gemini-2.5-pro",
    prompt_template=(
        "Extract entities from: '{text}'. "
        "Return strictly valid JSON with keys: 'names' (list), 'dates' (list). "
        "No markdown code blocks."
    ),
    output_key="raw_json"
)

# 2. Parser Tool
def parse_json(state):
    raw = state.get("raw_json", "{}")
    # Clean up markdown if model disobeys
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(raw)
        return data # Merges into state keys: 'names', 'dates'
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse JSON: {e}"}

parser = ToolNode(
    tool_function=parse_json,
    input_keys=["__state__"],
    output_key=None, # Merge result dict into state
    next_node=None
)

# Wiring
extractor.next_node = parser

if __name__ == "__main__":
    executor = GraphExecutor()
    text = "John met Sarah on 2023-12-05 for lunch."
    
    print(f"--- Extracting from: '{text}' ---")
    for step in executor.run_step_by_step(extractor, {"text": text}):
        if step['node'] == "ToolNode":
            diff = step['state_diff'].get("added", {})
            print(f"Names: {diff.get('names')}")
            print(f"Dates: {diff.get('dates')}")
