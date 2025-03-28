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

        # Get absolute paths for package directories
        package_root = str(
            Path(__file__).parent.parent.absolute()
        )  # pytui root directory
        pytui_path = str(Path(__file__).parent.absolute())  # pytui module directory

        # Build Python path with both package root and module directory
        python_paths = [package_root, pytui_path]
        if "PYTHONPATH" in env:
            python_paths.extend(env["PYTHONPATH"].split(os.pathsep))
        env["PYTHONPATH"] = os.pathsep.join(python_paths)

        # Set up hook to inject tracer
        env["PYTUI_TRACE"] = "1"

        # Modified bootstrap code for proper path handling and explicit imports
        bootstrap_code = (
            "import os, sys;\n"
            "sys.path[:0] = os.environ['PYTHONPATH'].split(os.pathsep);\n"
            "import pytui.tracer;\n"
            "pytui.tracer.install_trace();\n"
            "exec(compile(open(os.path.abspath(sys.argv[1])).read(), sys.argv[1], 'exec'))\n"
        )

        # Start subprocess with piped outputs
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                bootstrap_code,
                str(self.script_path.absolute()),
                *self.script_args,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=1,  # Line buffered
            cwd=str(self.script_path.parent),  # Run from script's directory
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
