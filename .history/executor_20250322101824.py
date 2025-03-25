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
        if 'PYTHONPATH' in env:
            python_paths.extend(env['PYTHONPATH'].split(os.pathsep))
        env['PYTHONPATH'] = os.pathsep.join(python_paths)
        
        # Create a named pipe or temporary file for IPC
        self.trace_fifo = tempfile.NamedTemporaryFile(delete=False, prefix='pytui_trace_', suffix='.jsonl')
        trace_path = self.trace_fifo.name
        self.trace_fifo.close()  # Close it so the subprocess can write to it
        
        # Set up hook to inject tracer with IPC path
        env['PYTUI_TRACE'] = "1"
        env['PYTUI_TRACE_PATH'] = trace_path
        
        # Updated bootstrap code with IPC for function traces
        bootstrap_code = (
            "import os, sys, threading, json\n"
            "def setup_tracing():\n"
            "    # Set up Python path\n"
            "    sys.path[:0] = os.environ['PYTHONPATH'].split(os.pathsep)\n"
            "    from pytui.tracer import install_trace\n"
            "    from pytui.collector import get_collector\n"
            "    # Get the trace path from environment\n"
            "    trace_path = os.environ.get('PYTUI_TRACE_PATH')\n"
            "    # Initialize collector\n"
            "    collector = get_collector()\n"
            "    # Set up the tracer with IPC path\n"
            "    install_trace(collector, trace_path)\n"
            "    return collector\n"
            "\n"
            "collector = setup_tracing()\n"
            "\n"
            "script_path = os.path.abspath(sys.argv[1])\n"
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
            "    exec(code, globals_dict)\n"
            "except Exception as e:\n"
            "    import traceback\n"
            "    traceback.print_exc()\n"
            "finally:\n"
            "    # Signal tracer to flush remaining data\n"
            "    if hasattr(collector, 'flush'):\n"
            "        collector.flush()\n"
        )

        # Start subprocess with piped outputs - split long command line
        cmd = [
            sys.executable,
            "-c",
            bootstrap_code,
            str(self.script_path.absolute()),
            *self.script_args
        ]

        # Start process
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            text=True,
            bufsize=1,
            cwd=str(self.script_path.parent)
        )
        
        self.is_running = True
        
        # Start reader threads
        self.stdout_thread = threading.Thread(
            target=self._read_output,
            args=(self.process.stdout, "stdout"),
            daemon=True
        )
        self.stdout_thread.start()
        
        self.stderr_thread = threading.Thread(
            target=self._read_output,
            args=(self.process.stderr, "stderr"),
            daemon=True
        )
        self.stderr_thread.start()
        
        # Start thread to monitor process completion
        self.monitor_thread = threading.Thread(
            target=self._monitor_process,
            daemon=True
        )
        self.monitor_thread.start()
        
        # Start thread to read trace data
        self.trace_thread = threading.Thread(
            target=self._read_trace_data,
            args=(trace_path,),
            daemon=True
        )
        self.trace_thread.start()
    
    def _read_trace_data(self, trace_path):
        """Read function call trace data from the IPC file."""
        # Wait a moment to ensure the subprocess has started
        import time
        time.sleep(0.1)
        
        try:
            with open(trace_path, 'r') as f:
                while self.is_running:
                    line = f.readline()
                    if not line:
                        time.sleep(0.05)  # Don't hog CPU
                        continue
                    
                    try:
                        # Parse the trace event
                        data = json.loads(line.strip())
                        event_type = data.get('type')
                        
                        if event_type == 'call':
                            # Add call to the collector
                            self.collector.add_call(
                                data['function_name'],
                                data['filename'],
                                data['line_no'],
                                data['args'],
                                call_id=data.get('call_id', 0),
                                parent_id=data.get('parent_id')
                            )
                        elif event_type == 'return':
                            # Add return to the collector
                            self.collector.add_return(
                                data['function_name'],
                                data['return_value'],
                                call_id=data.get('call_id', 0)
                            )
                    except json.JSONDecodeError:
                        # Skip malformed JSON
                        continue
                    except Exception as e:
                        print(f"Error processing trace data: {e}")
        except Exception as e:
            print(f"Error reading trace data: {e}")
        finally:
            # Clean up the trace file
            try:
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
                
                line = line.rstrip('\n')
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
            self.collector.add_output(f"Process exited with code {returncode}", "system")
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
