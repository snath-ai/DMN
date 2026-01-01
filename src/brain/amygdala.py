import os
import requests
import json
import time

class Amygdala:
    """
    The Amygdala: Responsible for rapid emotional processing and 'fight or flight' response.
    It analyzes the user's input for sentiment and urgency BEFORE the Cortex processes it.
    """
    
    def __init__(self, model="llama3"):
        self.model = f"ollama/{os.environ.get('OLLAMA_MODEL', 'llama3.2')}"
        host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.url = f"{host}/api/generate"
        
    def feel(self, text: str) -> dict:
        """
        Rapidly assesses the emotional content of the input.
        Returns a dict with 'emotion', 'arousal', and 'valence'.
        """
        print(f"⚡ [Amygdala] Scanning input for threats/emotions: '{text[:30]}...'")
        start_time = time.time()
        
        # Fast, instinctive prompt
        prompt = (
            f"Analyze the emotional tone of this text: '{text}'. "
            "Output ONLY a JSON object with keys: "
            "'primary_emotion' (str: Joy, Anger, Fear, Sadness, Surprise, Neutral), "
            "'intensity' (float: 0.0 to 1.0. Default to 0.0 if Neutral), "
            "'is_urgent' (bool: True ONLY if immediate threat, danger, or time-critical request. Otherwise False). "
            "Be conservative; default to Neutral and False."
        )
        
        try:
            response = requests.post(
                self.url,
                json={
                    "model": self.model.replace("ollama/", ""), # Raw ollama model name
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=5 # Amygdala must be fast!
            )
            
            if response.status_code == 200:
                result = response.json().get("response", "{}")
                data = json.loads(result)
                latency = (time.time() - start_time) * 1000
                print(f"⚡ [Amygdala] Felt {data.get('primary_emotion')} (Intensity: {data.get('intensity')}) in {latency:.0f}ms")
                return data
            else:
                print(f"⚠️ [Amygdala] Failed to process emotion.")
                return {"primary_emotion": "Neutral", "intensity": 0.0, "is_urgent": False}
                
        except Exception as e:
            print(f"⚠️ [Amygdala] Instinct failed: {e}")
            return {"primary_emotion": "Neutral", "intensity": 0.0, "is_urgent": False}

# Simple test
if __name__ == "__main__":
    amygdala = Amygdala()
    print(amygdala.feel("I am so happy that this works!"))
    print(amygdala.feel("This is a disaster, everything is broken!"))
