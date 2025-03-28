"""Script execution wrapper and subprocess manager."""

import sys
import os
import signal
import subprocess
from pathlib import Path
from typing import List, Optional

from .collector import DataCollector
from .tracer import install_trace
from .utils import kill_process_tree


class ScriptExecutor:
    """Manages script execution and tracing."""

    def __init__(self, script_path: Union[str, Path], script_args: List[str] = None):
        """Initialize the executor."""
        self.script_path = Path(script_path).resolve()
        self.script_args = script_args or []
        self.process: Optional[subprocess.Popen] = None
        self.is_running = False
        self.is_paused = False
        self.collector = DataCollector()
        install_trace(self.collector)

    def start(self) -> None:
        """Start script execution."""
        if self.is_running:
            return

        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.script_path.parent)

        try:
            self.process = subprocess.Popen(
                [sys.executable, str(self.script_path)] + self.script_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1,
            )
            self.is_running = True
        except Exception as e:
            self.collector.add_exception(e)
            self.stop()
            raise

    def stop(self) -> None:
        """Stop script execution."""
        if self.process:
            kill_process_tree(self.process.pid)
            self.process = None
        self.is_running = False

    def pause(self) -> None:
        """Pause script execution."""
        if self.process and self.is_running:
            if hasattr(signal, "SIGSTOP"):
                self.process.send_signal(signal.SIGSTOP)
            self.is_paused = True

    def resume(self) -> None:
        """Resume script execution."""
        if self.process and self.is_paused:
            if hasattr(signal, "SIGCONT"):
                self.process.send_signal(signal.SIGCONT)
            self.is_paused = False

    def restart(self) -> None:
        """Restart script execution."""
        self.stop()
        self.collector.clear()
        self.start()
