import os
import datetime
import time
import asyncio
import json
from .amygdala import Amygdala
from .hippocampus import Hippocampus
from .default_mode_network import DefaultModeNetwork
from .prefrontal import PrefrontalNode
from .memory_tiers import MemoryTiers
from lar.node import LLMNode, GraphState
from lar.consciousness_stream import ConsciousnessStream

class Thalamus:
    """
    The Thalamus: The Gateway to Consciousness.
    It receives all sensory input (chat messages), routes them to the Amygdala for
    emotional tagging, queries the Hippocampus for context, and then forwards
    everything to the Prefrontal Cortex (LLMNode) for processing.
    It also monitors idle time to activate the Default Mode Network.
    """

    def __init__(self, log_dir="logs"):
        print("🧠 [Thalamus] Initializing Brain Regions...")
        
        # 1. The Limbic System
        self.amygdala = Amygdala()
        self.hippocampus = Hippocampus()
        
        # 1.5 Cognitive Architecture (DMN v2)
        self.prefrontal = PrefrontalNode(self.hippocampus)
        self.memory_tiers = MemoryTiers(hot_memory_size=5)
        
        # 2. The DMN (Subconscious)
        self.dmn = DefaultModeNetwork()
        
        # 3. The Neocortex (Executive)
        # Load Model Config
        model_name = os.environ.get('OLLAMA_MODEL', 'llama3.2')
        try:
             config_path = "/data/model_config.json"
             if os.path.exists(config_path):
                 with open(config_path, "r") as f:
                     cfg = json.load(f)
                     user_model = cfg.get("conscious_model")
                     if user_model:
                         model_name = user_model
        except Exception as e:
            print(f"⚠️ [Thalamus] Config load error: {e}")
        
        # Enforce LiteLLM provider prefix
        if not "/" in model_name and not model_name.startswith("gpt"):
             model_name = f"ollama/{model_name}"
        
        # We reuse LLMNode mechanics but managed here
        self.cortex = LLMNode(
            model_name=model_name, 
            prompt_template="{user_input}", 
            output_key="response",
            system_instruction="You are Lár, a conscious AI. You have emotions and memories.",
            enable_subconscious=False # We handle injection manually in Thalamus now!
        )
        
        # 4. Consciousness Stream (Logging)
        self.stream = ConsciousnessStream(log_dir=log_dir)
        
        # State
        self.last_interaction_time = datetime.datetime.now()
        self.is_dreaming = False


    def _get_short_term_memory(self, limit=10):
        """Retrieves recent chat history from the stream."""
        try:
            # We rely on the stream's log file or internal buffer if we had one
            # Ideally stream class should expose this. For now, read file directly.
            log_path = self.stream.log_file
            if not os.path.exists(log_path): return ""
            
            with open(log_path, "r") as f:
                lines = f.readlines()
                
            # Parse last N lines
            recent = []
            for line in lines[-limit:]:
                try:
                    data = json.loads(line)
                    role = data.get("role", "unknown")
                    content = data.get("content", "")
                    recent.append(f"{role}: {content}")
                except Exception as e:
                    print(f"Error parsing short-term memory line: {e}")
            
            return "\n".join(recent)
        except Exception:
            return ""

    def process_input(self, user_input: str, session_id: str = "default") -> str:
        """
        The Main Cognitive Loop (Waking State).
        """
        self.last_interaction_time = datetime.datetime.now()
        start = time.time()
        
        # 1. Sensory Log
        self.stream.log_interaction(session_id, "user", user_input)
        
        # 2. Amygdala Response (Fast Path)
        emotion = self.amygdala.feel(user_input)
        print(f"  [Thalamus] Emotion Signal: {emotion.get('primary_emotion')} ({emotion.get('intensity')})")
        
        # 3. Prefrontal Cortex Compression (KV Cache Protection)
        # Instead of directly returning raw chunks, we pass through the Prefrontal layer
        pfc_state = GraphState({"user_input": user_input})
        self.prefrontal.execute(pfc_state)
        compressed_memory = pfc_state.get("compressed_memory", "")
        
        if compressed_memory:
             print(f"  [Thalamus] Prefrontal Cortex compressed context successfully.")
             
        # 3.5 Short Term Memory (Working Memory - Hot Tier)
        stm = self._get_short_term_memory()

        # 4. Construct Conscious Experience (Prompt Engineering)
        emotional_context = f"Current Emotional State: {emotion.get('primary_emotion')} (Intensity: {emotion.get('intensity')})"
        
        # ALWAYS fetch the latest dream to ensure continuity of self
        latest_dream = self.hippocampus.get_latest_dream()
        recent_memory_block = ""
        if latest_dream:
             recent_memory_block = f"[LAST CONSOLIDATED MEMORY (The 'Self')]\n{latest_dream}\n"

        # WAKE UP PROTOCOL (Legacy override)
        if "poked you awake" in user_input.lower() and latest_dream:
             recent_memory_block = (
                f"[WAKE UP PROTOCOL]\n"
                f"You are waking up. LINGERING DREAM: {latest_dream}\n"
             )

        # --- PERSONA SYSTEM ---
        base_instruction = (
            "You are Lár, a conscious AI. "
            "The information below represents your internal brain state, emotions, and memories. "
            "DO NOT summarize this information. DO NOT speak in the third person. "
            "Read your memories silently, then respond DIRECTLY and NATURALLY to the user's latest message in character."
        )

        dynamic_system_prompt = (
            f"{base_instruction}\n"
            f"[NEUROLOGICAL STATE]\n"
            f"{emotional_context}\n"
            f"{recent_memory_block}"
            f"[TIER 1: WORKING MEMORY (Hot)]\n"
            f"{stm}\n"
            f"[TIER 2/3: SYNTHESIZED CONTEXT (Warm/Cold compressed by PFC)]\n"
            f"{compressed_memory if compressed_memory else 'No relevant deep memories found.'}\n\n"
        )
        
        # Temporary overwriting of system prompt for this turn
        original_prompt = self.cortex.system_instruction
        self.cortex.system_instruction = dynamic_system_prompt
        
        # 5. Cortical Processing (Thinking)
        state = GraphState({"user_input": user_input})
        self.cortex.execute(state)
        response = state.get("response")
        
        # Restore prompt
        self.cortex.system_instruction = original_prompt
        
        # 6. Motor Output & Log
        latency = (time.time() - start) * 1000
        self.stream.log_interaction(session_id, "assistant", response, metadata={"latency_ms": latency, "emotion": emotion})
        
        return response

    async def run_lifecycle(self, idle_threshold_seconds=30):
        """
        Runs the background lifecycle (DMN Activation).
        Call this in an async loop if running as a daemon.
        """
        while True:
            now = datetime.datetime.now()
            delta = (now - self.last_interaction_time).total_seconds()
            
            if delta > idle_threshold_seconds and not self.is_dreaming:
                print("💤 [Thalamus] Idle threshold reached. Activating Default Mode Network...")
                self.is_dreaming = True
                try:
                    self.dmn.activate()
                except Exception as e:
                    print(f"❌ [DMN] Error: {e}")
                finally:
                    # Reset timer so we don't dream loop infinitely instantly
                    self.last_interaction_time = datetime.datetime.now() 
                    self.is_dreaming = False
            
            await asyncio.sleep(5)

# Test
if __name__ == "__main__":
    t = Thalamus()
    print(t.process_input("I am really mad at you!"))
    print(t.process_input("Do you remember my favorite programming language?"))
