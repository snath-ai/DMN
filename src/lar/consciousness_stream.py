import logging
import logging.handlers
import json
import time
import datetime
import uuid
import os
import functools
from typing import Callable, Any

class ConsciousnessStream:
    """
    A robust logging module to capture the 'Stream of Consciousness' of the AI.
    It logs every interaction to a rotated JSONL file.
    """

    def __init__(self, log_dir: str = "logs", filename: str = "interaction_stream.jsonl", max_bytes: int = 10 * 1024 * 1024, backup_count: int = 5):
        """
        Initialize the Consciousness Stream logger.

        Args:
            log_dir (str): Directory to store logs. Defaults to "logs".
            filename (str): Name of the log file. Defaults to "interaction_stream.jsonl".
            max_bytes (int): Max size of a log file before rotation. Defaults to 10MB.
            backup_count (int): Number of backup log files to keep. Defaults to 5.
        """
        # Support environment variable override for Docker
        env_log_file = os.environ.get("LOG_FILE")
        if env_log_file:
            self.log_path = env_log_file
            self.log_dir = os.path.dirname(self.log_path)
        else:
            self.log_path = os.path.join(self.log_dir, filename)
            
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # Configure the logger
        self.logger = logging.getLogger("ConsciousnessStream")
        self.logger.setLevel(logging.INFO)
        
        # Check for Stale Handlers (File deleted externally)
        # If the file does NOT exist, but we have handlers, those handlers are pointing to a deleted inode.
        if not os.path.exists(self.log_path) and self.logger.handlers:
            print("⚠️ [ConsciousnessStream] Detected stale log handlers. Resetting...")
            for h in self.logger.handlers:
                try:
                    h.close()
                except: pass
            self.logger.handlers.clear()
        
        # Prevent adding multiple handlers if instantiated multiple times
        if not self.logger.handlers:
            handler = logging.handlers.RotatingFileHandler(
                self.log_path, maxBytes=max_bytes, backupCount=backup_count
            )
            formatter = logging.Formatter('%(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_interaction(self, session_id: str, role: str, content: str, latency_ms: float = None, metadata: dict = None):
        """
        Logs a single interaction event.

        Args:
            session_id (str): Unique ID for the chat session.
            role (str): 'user' or 'assistant'.
            content (str): The text content of the message.
            latency_ms (float, optional): Latency in milliseconds (for assistant responses).
            metadata (dict, optional): Any other metadata to attach.
        """
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "session_id": session_id,
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        
        if latency_ms is not None:
            entry["metadata"]["latency_ms"] = latency_ms

        self.logger.info(json.dumps(entry))

    def wrap_chat(self, func: Callable) -> Callable:
        """
        Decorator to automatically log interactions for a chat function.
        
        Assumes the decorated function signature is roughly:
            func(user_input: str, session_id: str = None, *args, **kwargs) -> str
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract arguments based on assumption/convention
            # We assume the first string arg is user_input
            user_input = args[0] if args else kwargs.get('user_input')
            
            # Simple session ID generation if not provided
            session_id = kwargs.get('session_id', str(uuid.uuid4()))
            
            # Log User Input
            self.log_interaction(session_id, "user", user_input)
            
            start_time = time.time()
            try:
                # Execute the actual model/function
                response = func(*args, **kwargs)
                end_time = time.time()
                latency = (end_time - start_time) * 1000
                
                # Log Assistant Response
                self.log_interaction(session_id, "assistant", response, latency_ms=latency)
                
                return response
            except Exception as e:
                # Log errors if necessary, but re-raise
                end_time = time.time()
                latency = (end_time - start_time) * 1000
                self.log_interaction(session_id, "system", f"ERROR: {str(e)}", latency_ms=latency)
                raise e
                
        return wrapper

if __name__ == "__main__":
    # Internal Test
    stream = ConsciousnessStream(log_dir="test_logs")
    
    @stream.wrap_chat
    def mock_chat(user_input, session_id=None):
        time.sleep(0.1) # Simulate think time
        return f"Echo: {user_input}"

    print("Running internal test...")
    mock_chat("Hello World", session_id="test-session-1")
    print("Done. Check test_logs/interaction_stream.jsonl")
