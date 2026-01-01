import json

def extract_strings_debug(insights):
    found_narratives = []
    
    def extract_strings(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ["narrative", "insight", "summary", "content"] and isinstance(v, str):
                    found_narratives.append(v)
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
    return found_narratives

with open("memory/dreams.json", "r") as f:
    dreams = json.load(f)
    print(f"Loaded {len(dreams)} dreams.")
    last_dream = dreams[-1]
    print(f"Latest Dream ID: {last_dream['id']}")
    print("--- RAW INSIGHTS ---")
    print(json.dumps(last_dream['insights'], indent=2))
    print("--- EXTRACTED ---")
    extracted = extract_strings_debug(last_dream['insights'])
    for e in extracted:
        print(f"[FOUND] {e}")
