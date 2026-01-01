import sys
import os

print(f"Python: {sys.version}")

try:
    import requests
    print("Requests imported.")
    try:
        r = requests.post("http://host.docker.internal:11434/api/tags", timeout=2)
        print(f"Requests Check: {r.status_code}")
    except Exception as e:
        print(f"Requests Failed: {e}")

except ImportError:
    print("Requests not installed.")

print("-" * 20)

try:
    import litellm
    print(f"LiteLLM File: {litellm.__file__}")
    # print(f"LiteLLM Dir: {dir(litellm)}")
    from litellm import completion
    print(f"LiteLLM Completion imported.")
    
    try:
        response = completion(
            model="ollama/llama3.2",
            messages=[{"role": "user", "content": "Hello"}],
            api_base="http://host.docker.internal:11434"
        )
        print("LiteLLM Check: Success")
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"LiteLLM Failed: {e}")
        import traceback
        traceback.print_exc()

except ImportError:
    print("LiteLLM not installed.")
