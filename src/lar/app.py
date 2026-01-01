import streamlit as st
import pandas as pd
import json
import os
import datetime
import sys
import time

# --- Path Fix for Standalone Run ---
import sys
import os

# 1. Identify the Correct Source Path
# Current file: .../DMN/lar/src/lar/app.py
# Correct src: .../DMN/lar/src
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
correct_src_path = os.path.join(project_root, "src")

# 2. Aggressively Clean sys.path
# Remove any other paths that might contain 'lar' package to avoid conflicts
# We look for paths ending in 'src' that are NOT our correct path
paths_to_remove = [p for p in sys.path if p.endswith("src") and os.path.abspath(p) != correct_src_path]
for p in paths_to_remove:
    if p in sys.path:
        sys.path.remove(p)

# 3. Insert Correct Path at the Very Front
if correct_src_path not in sys.path:
    sys.path.insert(0, correct_src_path)
else:
    # Ensure it is first
    sys.path.remove(correct_src_path)
    sys.path.insert(0, correct_src_path)

# 4. Force Unload 'lar' if it point to the wrong location
if "lar" in sys.modules:
    import lar
    if not lar.__file__.startswith(correct_src_path):
        del sys.modules["lar"]
        # Also clean submodules
        keys_to_del = [k for k in sys.modules.keys() if k.startswith("lar.")]
        for k in keys_to_del:
            del sys.modules[k]

# 5. Import and Verification
try:
    import lar
    from lar.dmn_dreamer import dream
    from lar.consciousness_stream import ConsciousnessStream
    from lar.node import LLMNode, GraphState
except ImportError as e:
    st.error(f"Import failed: {e}")
    st.write(f"Paths: {sys.path}")
    st.stop()

# --- Configuration ---
OLLAMA_URL_GENERATE = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3"
LOG_FILE = os.environ.get("LOG_FILE", os.path.join("logs", "interaction_stream.jsonl"))
MEMORY_FILE = os.environ.get("MEMORY_FILE", os.path.join("memory", "dreams.json"))

