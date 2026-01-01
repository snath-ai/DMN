import asyncio
import sys
import os
import time

# --- Path Fix for Standalone Run ---
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
correct_src_path = os.path.join(project_root, "src")

# Aggressively Clean sys.path
paths_to_remove = [p for p in sys.path if p.endswith("src") and os.path.abspath(p) != correct_src_path]
for p in paths_to_remove:
    if p in sys.path:
        sys.path.remove(p)

if correct_src_path not in sys.path:
    sys.path.insert(0, correct_src_path)

# Force reload/import
if "lar" in sys.modules:
    del sys.modules["lar"]

from lar.dmn_dreamer import dream

# Config
DEFAULT_IDLE_THRESHOLD = 30 * 60 # 30 minutes in seconds
DEFAULT_CHECK_INTERVAL = 60 # Check every minute
LOG_FILE = os.path.join("logs", "interaction_stream.jsonl")

class LarOrchestrator:
    """
    A lightweight background service that monitors user activity (via log file updates)
    and triggers the DMN Dreamer when the system is idle.
    """
    def __init__(self, idle_threshold_seconds: int = DEFAULT_IDLE_THRESHOLD, check_interval_seconds: int = DEFAULT_CHECK_INTERVAL):
        """
        Args:
            idle_threshold_seconds (int): How many seconds of inactivity before dreaming.
            check_interval_seconds (int): How often to check the file timestamp.
        """
        self.idle_threshold = idle_threshold_seconds
        self.check_interval = check_interval_seconds
        self.is_dreaming = False
        self.last_active_time = time.time()
        
        # Ensure log dir exists just in case
        if not os.path.exists(os.path.dirname(LOG_FILE)):
             os.makedirs(os.path.dirname(LOG_FILE))

    def _get_last_modified_time(self) -> float:
        """Returns the last modification time of the log file, or current time if missing."""
        if os.path.exists(LOG_FILE):
            return os.path.getmtime(LOG_FILE)
        return time.time() # Assume active if no logs (or brand new) to prevent immediate dreaming? 
                           # Or maybe 0? Let's use current time to say "nothing happened yet, so wait".

    async def monitor(self):
        """
        The main async loop.
        """
        print(f"👀 [Orchestrator] Watching {LOG_FILE} for inactivity > {self.idle_threshold}s...")
        
        while True:
            try:
                current_time = time.time()
                last_mod = self._get_last_modified_time()
                
                # Calculate time since last activity
                time_since_active = current_time - last_mod
                
                if time_since_active > self.idle_threshold and not self.is_dreaming:
                    print(f"💤 [Orchestrator] System idle for {int(time_since_active)}s. Entering Dream State...")
                    self.is_dreaming = True
                    
                    # Log event (visually to console, maybe to file if needed)
                    # We run the synchronous dream() function in a separate thread to not block the loop
                    await asyncio.to_thread(dream)
                    
                    print("⏰ [Orchestrator] Waking Up - Insights Integrated.")
                    self.is_dreaming = False
                    
                    # Update mod time or just wait? 
                    # If we don't 'touch' the file, it will dream again immediately if threshold is passed.
                    # We should probably wait until new activity OR sleep for a while.
                    # Ideally, dreaming itself generates an "insight" log, but that's in memory/ folder, not interactions.
                    # Let's enforce a "sleep refractory period" or just wait for next loop.
                    # If the user is STILL away, should it dream again?
                    # Typically DMN runs continuously. But for this script, maybe once per "long sleep" 
                    # or repeatedly. Let's let it run again if still idle, but maybe the dreamer itself handles "nothing new to process"?
                    # Yes, DMN checks recent logs. If it already processed them, it might process same ones again 
                    # unless DMN logic tracks "last_processed_timestamp". 
                    # For now, simplistic implementation as requested.
                
                elif time_since_active < self.idle_threshold and self.is_dreaming:
                    # User woke up mid-dream? (Not handled deep inside dream, but we can flag it)
                    print("❗ [Orchestrator] Activity detected. Waking up!")
                    self.is_dreaming = False

                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                print(f"❌ [Orchestrator] Error: {e}")
                await asyncio.sleep(self.check_interval)

if __name__ == "__main__":
    # Standalone runner
    orchestrator = LarOrchestrator()
    try:
        asyncio.run(orchestrator.monitor())
    except KeyboardInterrupt:
        print("\n👋 [Orchestrator] Shutting down.")
