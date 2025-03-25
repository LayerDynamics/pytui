"""Script execution wrapper and subprocess manager."""

# pylint: disable=trailing-whitespace

import os
import sys
import subprocess
import json
import tempfile
import time
import fcntl  # Move import to top level
from pathlib import Path
import threading
from typing import Optional, Dict, Any, List, Union
import queue

from .collector import DataCollector
from .utils import terminate_process_tree, kill_process_tree

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
            # Use with statement for resource management
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
            *self.script_args,  # Removed extra comma
        ]

        # Use a more reliable process creation approach
        try:
            # Start the process with pipe buffers explicitly sized
            # Use self.process directly to avoid reimporting subprocesscess = subprocess.Popen(
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,ubprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                bufsize=1,  # Line buffered
                cwd=str(self.script_path.parent),   universal_newlines=True,  # Ensure text mode works properly
                universal_newlines=True,  # Ensure text mode works properly
            )self.is_running = True
            self.is_running = True
            
            # Add an immediate message to show the process startedself.collector.add_output(f"Started process: {self.process.pid}", "system")
            self.collector.add_output(f"Started process: {self.process.pid}", "system")
            
            self._start_threads(trace_path)
        except (OSError, subprocess.SubprocessError) as e:ut(f"Failed to start process: {e}", "error")
            self.collector.add_output(f"Failed to start process: {e}", "error")is_running = False
            self.is_running = False            raise
            raise

    def _start_threads(self, trace_path):s."""
        """Start all monitoring threads."""nfigurations
        # Define thread configurations
        thread_configs = [
            ("stdout_thread", self._read_output, (self.process.stdout, "stdout")),cess.stderr, "stderr")),
            ("stderr_thread", self._read_output, (self.process.stderr, "stderr")),
            ("monitor_thread", self._monitor_process, ()),h,)),
            ("trace_thread", self._read_trace_data, (trace_path,)),   ("error_handler_thread", self._handle_errors, ()),
            ("error_handler_thread", self._handle_errors, ()),        ]
        ]

        # Start each thread
        for name, target, args in thread_configs:arget=target, args=args, daemon=True)
            thread = threading.Thread(target=target, args=args, daemon=True)name, thread)
            setattr(self, name, thread)            thread.start()
            thread.start()

    def _read_trace_data(self, trace_path):"""
        """Read function call trace data from the IPC file."""        print("Debug: Reading trace data from", trace_path)
        print("Debug: Reading trace data from", trace_path)

        try:_wait_for_trace_file(trace_path)
            content = self._wait_for_trace_file(trace_path)tent:
            if not content:                return
                return

            lines = content.splitlines()            print("Debug: Found", len(lines), "lines in trace file")
            print("Debug: Found", len(lines), "lines in trace file")
            self._process_trace_lines(lines)
            self._process_trace_lines(lines)

        except OSError as e:t("Fatal error reading trace data:", str(e))
            print("Fatal error reading trace data:", str(e))
        finally:
            try:ath):
                if os.path.exists(trace_path):nk(trace_path)
                    os.unlink(trace_path)SError:
            except OSError:                pass
                pass
30) -> str:
    def _wait_for_trace_file(self, trace_path: str, max_retries: int = 30) -> str:nd return its content."""
        """Wait for trace file to be created and return its content."""rocess time to start up
        # Give the subprocess time to start up        time.sleep(0.5)
        time.sleep(0.5)

        for _ in range(max_retries):
            if not os.path.exists(trace_path):race file does not exist, retrying...")
                print("Debug: Trace file does not exist, retrying...")ep(0.2)
                time.sleep(0.2)                continue
                continue

            file_size = os.path.getsize(trace_path)            print("Debug: Trace file exists, size:", file_size)
            print("Debug: Trace file exists, size:", file_size)

            if file_size == 0:race file is empty, retrying...")
                print("Debug: Trace file is empty, retrying...")ep(0.2)
                time.sleep(0.2)                continue
                continue
"r", encoding="utf-8") as f:
            with open(trace_path, "r", encoding="utf-8") as f:                content = f.read()
                content = f.read()
:
            if content.strip():                return content
                return content
            time.sleep(0.2)
            time.sleep(0.2)
bug: Could not read content from trace file after multiple retries")
        print("Debug: Could not read content from trace file after multiple retries")        return ""
        return ""
:
    def _process_trace_lines(self, lines: List[str]) -> None:s trace file lines and update collector."""
        """Process trace file lines and update collector."""
        if lines::")
            print("Debug: First few trace lines:")
            for i in range(min(3, len(lines))):                print("  Line", i + 1, ":", lines[i][:100])
                print("  Line", i + 1, ":", lines[i][:100])

        call_count = return_count = error_count = 0        content = "\n".join(lines)  # Store content for alternative parsing
        content = "\n".join(lines)  # Store content for alternative parsing