st.set_page_config(
    page_title="Lár - Internal State",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown("""
<style>
    .reportview-container {
        background: #0e1117;
    }
    .chat-message {
        padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex;
    }
    .chat-user {
        background-color: #2b313e;
    }
    .chat-assistant {
        background-color: #1c2333;
    }
    .insight-card {
        padding: 1rem;
        background-color: #262730;
        border-radius: 0.5rem;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Brain Setup (The Neuro-Architecture) ---
try:
    from brain.thalamus import Thalamus
except ImportError:
    # Fallback if python path is tricky
    from src.brain.thalamus import Thalamus

if "brain" not in st.session_state:
    st.session_state.brain = Thalamus(log_dir="logs")

# --- Helpers ---
def load_logs():
    if not os.path.exists(LOG_FILE):
        return []
    
    data = []
    try:
        with open(LOG_FILE, "r") as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
    except Exception as e:
        st.error(f"Error reading logs: {e}")
        return []
    
    # Sort by timestamp (Oldest first for chat flow)
    return data

def load_dreams():
    if not os.path.exists(MEMORY_FILE):
        return []
    
    try:
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return list(reversed(data)) # Newest dreams first
            return []
    except Exception as e:
        st.error(f"Error reading memory: {e}")
        return []

# --- Main Data Loading ---
logs = load_logs()

# --- Sidebar ---
st.sidebar.title("🧠 Lár Brain")
st.sidebar.caption("Human-Like Architecture")

# Dynamic Brain State
latest_emotion = "Neutral"
latest_intensity = 0.0
latest_urgency = False

# Fetch latest emotion from logs
if logs and len(logs) > 0:
    last_entry = logs[-1] # Newest is actually last in the list from load_logs, but we display reversed in UI?
    # load_logs returns chronological [old, ..., new]
    # So last entry is new.
    meta = last_entry.get("metadata", {})
    if "emotion" in meta:
        e = meta["emotion"]
        latest_emotion = e.get("primary_emotion", "Neutral")
        latest_intensity = e.get("intensity", 0.0)
        latest_urgency = e.get("is_urgent", False)

# Brain Region Status Modals
with st.sidebar.expander("Amygdala (Emotion)", expanded=True):
    st.write(f"**Emotion**: {latest_emotion}")
    st.write(f"**Intensity**: {latest_intensity:.2f}")
    if latest_urgency:
        st.error("Status: FIGHT OR FLIGHT 🚨")
    else:
        st.success("Status: Nominal ✅")
    st.progress(max(0.0, min(1.0, latest_intensity)))

with st.sidebar.expander("Hippocampus (Memory)"):
    st.write("Status: Active 📚")
    st.write("Role: Semantic Retrieval")

with st.sidebar.expander("Default Mode Network"):
    st.write("Status: Idle 💤")
    st.write("Role: Dreaming & Consolidation")

# Re-init brain if logs were deleted externally (Fix for 'Chat Disappears' bug)
# If logs are empty, it's safer to re-hook the logger ensuring we aren't writing to a deleted inode
if (not os.path.exists(LOG_FILE) or len(logs) == 0) and "brain" in st.session_state:
    st.session_state.brain = Thalamus(log_dir="logs")

# --- Autonomic Status (Sleep Timer) ---
st.sidebar.markdown("---")
st.sidebar.subheader("🔌 Autonomic System")

if os.path.exists(LOG_FILE):
    last_interaction_ts = os.path.getmtime(LOG_FILE)
    now_ts = time.time()
    idle_seconds = now_ts - last_interaction_ts
    sleep_threshold = 30.0 # Must match autonomic_system.py
    
    
    # Live Monitor Mode (Applies to both Active and Sleeping states to show dreams appearing)
    if st.sidebar.checkbox("Live Countdown Mode", value=False, help="Enable to watch timer update and see dreams appear live."):
        time.sleep(1)
        st.rerun()

    if idle_seconds < sleep_threshold:
        time_left = int(sleep_threshold - idle_seconds)
        st.sidebar.info(f"⚡ Brain Active\n\nDreaming in: **{time_left}s**")
        st.sidebar.progress(min(1.0, idle_seconds / sleep_threshold))
    else:
        st.sidebar.success("💤 Brain Sleeping / Dreaming")
        if st.sidebar.button("⏰ Interrupt Sleep"):
            # 1. Log the wake up signal (Updates file timestamp, resetting idle timer)
            # 2. Trigger a conscious response
             with st.spinner("Waking up..."):
                try:
                    # We inject a system prompt to the Brain
                    wake_msg = "User poked you awake. Briefly mention what you were doing or dreaming about."
                    response = st.session_state.brain.process_input(wake_msg, session_id="wakethread")
                    # Force reload to show the response
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Wake error: {e}")
else:
    st.sidebar.warning("System Offline")
    
if st.sidebar.button("🛌 Force R.E.M. Sleep"):
    with st.sidebar.status("Dreaming..."):
        try:
            # Manually trigger the DMN via Thalamus ref
            st.session_state.brain.dmn.activate()
            st.success("Dream complete! Insights consolidated.")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Dream failed: {e}")

# --- Neural Configuration (Model Switcher) ---
st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ Neural Configuration")

def get_ollama_models():
    """Fetches available models from local Ollama instance."""
    try:
        import requests
        # Use localhost inside container to talk to host, or OLLAMA_HOST env
        host = os.environ.get("OLLAMA_HOST", "http://host.docker.internal:11434")
        if not host.startswith("http"): host = f"http://{host}:11434"
        
        # Strip /api/generate if present for the tags endpoint
        base_host = host.replace("/api/generate", "")
        
        response = requests.get(f"{base_host}/api/tags", timeout=2)
        if response.status_code == 200:
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
    except Exception as e:
        # Fallback if offline
        pass
    return ["llama3.2", "qwen2.5:14b", "mistral"]

# Load Config
CONFIG_PATH = "/data/model_config.json"
model_config = {"conscious_model": "llama3.2", "subconscious_model": "qwen2.5:14b"}
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r") as f:
            model_config.update(json.load(f))
    except: pass

available_models = get_ollama_models()

# Ensure current config models are in the list (handle customs)
for m in model_config.values():
    if m not in available_models:
        available_models.append(m)

# UI Controls
conscious_model = st.sidebar.selectbox(
    "☀️ Conscious Mind (Fast)", 
    options=available_models,
    index=available_models.index(model_config["conscious_model"]) if model_config["conscious_model"] in available_models else 0
)

subconscious_model = st.sidebar.selectbox(
    "🌙 Subconscious Mind (Smart)", 
    options=available_models,
    index=available_models.index(model_config["subconscious_model"]) if model_config["subconscious_model"] in available_models else 0
)

# Save & Apply
if conscious_model != model_config["conscious_model"] or subconscious_model != model_config["subconscious_model"]:
    new_config = {
        "conscious_model": conscious_model,
        "subconscious_model": subconscious_model
    }
    with open(CONFIG_PATH, "w") as f:
        json.dump(new_config, f)
    
    # Live update the running brain
    if "brain" in st.session_state:
        # Verify it's not the same to avoid redundant updates?
        # Actually LLMNode handles string updates fine.
        # We assume Ollama format. If the user picked a non-ollama string (e.g. gpt-4), LiteLLM handles it.
        # But our fetching logic assumes Ollama. 
        # For now, we prepend 'ollama/' if it's from the list, ONLY if it doesn't have a provider prefix.
        # But wait, LLMNode logic in Thalamus adds 'ollama/' prefix hardcoded. 
        # We should fix Thalamus to be flexible if we want full LiteLLM support.
        # For now, let's assume Thalamus.cortex needs to be updated.
        
        # We need to hackily update the cortex model_name
        # Thalamus.cortex is an LLMNode.
        # LLMNode.__init__ sets self.model_name.
        # We can just update the attribute.
        
        # Handle the prefix logic that Thalamus usually does
        target_model = conscious_model
        if not "/" in target_model and not target_model.startswith("gpt"):
             target_model = f"ollama/{target_model}"
             
        st.session_state.brain.cortex.model_name = target_model
        st.toast(f"Brain rewired to {conscious_model}")
        time.sleep(0.5)
        st.rerun()

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# --- Main Interface ---
st.title("Lár v1.0.0: Glass Box Consciousness")

tab1, tab2 = st.tabs(["⚡ Short Term Memory (Consciousness)", "💾 Long Term Memory (Subconscious)"])

# --- Tab 1: Short Term Memory ---
with tab1:
    st.header("Short Term Memory (Interaction Log)")
    # logs already loaded above
    
    if not logs:
        st.info("No interactions. Wake the brain up by saying hello!")
    else:
        for entry in logs:
            role = entry.get("role", "unknown")
            content = entry.get("content", "")
            timestamp = entry.get("timestamp", "")
            metadata = entry.get("metadata", {})
            latency = metadata.get("latency_ms", None)
            emotion = metadata.get("emotion", None)

            with st.chat_message(role):
                st.markdown(content)
                caption = f"{timestamp}"
                if latency:
                    caption += f" | ⚡ {latency:.2f}ms"
                if emotion:
                    # visualize emotion tag from Amygdala
                    emo_type = emotion.get('primary_emotion', 'Neutral')
                    intensity = emotion.get('intensity', 0)
                    caption += f" | 🎭 {emo_type} ({intensity:.1f})"
                
                st.caption(caption)

    # --- Chat Input ---
    if prompt := st.chat_input("Stimulate the Thalamus..."):
        # 1. Display User Message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 2. Process via Thalamus
        with st.chat_message("assistant"):
            with st.spinner("Processing in Thalamus..."):
                try:
                    # The Thalamus handles Logging, Amygdala, Hippocampus, and Cortex
                    response = st.session_state.brain.process_input(prompt, session_id="streamlit-session")
                    
                    st.markdown(response)
                    
                    # Rerun to update logs
                    time.sleep(0.5)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Brain Error: {e}")

# --- Tab 2: Long Term Memory ---
with tab2:
    st.header("Long Term Memory (Dreams & Insights)")
    st.caption("Long-Term Memories consolidated by the Default Mode Network")
    
    dreams = load_dreams()
    
    if not dreams:
        st.info("No dreams recorded yet.")
    else:
        for dream in dreams:
            # FIX: Robust timestamp reading
            ts = dream.get("timestamp") or dream.get("dream_timestamp") or "Unknown Time"

            # Hybrid support: older logs have 'log_count' at top, new ones might vary
            count = dream.get("log_count", 0) 
            if count == 0:
                 count = dream.get("analyzed_entries_count", 0)
            if count == 0:
                 # Check metadata (New Standard)
                 meta = dream.get("metadata", {})
                 count = meta.get("log_count", 0)
            
            # --- HYBRID MEMORY SUPPORT (JSON + Chroma) ---
            # New format uses "content", Legacy uses "insights"
            if "content" in dream:
                insights = dream["content"] # Treat 'content' string as the core insight
            else:
                insights = dream.get("insights", [])
            
            # Handling nested insights structure (Recursively unwrap known wrappers)
            # The LLM sometimes wraps the response in { "DMN": { "content": ... } } or { "insights": ... }
            max_depth = 4
            current_depth = 0
            while isinstance(insights, dict) and current_depth < max_depth:
                 current_depth += 1
                 if 'insights' in insights:
                     insights = insights['insights']
                 elif 'DMN' in insights:
                     insights = insights['DMN']
                 elif 'root' in insights:
                     insights = insights['root']
                 else:
                     break
            # Now 'insights' should be the actual payload (List, String, or Dict)
            
            with st.expander(f"🌙 Dream at {ts} (Analyzed {count} memories)", expanded=True):
                # Always show raw data option for debugging
                # Always show raw data option for debugging
                # Checkbox used because nested expanders are not allowed in Streamlit
                dream_id = dream.get("id", str(ts))
                if st.checkbox("🔍 Show Raw Dream Data", key=f"raw_{dream_id}"):
                    if isinstance(insights, (dict, list)):
                        st.json(insights)
                    else:
                        st.info(f"Raw Content: {insights}")

                # 1. Handle List of Strings (Standard)
                if isinstance(insights, list):
                    for item in insights:
                        content = item
                        if isinstance(item, dict):
                            # Try to extract the "meat" of the insight
                            # Check for new keys from "Limitless" prompt?
                            # It usually outputs strings now, but if it outputs objects:
                            content = item.get("insight") or item.get("pattern") or item.get("narrative") or str(item)
                        
                        st.markdown(f"""
                        <div class="insight-card">
                            {content}
                        </div>
                        """, unsafe_allow_html=True)
                
                # 2. Handle Single Dict (Wrapped)
                elif isinstance(insights, dict):
                     # ULTRA-ROBUST STRATEGY: 
                     # Recursively find ALL strings that are longer than 50 chars (likely narrative)
                     # or fallback to specific keys.
                     
                     found_narratives = []
                     
                     def extract_strings(obj):
                         if isinstance(obj, dict):
                             for k, v in obj.items():
                                 if k in ["narrative", "insight", "summary", "content"] and isinstance(v, str):
                                     found_narratives.append(v)
                                 # Limitless prompt sometimes outputs list of dicts with content
                                 elif k == "content" and isinstance(v, list):
                                     for item in v:
                                         if isinstance(item, str): found_narratives.append(item)
                                         elif isinstance(item, dict): extract_strings(item)
                                 else:
                                     extract_strings(v)
                         elif isinstance(obj, list):
                             for item in obj:
                                 extract_strings(item)
                         elif isinstance(obj, str):
                             if len(obj) > 30: # Heuristic to ignore small keys/ids
                                 found_narratives.append(obj)

                     extract_strings(insights)
                     
                     if found_narratives:
                         for text in found_narratives:
                             # Filter out raw JSON dumps if they got caught
                             if "{" in text and "}" in text and len(text) > 100: continue 
                             
                             st.markdown(f"""
                                <div class="insight-card">
                                    {text}
                                </div>
                                """, unsafe_allow_html=True)
                     else:
                         st.warning("No narrative text found in dream structure.")
                         st.json(insights)
                
                # 3. Handle Raw String
                elif isinstance(insights, str):
                    st.markdown(f"""
                        <div class="insight-card">
                            {insights}
                        </div>
                        """, unsafe_allow_html=True)

# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.caption("Lár v1.0.0")
