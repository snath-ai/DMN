import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path to allow imports
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(base_dir, "src"))
sys.path.append(os.path.join(base_dir, "src", "lar"))

os.environ["OLLAMA_MODEL"] = "ollama/llama3.2"

from brain.thalamus import Thalamus

def run_test():
    print("🧠 Starting DMN v2 Verification Protocol...")
    
    t = Thalamus()
    
    # 1. Inject some fake complex memory chunks to force retrieval
    print("\\n[Test] Injecting fake cold/warm memories...")
    for i in range(5):
        t.hippocampus.save_memory(
            f"User asked a highly complex question about quantum mechanics {i}. The response was detailed and very long, containing multiple formulas and philosophical interpretations of the many-worlds theory.",
            [0.1] * 3072, # Fake simple embedding
            {"source": "test_injector"}
        )
        t.hippocampus.save_warm_memory(
            f"Summary {i}: Detailed discussion on quantum mechanics and philosophical implications.",
            [0.2] * 3072,
            {"source": "test_injector"}
        )
    
    print("\\n[Test] Sending Query to Thalamus (Expect Prefrontal Compression)...")
    res = t.process_input("What have we discussed recently about quantum theory?")
    
    print("\\n[Thalamus Output]:")
    print(res)

if __name__ == "__main__":
    run_test()