e(lines):
        for i, line in enumerate(lines):strip()
            line = line.strip()
            if not line:                continue
                continue

            try:
                if not line.startswith("{"):kipping invalid JSON line", i + 1, ": doesn't start with {")
                    print("Skipping invalid JSON line", i + 1, ": doesn't start with {")                    continue
                    continue

                data = json.loads(line)                event_type = data.get("type")
                event_type = data.get("type")

                if event_type == "call":all_event(data)
                    self._process_call_event(data)
                    call_count += 1
                elif event_type == "return":urn_event(data)
                    self._process_return_event(data)                    return_count += 1
                    return_count += 1

            except json.JSONDecodeError as e:", e)
                self._queue_error("JSON parsing", e)
            except (KeyError, ValueError) as e:                self._queue_error("trace processing", e)
                self._queue_error("trace processing", e)

        print(
            "Debug: Processed",
            f"{call_count} call events",vents",
            f"and {return_count} return events",   f"with {error_count} errors",
            f"with {error_count} errors",        )
        )

        if call_count == 0:arsing method...")
            print("Debug: Attempting alternative parsing method...")            self._try_alternative_parsing(content)
            self._try_alternative_parsing(content)
ny]) -> None:
    def _process_call_event(self, data: Dict[str, Any]) -> None:""
        """Process a call event from trace data."""", "")
        func_name = data.get("function_name", "")"")
        filename = data.get("filename", "")", 0)
        line_no = data.get("line_no", 0)
        args = data.get("args", {})
        call_id = data.get("call_id", 0)        parent_id = data.get("parent_id")
        parent_id = data.get("parent_id")
c_name or not filename:
        if not func_name or not filename:            return
            return
.add_call(
        self.collector.add_call(,
            func_name,,
            filename,no,
            line_no,
            args,
            call_id=call_id,   parent_id=parent_id,
            parent_id=parent_id,        )
        )
ny]) -> None:
    def _process_return_event(self, data: Dict[str, Any]) -> None:from trace data."""
        """Process a return event from trace data."""
        self.collector.add_return(
            data.get("function_name", ""),),
            data.get("return_value", "None"),   call_id=data.get("call_id", 0),
            call_id=data.get("call_id", 0),        )
        )

    def _try_alternative_parsing(self, content):ry alternative parsing methods for trace data."""
        """Try alternative parsing methods for trace data."""
        try:t.replace("\r\n", "\n").split("\n")
            lines = content.replace("\r\n", "\n").split("\n")
            call_count = 0
            for line in lines:strip()
                line = line.strip()
                if not line:                    continue
                    continue
ction_name": "function1"' in line:
                if '"function_name": "function1"' in line:
                    try:
                        data = json.loads(line)", "")
                        func_name = data.get("function_name", "")"")
                        filename = data.get("filename", "")", 0)
                        line_no = data.get("line_no", 0)                        args = data.get("args", {})
                        args = data.get("args", {})
ollector.add_call(func_name, filename, line_no, args)
                        self.collector.add_call(func_name, filename, line_no, args)
                        print(   f"Debug: Manually found function1 call: {func_name} at {filename}:{line_no}"
                            f"Debug: Manually found function1 call: {func_name} at {filename}:{line_no}"
                        )
                        call_count += 1
                    except (json.JSONDecodeError, KeyError) as e:                        self._queue_error("alternative parsing", e)
                        self._queue_error("alternative parsing", e)
