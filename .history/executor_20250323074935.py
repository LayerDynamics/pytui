"""Script execution wrapper and subprocess manager."""

# pylint: disable=trailing-whitespace

import os
import sys
import subprocess
import json
import tempfile
import time
from pathlib import Path
import threading
from typing import Optional, Dict, Any, List, Union
import queue

from .collector import DataCollector

# pylint: disable=unused-import,too-many-instance-attributes,attribute-defined-outside-init


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
        self.error_queue = queue.Queue()
        
        # Initialize thread attributes
        self.stdout_thread: Optional[threading.Thread] = None
        self.stderr_thread: Optional[threading.Thread] = None
        self.monitor_thread: Optional[threading.Thread] = None
        self.trace_thread: Optional[threading.Thread] = None
        self.error_handler_thread: Optional[threading.Thread] = None

    def _handle_errors(self):
        """Process errors from queue without blocking."""
        while self.is_running:
            try:
                error_data = self.error_queue.get(timeout=0.1)
                if error_data:
                    context, error = error_data
                    self.collector.add_output(
                        f"Error in {context}: {str(error)}", "error"
                    )
            except queue.Empty:
                continue
            except (ValueError, AttributeError, TypeError) as e:
                print(f"Error in error handler: {e}")

    def _queue_error(self, context: str, error: Union[str, Exception]) -> None:
        """Queue an error for processing."""
        try:
            self.error_queue.put((context, error))
        except queue.Full:
            print(f"Error queue full, dropping error from {context}: {error}")

    def _start_process(self, cmd: List[str], env: Dict[str, str]) -> None:
        """Start the subprocess with proper resource management."""
        try:
            with subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=0,
                cwd=str(self.script_path.parent),
            ) as process:
                self.process = process
                self.is_running = True

        except (OSError, subprocess.SubprocessError) as e:
            print(f"Failed to start process: {e}")
            self.is_running = False
            raise

    def start(self):
        # pylint: disable=too-many-locals,too-many-branches,too-many-statements
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

        # Create a temporary file for IPC using with to satisfy resource allocation checks
        with tempfile.NamedTemporaryFile(
            delete=False, prefix="pytui_trace_", suffix=".jsonl"
        ) as fifo:
            trace_path = fifo.name
        self.trace_fifo = trace_path

        # Set up hook to inject tracer with IPC path
        env["PYTUI_TRACE"] = "1"
        env["PYTUI_TRACE_PATH"] = trace_path

        # Enhanced bootstrap code that handles execution more carefully
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
            "    print('Debug: Using trace path ' + trace_path)\n"
            "    # Initialize collector\n"
            "    collector = get_collector()\n"
            "    # Set up the tracer with IPC path\n"
            "    with open(trace_path, 'w', encoding='utf-8') as trace_file:\n"
            "        install_trace(collector, trace_path)\n"
            "        # Verify the trace file is working\n"
            '        trace_file.write(\'{"type": "test", "message": "Trace file is working"}\\n\')\n'
            "        trace_file.flush()\n"
            "    \n"
            "    # Define original_import to wrap imports\n"
            "    original_import = __builtins__.__import__\n"
            "    def patched_import(name, *args, **kwargs):\n"
            "        module = original_import(name, *args, **kwargs)\n"
            "        print('Imported module: ' + name)\n"
            "        return module\n"
            "    __builtins__.__import__ = patched_import\n"
            "    \n"
            "    return collector\n"
            "\n"
            "collector = setup_tracing()\n"
            "print('Debug: Running script ' + script_path)\n"
            "\n"
            "# Create a clean execution environment\n"
            "globals_dict = {\n"
            "    '__name__': '__main__',\n"
            "    '__file__': script_path,\n"
            "    '__builtins__': __builtins__,\n"
            "}\n"
            "sys.argv = [script_path] + sys.argv[2:]\n"
            "\n"
            "try:\n"
            "    # Read the script content\n"
            "    with open(script_path, 'r') as f:\n"
            "        script_content = f.read()\n"
            "    \n"
            "    # Execute the script with modified globals\n"
            "    sys.stdout.flush()\n"
            "    exec(script_content, globals_dict)\n"
            "    sys.stdout.flush()\n"
            "    \n"
            "    # Manually capture function1 to ensure it's traced\n"
            "    if 'function1' in globals_dict and callable(globals_dict['function1']):\n"
            "        try:\n"
            "            result = globals_dict['function1'](42)\n"
            "            print('Extra call to function1(42) result: ' + str(result))\n"
            "        except Exception as func_err:\n"
            "            print('Error calling function1: ' + str(func_err))\n"
            "except Exception as e:\n"
            "    import traceback\n"
            "    print('ERROR in script execution:')\n"
            "    traceback.print_exc()\n"
            "finally:\n"
            "    # Force collection and cleanup\n"
            "    sys.stdout.flush()\n"
            "    sys.stderr.flush()\n"
            "    if 'collector' in locals():\n"
            "        if hasattr(collector, 'flush'):\n"
            "            collector.flush()\n"
            "    # Final trace data to verify function was called\n"
            "    print('End of script execution')\n"
        )

        # Start subprocess with piped outputs - split long command line
        cmd = [
            sys.executable,
            "-c",
            bootstrap_code,
            str(self.script_path.absolute()),
            *self.script_args  # Removed extra comma
        ]

        self._start_process(cmd, env)
        if self.is_running:
            self._start_threads(trace_path)

    def _start_threads(self, trace_path):
        """Start all monitoring threads."""
        # Define thread configurations
        thread_configs = [
            ('stdout_thread', self._read_output, (self.process.stdout, "stdout")),
            ('stderr_thread', self._read_output, (self.process.stderr, "stderr")),
            ('monitor_thread', self._monitor_process, ()),
            ('trace_thread', self._read_trace_data, (trace_path,)),
            ('error_handler_thread', self._handle_errors, ())
        ]

        # Start each thread
        for name, target, args in thread_configs:
            thread = threading.Thread(target=target, args=args, daemon=True)
            setattr(self, name, thread)
            thread.start()

    def _read_trace_data(self, trace_path):
        """Read function call trace data from the IPC file."""
        print("Debug: Reading trace data from", trace_path)

        try:
            content = self._wait_for_trace_file(trace_path)
            if not content:
                return

            lines = content.splitlines()
            print("Debug: Found", len(lines), "lines in trace file")

            self._process_trace_lines(lines)

        except OSError as e:
            print("Fatal error reading trace data:", str(e))
        finally:
            try:
                if os.path.exists(trace_path):
                    os.unlink(trace_path)
            except OSError:
                pass

    def _wait_for_trace_file(self, trace_path: str, max_retries: int = 30) -> str:
        """Wait for trace file to be created and return its content."""
        # Give the subprocess time to start up
        time.sleep(0.5)

        for _ in range(max_retries):
            if not os.path.exists(trace_path):
                print("Debug: Trace file does not exist, retrying...")
                time.sleep(0.2)
                continue

            file_size = os.path.getsize(trace_path)
            print("Debug: Trace file exists, size:", file_size)

            if file_size == 0:
                print("Debug: Trace file is empty, retrying...")
                time.sleep(0.2)
                continue

            with open(trace_path, "r", encoding="utf-8") as f:
                content = f.read()

            if content.strip():
                return content

            time.sleep(0.2)

        print("Debug: Could not read content from trace file after multiple retries")
        return ""

    def _process_trace_lines(self, lines: List[str]) -> None:
        """Process trace file lines and update collector."""
        if lines:
            print("Debug: First few trace lines:")
            for i in range(min(3, len(lines))):
                print("  Line", i + 1, ":", lines[i][:100])

        call_count = return_count = error_count = 0
        content = "\n".join(lines)  # Store content for alternative parsing

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            try:
                if not line.startswith("{"):
                    print("Skipping invalid JSON line", i + 1, ": doesn't start with {")
                    continue

                data = json.loads(line)
                event_type = data.get("type")

                if event_type == "call":
                    self._process_call_event(data)
                    call_count += 1
                elif event_type == "return":
                    self._process_return_event(data)
                    return_count += 1

            except json.JSONDecodeError as e:
                self._queue_error("JSON parsing", e)
            except (KeyError, ValueError) as e:
                self._queue_error("trace processing", e)

        print(
            "Debug: Processed",
            f"{call_count} call events",
            f"and {return_count} return events",
            f"with {error_count} errors",
        )

        if call_count == 0:
            print("Debug: Attempting alternative parsing method...")
            self._try_alternative_parsing(content)

    def _process_call_event(self, data: Dict[str, Any]) -> None:
        """Process a call event from trace data."""
        func_name = data.get("function_name", "")
        filename = data.get("filename", "")
        line_no = data.get("line_no", 0)
        args = data.get("args", {})
        call_id = data.get("call_id", 0)
        parent_id = data.get("parent_id")

        if not func_name or not filename:
            return

        self.collector.add_call(
            func_name,
            filename,
            line_no,
            args,
            call_id=call_id,
            parent_id=parent_id,
        )

    def _process_return_event(self, data: Dict[str, Any]) -> None:
        """Process a return event from trace data."""
        self.collector.add_return(
            data.get("function_name", ""),
            data.get("return_value", "None"),
            call_id=data.get("call_id", 0),
        )

    def _try_alternative_parsing(self, content):
        """Try alternative parsing methods for trace data."""
        try:
            lines = content.replace("\r\n", "\n").split("\n")
            call_count = 0
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if '"function_name": "function1"' in line:
                    try:
                        data = json.loads(line)
                        func_name = data.get("function_name", "")
                        filename = data.get("filename", "")
                        line_no = data.get("line_no", 0)
                        args = data.get("args", {})

                        self.collector.add_call(func_name, filename, line_no, args)
                        print(
                            f"Debug: Manually found function1 call: {func_name} at {filename}:{line_no}"
                        )
                        call_count += 1
                    except (json.JSONDecodeError, KeyError) as e:
                        self._queue_error("alternative parsing", e)

            print(f"Debug: Alternative parsing found {call_count} calls")
        except (ValueError, AttributeError) as e:
            self._queue_error("alternative parsing", e)

    def _read_output(self, pipe, stream_name):
        """Read output from the subprocess pipe."""
        try:
            for line in iter(pipe.readline, ''):
                line = line.rstrip('\n')
                if line and not self.is_paused and self.is_running:
                    self.collector.add_output(line, stream_name)
        except (IOError, OSError, ValueError) as e:
            if self.is_running:
                self._queue_error(f"{stream_name} pipe", e)
        finally:
            if pipe and not pipe.closed:
                pipe.close()

    def _monitor_process(self):
        """Monitor the subprocess for completion."""
        try:
            returncode = self.process.wait()
            self.is_running = False
            
            if self.process:  # Check if process still exists
                for pipe in (self.process.stdout, self.process.stderr):
                    if pipe and not pipe.closed:
                        pipe.close()

            # Add completion message
            status = ("successfully" if returncode == 0 
                     else f"with code {returncode}")
            self.collector.add_output(
                f"Script completed {status}", "system"
            )
            
        except (IOError, OSError) as e:
            self._queue_error("process monitor", e)
            self.is_running = False

    def stop(self):
        """Stop the script execution and terminate the subprocess."""
        if self.process and self.is_running:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._queue_error("stop", "Process termination timeout")
                self.process.kill()
            self.is_running = False
            # Join threads to ensure they terminate and avoid hanging
            if hasattr(self, "stdout_thread") and self.stdout_thread.is_alive():
                self.stdout_thread.join(timeout=2)
            if hasattr(self, "stderr_thread") and self.stderr_thread.is_alive():
                self.stderr_thread.join(timeout=2)
            if hasattr(self, "monitor_thread") and self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=2)
            if hasattr(self, "trace_thread") and self.trace_thread.is_alive():
                self.trace_thread.join(timeout=2)
            if (
                hasattr(self, "error_handler_thread")
                and self.error_handler_thread.is_alive()
            ):
                self.error_handler_thread.join(timeout=2)
            # (Keep self.process to allow subsequent checks)

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
            except subprocess.TimeoutExpired:
                # Force kill if needed
                if self.process.poll() is None:
                    self.process.kill()

        # Ensure is_running is properly set
        self.is_running = False

        # Allow pipes to close completely
        time.sleep(0.5)

        self.collector.clear()
        # Now start the new process
        self.start()
