"""Script execution wrapper and subprocess manager."""

import os
import sys
import subprocess
from pathlib import Path
import threading

from .collector import DataCollector


class ScriptExecutor:
    """Executes a Python script in a subprocess with tracing and output capture."""

    def __init__(self, script_path, script_args=None):
        """Initialize the executor with a script path and arguments."""
        self.script_path = Path(script_path).resolve()
        self.script_args = script_args or []
        self.process = None
        self.collector = DataCollector()
        self.is_running = False
        self.is_paused = False

    def start(self):
        """Start the script execution in a subprocess."""
        if not self.script_path.exists():
            raise FileNotFoundError(f"Script not found: {self.script_path}")

        # Set up environment for tracing
        env = os.environ.copy()

        # Add the tracer module to Python path
        tracer_module_path = Path(__file__).parent.resolve()
        if "PYTHONPATH" in env:
            env["PYTHONPATH"] = f"{tracer_module_path}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = str(tracer_module_path)

        # Set up hook to inject tracer
        env["PYTUI_TRACE"] = "1"

        # Prepare command to run with tracer injection
        cmd = [
            sys.executable,
            "-c",
            "import sys; from pytui.tracer import install_trace; install_trace(); exec(open(sys.argv[1]).read())",
            str(self.script_path),
            *self.script_args,
        ]

        # Start subprocess with piped outputs
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=1,  # Line buffered
        )

        self.is_running = True

        # Start threads to read stdout and stderr
        threading.Thread(
            target=self._read_output, args=(self.process.stdout, "stdout"), daemon=True
        ).start()
        threading.Thread(
            target=self._read_output, args=(self.process.stderr, "stderr"), daemon=True
        ).start()

        # Start thread to monitor process completion
        threading.Thread(target=self._monitor_process, daemon=True).start()

    def _read_output(self, pipe, stream_name):
        """Read output from the subprocess pipe."""
        try:
            for line in iter(pipe.readline, ""):
                line = line.rstrip("\n")  # Remove trailing newlines
                if line:  # Only process non-empty lines
                    if not self.is_paused:
                        self.collector.add_output(line, stream_name)
                if not self.is_running:
                    break
        except Exception as e:
            self.collector.add_exception(e)
        finally:
            pipe.close()

    def _monitor_process(self):
        """Monitor the subprocess for completion."""
        try:
            returncode = self.process.wait()
            self.is_running = False
            # Ensure pipes are fully read before reporting completion
            if self.process.stdout:
                self.process.stdout.close()
            if self.process.stderr:
                self.process.stderr.close()
            self.collector.add_output(
                f"Process exited with code {returncode}", "system"
            )
        except Exception as e:
            self.collector.add_exception(e)

    def stop(self):
        """Stop the script execution."""
        if self.process and self.is_running:
            self.process.terminate()
            self.is_running = False

    def pause(self):
        """Pause updating the UI with new data."""
        self.is_paused = True

    def resume(self):
        """Resume updating the UI with new data."""
        self.is_paused = False

    def restart(self):
        """Restart the script execution."""
        self.stop()
        self.collector.clear()
        self.start()
