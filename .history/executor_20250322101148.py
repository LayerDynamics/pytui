"""Script execution wrapper and subprocess manager."""

# pylint: disable=trailing-whitespace

import os
import sys
import subprocess
from pathlib import Path
import threading
from typing import Optional

from .collector import DataCollector


class ScriptExecutor:
    """Executes a Python script in a subprocess with tracing and output capture."""

    def __init__(self, script_path, script_args=None):
        """Initialize the executor with a script path and arguments."""
        self.script_path = Path(script_path).resolve()
        self.script_args = script_args or []
        self.process: Optional[subprocess.Popen] = None
        self.collector = DataCollector()
        self.is_running = False
        self.is_paused = False

    def start(self):
        """Start the script execution in a subprocess."""
        if not self.script_path.exists():
            raise FileNotFoundError(f"Script not found: {self.script_path}")

        env = os.environ.copy()
        package_root = str(Path(__file__).parent.parent.absolute())
        pytui_path = str(Path(__file__).parent.absolute())

        python_paths = [package_root, pytui_path]
        if "PYTHONPATH" in env:
            python_paths.extend(env["PYTHONPATH"].split(os.pathsep))
        env["PYTHONPATH"] = os.pathsep.join(python_paths)
        env["PYTUI_TRACE"] = "1"

        # Simplified and improved bootstrap code
        bootstrap_code = (
            "import os, sys, threading\n"
            "# Initialize paths and core modules\n"
            "sys.path[:0] = os.environ['PYTHONPATH'].split(os.pathsep)\n"
            "from pytui.collector import get_collector\n"
            "from pytui.tracer import trace_function, install_trace\n"
            "\n"
            "# Set up tracing explicitly\n"
            "collector = get_collector()\n"
            "install_trace()\n"
            "\n"
            "# Load target script\n"
            "script_path = os.path.abspath(sys.argv[1])\n"
            "print(f'Running script: {script_path}')\n"
            "with open(script_path) as f:\n"
            "    code = compile(f.read(), script_path, 'exec')\n"
            "\n"
            "# Execute with proper globals\n"
            "script_globals = {\n"
            "    '__name__': '__main__',\n"
            "    '__file__': script_path,\n"
            "    '__builtins__': __builtins__,\n"
            "}\n"
            "# Ensure sys.argv is set correctly\n"
            "old_argv = list(sys.argv)\n"
            "sys.argv = [script_path] + sys.argv[2:]\n"
            "try:\n"
            "    exec(code, script_globals)\n"
            "except Exception as e:\n"
            "    import traceback\n"
            "    traceback.print_exc()\n"
            "finally:\n"
            "    # Restore original argv\n"
            "    sys.argv = old_argv\n"
        )

        # Start subprocess with piped outputs - split long command line
        cmd = [
            sys.executable,
            "-c",
            bootstrap_code,
            str(self.script_path.absolute()),
            *self.script_args,
        ]

        # IMPORTANT: Don't use 'with' here - it causes premature pipe closure
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=1,
            cwd=str(self.script_path.parent),
        )

        self.is_running = True

        # Create reader threads with better pipe handling
        self.stdout_thread = threading.Thread(
            target=self._read_output, args=(self.process.stdout, "stdout"), daemon=True
        )
        self.stdout_thread.start()

        self.stderr_thread = threading.Thread(
            target=self._read_output, args=(self.process.stderr, "stderr"), daemon=True
        )
        self.stderr_thread.start()

        # Monitor thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_process, daemon=True
        )
        self.monitor_thread.start()

    def _read_output(self, pipe, stream_name):
        """Read output from the subprocess pipe."""
        try:
            while self.is_running and pipe and not pipe.closed:
                line = pipe.readline()
                if not line:
                    break  # EOF reached

                line = line.rstrip("\n")
                if line and not self.is_paused:
                    self.collector.add_output(line, stream_name)
        except (IOError, OSError, ValueError) as e:
            # Only log pipe errors if we're still running
            if self.is_running:
                self.collector.add_output(f"Output read error: {e}", "system")
        finally:
            # Don't try to close an already closed pipe
            if pipe and not pipe.closed:
                pipe.close()

    def _monitor_process(self):
        """Monitor the subprocess for completion."""
        try:
            returncode = self.process.wait()
            self.is_running = False
            if self.process.stdout:
                self.process.stdout.close()
            if self.process.stderr:
                self.process.stderr.close()
            self.collector.add_output(
                f"Process exited with code {returncode}", "system"
            )
        except (IOError, OSError) as e:
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

        # Wait for process to terminate completely
        if self.process:
            try:
                self.process.wait(timeout=1.0)
            except Exception:
                # Force kill if needed
                if self.process.poll() is None:
                    self.process.kill()

        # Ensure is_running is properly set
        self.is_running = False

        # Allow pipes to close completely
        import time

        time.sleep(0.5)

        self.collector.clear()
        # Now start the new process
        self.start()
