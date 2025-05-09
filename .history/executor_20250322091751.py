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

        # Break long lines and use context management for resources
        bootstrap_code = (
            "import os, sys, threading, contextlib\n"
            "def setup_tracing():\n"
            "    sys.path[:0] = os.environ['PYTHONPATH'].split(os.pathsep)\n"
            "    import pytui.tracer\n"
            "    from pytui.collector import get_collector\n"
            "    collector = get_collector()\n"
            "    sys.settrace(pytui.tracer.trace_function)\n"
            "    threading.settrace(pytui.tracer.trace_function)\n"
            "\n"
            "setup_tracing()\n"
            "\n"
            "script_path = os.path.abspath(sys.argv[1])\n"
            "with contextlib.closing(open(script_path)) as f:\n"
            "    source = f.read()\n"
            "    code = compile(\n"
            "        source,\n"
            "        script_path,\n"
            "        'exec'\n"
            "    )\n"
            "\n"
            "globals_dict = {\n"
            "    '__name__': '__main__',\n"
            "    '__file__': script_path,\n"
            "    '__builtins__': __builtins__,\n"
            "}\n"
            "sys.argv = sys.argv[1:]\n"
            "try:\n"
            "    exec(code, globals_dict)\n"
            "except (SystemExit, KeyboardInterrupt):\n"
            "    raise\n"
            "except Exception as e:\n"
            "    import traceback\n"
            "    traceback.print_exc()\n"
            "    sys.exit(1)\n"
        )

        # Start subprocess with piped outputs - split long command line
        cmd = [
            sys.executable,
            "-c",
            bootstrap_code,
            str(self.script_path.absolute()),
            *self.script_args,
        ]

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=1,  # Line buffered
            cwd=str(self.script_path.parent),
        )

        self.is_running = True

        # Start reader threads
        threading.Thread(
            target=self._read_output, args=(self.process.stdout, "stdout"), daemon=True
        ).start()
        threading.Thread(
            target=self._read_output, args=(self.process.stderr, "stderr"), daemon=True
        ).start()
        threading.Thread(target=self._monitor_process, daemon=True).start()

    def _read_output(self, pipe, stream_name):
        """Read output from the subprocess pipe."""
        try:
            for line in iter(pipe.readline, ""):
                line = line.rstrip("\n")
                if line and not self.is_paused:
                    self.collector.add_output(line, stream_name)
                if not self.is_running:
                    break
        except (IOError, OSError) as e:
            self.collector.add_exception(e)
        finally:
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
        self.collector.clear()
        self.start()
