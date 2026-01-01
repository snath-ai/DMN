import time
import os
import sys
import datetime
from .default_mode_network import DefaultModeNetwork

# Configuration
LOG_FILE = "logs/interaction_stream.jsonl"
IDLE_THRESHOLD_SECONDS = 30 # Short for demo purposes. In prod, maybe 600 (10 mins)
CHECK_INTERVAL = 10 

class AutonomicNervousSystem:
    """
    Runs in the background to handle autonomic functions like:
    - Sleep/Dream cycles (DMN activation)
    - Memory consolidation
    - (Future) Homeostasis maintenance
    """

    def __init__(self):
        self.pid = os.getpid()
        self._log(f"🧠 [ANS] Autonomic System Online. PID: {self.pid}")
        self.dmn = DefaultModeNetwork()
        self.last_dream_time = datetime.datetime.now()

    def _log(self, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        # Append to debug log
        try:
            with open("logs/ans_debug.log", "a") as f:
                f.write(line + "\n")
        except: pass
        
    def get_last_interaction_time(self):
        """Checks the modification time of the log file."""
        if not os.path.exists(LOG_FILE):
            return datetime.datetime.now() # Assume active if no logs to prevent premature dreaming
            
        try:
            mtime = os.path.getmtime(LOG_FILE)
            return datetime.datetime.fromtimestamp(mtime)
        except OSError:
            return datetime.datetime.now()

    def run(self):
        print(f"🧠 [ANS] Monitoring for idle states (> {IDLE_THRESHOLD_SECONDS}s)...")
        while True:
            try:
                now = datetime.datetime.now()
                last_interaction = self.get_last_interaction_time()
                
                # Time since last talked to user
                idle_duration = (now - last_interaction).total_seconds()
                
                # Check for Dream Condition
                # We also check if we haven't dreamt recently to avoid looping dreams
                time_since_last_dream = (now - self.last_dream_time).total_seconds()
                
                if idle_duration > IDLE_THRESHOLD_SECONDS:
                    # Only dream if we have new info or sufficient time passed?
                    # For now: dream if idle AND haven't dreamt in a while (e.g. Dream once per idle session logic?)
                    # Let's simple logic: Dream if idle, then wait for new interaction or very long sleep.
                    
                    # Logic: If idle > threshold AND last dream was BEFORE the last interaction
                    # This means we haven't processed the *latest* interactions yet.
                    if self.last_dream_time < last_interaction:
                         self._log(f"💤 [ANS] Brain is idle ({int(idle_duration)}s). Spindles active. Initiating R.E.M...")
                         self.dmn.activate()
                         self.last_dream_time = datetime.datetime.now()
                         self._log(f"🧠 [ANS] R.E.M Cycle Complete because last_int {last_interaction} > prev_dream. Now last_dream={self.last_dream_time}")
                    else:
                         # Already dreamt about these logs.
                         pass
                
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                print("\n🧠 [ANS] Shutting down.")
                break
            except Exception as e:
                print(f"❌ [ANS] Error: {e}")
                time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    # Ensure we are in project root or path is set
    # sys.path hack if running as script from root
    sys.path.append(os.getcwd())
    
    ans = AutonomicNervousSystem()
    ans.run()