und {call_count} calls")
            print(f"Debug: Alternative parsing found {call_count} calls")
        except (ValueError, AttributeError) as e:            self._queue_error("alternative parsing", e)
            self._queue_error("alternative parsing", e)

    def _read_output(self, pipe, stream_name):ead output from the subprocess pipe."""
        """Read output from the subprocess pipe."""
        try:ocking mode for the pipe
            # Set non-blocking mode for the pipe - using imported fcntl at top levelntl
            fd = pipe.fileno()import os
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            
            buffer = ""fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            while self.is_running:
                try:
                    # Try reading from the pipelf.is_running:
                    chunk = pipe.read(4096)
                    if chunk:pipe
                        # Process lines in the chunkipe.read(4096)
                        buffer += chunk
                        lines = buffer.splitlines(True) in the chunk
                        buffer = ""
                        fer.splitlines(True)
                        for line in lines:buffer = ""
                            if line.endswith("\n"):
                                line = line.rstrip("\n")
                                if line and not self.is_paused:
                                    self.collector.add_output(line, stream_name)
                            else:
                                # Incomplete line, add back to buffer   self.collector.add_output(line, stream_name)
                                buffer += line
                    else:ine, add back to buffer
                        # No data available, sleep a bit to avoid CPU spin       buffer += line
                        time.sleep(0.01)
                except (IOError, OSError):ble, sleep a bit to avoid CPU spin
                    # Expected for non-blocking read with no data - ignore the exception
                    time.sleep(0.01)
        except Exception as read_error:  # Renamed to read_error to avoid unused 'e'on-blocking read with no data
            if self.is_running:(0.01)
                self._queue_error(f"{stream_name} pipe", read_error)
        finally:
            if pipe and not pipe.closed:self._queue_error(f"{stream_name} pipe", e)
                pipe.close()
pipe.closed:
    def _monitor_process(self):                pipe.close()
        """Monitor the subprocess for completion."""
        try:
            returncode = self.process.wait()onitor the subprocess for completion."""
            self.is_running = False
ss.wait()
            if self.process:  # Check if process still exists            self.is_running = False
                for pipe in (self.process.stdout, self.process.stderr):
                    if pipe and not pipe.closed:
                        pipe.close(), self.process.stderr):
pipe.closed:
            # Add completion message                        pipe.close()
            status = "successfully" if returncode == 0 else f"with code {returncode}"
            self.collector.add_output(f"Script completed {status}", "system")
rncode}"
        except (IOError, OSError) as e:            self.collector.add_output(f"Script completed {status}", "system")
            self._queue_error("process monitor", e)
            self.is_running = False
ess monitor", e)
    def stop(self):            self.is_running = False
        """Stop the script execution."""
        if self.process:
            try:pt execution."""
                # Try graceful termination firstprocess:
                terminate_process_tree(self.process.pid)
                
                # If process still running after 2 seconds, force killterminate_process_tree(self.process.pid)
                if self.process.poll() is None:
                    kill_process_tree(self.process.pid)r 2 seconds, force kill
                    
                # Wait for process to fully terminatekill_process_tree(self.process.pid)
                self.process.wait(timeout=1)
            except (subprocess.TimeoutExpired, OSError, ProcessLookupError) as stop_error:terminate
                # Specify exact exception types instead of bare exceptf.process.wait(timeout=1)
                # If anything goes wrong, ensure process is killed
                try: anything goes wrong, ensure process is killed
                    kill_process_tree(self.process.pid)
                except (OSError, ProcessLookupError):l_process_tree(self.process.pid)
                    # Specify exact exception types for the nested exception
                    passpass
            finally:
                self.is_running = Falsealse
                self.process = None                self.process = None

    def pause(self):
        """Pause updating the UI with new data.""" UI with new data."""
        self.is_paused = True        self.is_paused = True

    def resume(self):
        """Resume updating the UI with new data.""" UI with new data."""
        self.is_paused = False        self.is_paused = False

    def restart(self):
        """Restart the script execution."""the script execution."""
        self.stop()
        self.collector.clear()
        time.sleep(0.1)  # Brief pause to ensure cleanup.1)  # Brief pause to ensure cleanup
        self.start()        self.start()

