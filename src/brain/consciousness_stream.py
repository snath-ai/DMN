"""
ConsciousnessStream — DMN interaction logger.

Writes JSONL conversation turns to disk so the Hippocampus, DMN dreamer,
and orchestrator can read the session history.  It is intentionally separate
from lar.logger (AuditLogger) which records graph execution traces; this
module records the *conversational* stream of consciousness.
"""

import os
import json
import datetime
from typing import Optional


class ConsciousnessStream:
    """
    Append-only JSONL logger for Thalamus conversation turns.

    Each line written has the shape:
        {"timestamp": "...", "session_id": "...", "role": "user"|"assistant",
         "content": "...", "metadata": {...}}

    Parameters
    ----------
    log_dir : str
        Directory where the JSONL log files are stored.  Created if absent.
    filename : str
        Name of the log file within *log_dir*.
        Defaults to ``interaction_stream.jsonl``.
    """

    DEFAULT_FILENAME = "interaction_stream.jsonl"

    def __init__(self, log_dir: str = "logs", filename: Optional[str] = None):
        self._log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self._filename = filename or self.DEFAULT_FILENAME
        self._log_path = os.path.join(log_dir, self._filename)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def log_path(self) -> str:
        """Absolute (or relative) path to the active JSONL log file."""
        return self._log_path

    def log_interaction(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Append one conversation turn to the log file.

        Parameters
        ----------
        session_id : str
            Opaque identifier for the current conversation session.
        role : str
            ``"user"`` or ``"assistant"``.
        content : str
            The raw message text.
        metadata : dict, optional
            Any extra fields to persist (e.g. latency_ms, emotion).
        """
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "session_id": session_id,
            "role": role,
            "content": content,
        }
        if metadata:
            entry["metadata"] = metadata

        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as exc:
            # Non-fatal — log the warning but don't crash the Thalamus.
            print(f"⚠️  [ConsciousnessStream] Could not write log: {exc}")

    def read_recent(self, n: int = 50) -> list[dict]:
        """
        Return the last *n* entries from the log as parsed dicts.
        Returns an empty list if the file does not yet exist.
        """
        if not os.path.exists(self._log_path):
            return []
        try:
            with open(self._log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            entries = []
            for line in lines[-n:]:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            return entries
        except OSError:
            return []
