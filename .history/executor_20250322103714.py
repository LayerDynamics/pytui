"""Script execution wrapper and subprocess manager."""

# pylint: disable=trailing-whitespace

import os
import sys
import subprocess
import json
import tempfile
from pathlib import Path
import threading
from typing import Optional

from .collector import DataCollector, CallEvent


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

        # Create a named pipe or temporary file for IPC
        self.trace_fifo = tempfile.NamedTemporaryFile(
            delete=False, prefix="pytui_trace_", suffix=".jsonl"
        )
        trace_path = self.trace_fifo.name
        self.trace_fifo.close()  # Close it so the subprocess can write to it

        # Set up hook to inject tracer with IPC path
        env["PYTUI_TRACE"] = "1"
        env["PYTUI_TRACE_PATH"] = trace_path

        # Enhanced bootstrap code to guarantee trace capture
        bootstrap_code = (
            "import os, sys, threading, json\n"
            "def setup_tracing():\n"
            "    # Set up Python path\n"
            "    sys.path[:0] = os.environ['PYTHONPATH'].split(os.pathsep)\n"
            "    from pytui.tracer import install_trace\n"
            "    from pytui.collector import get_collector\n"
            "    # Get the trace path from environment\n"
            "    trace_path = os.environ.get('PYTUI_TRACE_PATH')\n"
            "    if not trace_path:\n"
            "        print('ERROR: No trace path specified')\n"
            "        return None\n"
            "    print(f'Debug: Using trace path {trace_path}')\n"
            "    # Initialize collector\n"
            "    collector = get_collector()\n"
            "    # Set up the tracer with IPC path\n"
            "    install_trace(collector, trace_path)\n"
            "    # Verify tracing is working\n"
            "    def _test_func(x):\n"
            "        return x\n"
            "    _test_func(42)  # This should trigger tracing\n"
            "    return collector\n"
            "\n"
            "collector = setup_tracing()\n"
            "\n"
            "script_path = os.path.abspath(sys.argv[1])\n"
            "print(f'Debug: Running script {script_path}')\n"
            "with open(script_path) as f:\n"
            "    code = compile(f.read(), script_path, 'exec')\n"
            "\n"
            "globals_dict = {\n"
            "    '__name__': '__main__',\n"
            "    '__file__': script_path,\n"
            "    '__builtins__': __builtins__,\n"
            "}\n"
            "sys.argv = [script_path] + sys.argv[2:]\n"
            "try:\n"
            "    sys.stdout.flush()\n"  # Flush before execution
            "    exec(code, globals_dict)\n"
            "    sys.stdout.flush()\n"  # Flush after execution
            "except Exception as e:\n"
            "    import traceback\n"
            "    traceback.print_exc()\n"
            "finally:\n"
            "    # Signal tracer to flush remaining data\n"
            "    if hasattr(collector, 'flush'):\n"
            "        collector.flush()\n"
            "    # Make sure trace file is completely written\n"
            "    sys.stdout.flush()\n"
            "    sys.stderr.flush()\n"
        )

        # Start subprocess with piped outputs - split long command line
        cmd = [
            sys.executable,
            "-c",
            bootstrap_code,
            str(self.script_path.absolute()),
            *self.script_args,
        ]

        # Start process
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

        # Start reader threads
        self.stdout_thread = threading.Thread(
            target=self._read_output, args=(self.process.stdout, "stdout"), daemon=True
        )
        self.stdout_thread.start()

        self.stderr_thread = threading.Thread(
            target=self._read_output, args=(self.process.stderr, "stderr"), daemon=True
        )
        self.stderr_thread.start()

        # Start thread to monitor process completion
        self.monitor_thread = threading.Thread(
            target=self._monitor_process, daemon=True
        )
        self.monitor_thread.start()

        # Start thread to read trace data
        self.trace_thread = threading.Thread(
            target=self._read_trace_data, args=(trace_path,), daemon=True
        )
        self.trace_thread.start()

    def _read_trace_data(self, trace_path):
        """Read function call trace data from the IPC file."""
        # Wait a bit longer to ensure the subprocess has started and written some data
        import time

        time.sleep(0.2)

        # Debug output
        print(f"Debug: Reading trace data from {trace_path}")
        if os.path.exists(trace_path):
            print(f"Debug: Trace file exists, size: {os.path.getsize(trace_path)}")
        else:
            print(f"Debug: Trace file does not exist yet")

        # Flag to track if we've seen data in the file
        has_seen_data = False
        read_attempts = 0
        max_attempts = 50  # Increase max attempts

        try:
            # Keep checking for the file until it's created or timeout
            while not os.path.exists(trace_path) and read_attempts < 10:
                time.sleep(0.1)
                read_attempts += 1

            if not os.path.exists(trace_path):
                print(f"Debug: Trace file never created")
                return

            with open(trace_path, "r") as f:
                while self.is_running and read_attempts < max_attempts:
                    # Read all available content in the file
                    content = f.read()

                    if content:
                        has_seen_data = True

                        # Process each line
                        for line in content.splitlines():
                            if not line.strip():
                                continue

                            try:
                                # Parse the trace event
                                data = json.loads(line.strip())
                                event_type = data.get("type")

                                if event_type == "call":
                                    # Extract data with defaults for backward compatibility
                                    func_name = data.get("function_name", "")
                                    filename = data.get("filename", "")
                                    line_no = data.get("line_no", 0)
                                    args = data.get("args", {})
                                    call_id = data.get("call_id", 0)
                                    parent_id = data.get("parent_id")

                                    # Skip if missing key data
                                    if not func_name or not filename:
                                        continue

                                    # Add call to the collector
                                    self.collector.add_call(
                                        func_name,
                                        filename,
                                        line_no,
                                        args,
                                        call_id=call_id,
                                        parent_id=parent_id,
                                    )
                                    print(f"Debug: Added call {func_name}")

                                elif event_type == "return":
                                    # Add return to the collector
                                    self.collector.add_return(
                                        data.get("function_name", ""),
                                        data.get("return_value", "None"),
                                        call_id=data.get("call_id", 0),
                                    )
                            except json.JSONDecodeError:
                                # Skip malformed JSON
                                continue
                            except Exception as e:
                                print(f"Error processing trace data: {e}")

                    # Wait for more content
                    time.sleep(0.1)
                    read_attempts += 1

                if not has_seen_data:
                    print("Debug: No trace data received")
        except Exception as e:
            print(f"Error reading trace data: {e}")
        finally:
            # Clean up the trace file
            try:
                if os.path.exists(trace_path):
                    os.unlink(trace_path)
            except:
                pass

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
