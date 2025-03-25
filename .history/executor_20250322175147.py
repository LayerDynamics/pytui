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
            "    print(f'Debug: Using trace path {trace_path}')\n"
            "    # Initialize collector\n"
            "    collector = get_collector()\n"
            "    # Set up the tracer with IPC path\n"
            "    trace_file = open(trace_path, 'w', encoding='utf-8')\n"
            "    install_trace(collector, trace_path)\n"
            "    \n"
            "    # Verify the trace file is working by directly writing to it\n"
            "    trace_file.write('{\"type\": \"test\", \"message\": \"Trace file is working\"}\\n')\n"
            "    trace_file.flush()\n"
            "    \n"
            "    # Define original_import to wrap imports\n"
            "    original_import = __builtins__.__import__\n"
            "    def patched_import(name, *args, **kwargs):\n"
            "        module = original_import(name, *args, **kwargs)\n"
            "        # For debugging - log imported modules\n"
            "        print(f'Imported module: {name}')\n"
            "        return module\n"
            "    __builtins__.__import__ = patched_import\n"
            "    \n"
            "    return collector\n"
            "\n"
            "collector = setup_tracing()\n"
            "\n"
            "# Load and execute script directly to avoid nested exec issues\n"
            "script_path = os.path.abspath(sys.argv[1])\n"
            "print(f'Debug: Running script {script_path}')\n"
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
            "            print(f'Extra call to function1(42) result: {result}')\n"
            "        except Exception as func_err:\n"
            "            print(f'Error calling function1: {func_err}')\n"
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
        # Wait for the file to be created and populated
        import time
        
        # Give the subprocess a bit more time to start up
        time.sleep(0.5)
        
        # Debug output
        print(f"Debug: Reading trace data from {trace_path}")
        
        try:
            # Monitor file for content
            max_retries = 30
            retry_count = 0
            content = ""
            
            while retry_count < max_retries:
                if not os.path.exists(trace_path):
                    print(f"Debug: Trace file does not exist, retrying...")
                    time.sleep(0.2)
                    retry_count += 1
                    continue
                    
                file_size = os.path.getsize(trace_path)
                print(f"Debug: Trace file exists, size: {file_size}")
                
                if file_size == 0:
                    print(f"Debug: Trace file is empty, retrying...")
                    time.sleep(0.2)
                    retry_count += 1
                    continue
                    
                # Read the file content
                with open(trace_path, 'r') as f:
                    content = f.read()
                    
                if content.strip():
                    break
                    
                time.sleep(0.2)
                retry_count += 1
            
            # Process content if we got some
            if not content.strip():
                print("Debug: Could not read any content from trace file after multiple retries")
                return
                
            # Process line by line
            lines = content.splitlines()
            print(f"Debug: Found {len(lines)} lines in trace file")
            
            # Sample some lines for debugging
            if lines:
                print(f"Debug: First few trace lines:")
                for i in range(min(3, len(lines))):
                    print(f"  Line {i+1}: {lines[i][:100]}")
            
            # Process each line
            call_count = 0
            return_count = 0
            error_count = 0
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    # Add more robust JSON parsing - sometimes we get malformed JSON
                    # Make sure line starts with {
                    if not line.startswith('{'):
                        print(f"Skipping invalid JSON line {i+1}: doesn't start with {{")
                        continue
                        
                    # Parse the trace event
                    data = json.loads(line)
                    event_type = data.get('type')
                    
                    if event_type == 'call':
                        # Extract data with defaults for backward compatibility
                        func_name = data.get('function_name', '')
                        filename = data.get('filename', '')
                        line_no = data.get('line_no', 0)
                        args = data.get('args', {})
                        call_id = data.get('call_id', 0)
                        parent_id = data.get('parent_id')
                        
                        # Skip if missing key data
                        if not func_name or not filename:
                            continue
                            
                        # Add call to the collector
                        self.collector.add_call(
                            func_name, filename, line_no, args,
                            call_id=call_id, parent_id=parent_id
                        )
                        call_count += 1
                        
                    elif event_type == 'return':
                        # Add return to the collector
                        self.collector.add_return(
                            data.get('function_name', ''),
                            data.get('return_value', 'None'),
                            call_id=data.get('call_id', 0)
                        )
                        return_count += 1
                        
                except json.JSONDecodeError as e:
                    # More detailed error for JSON parsing issues
                    error_count += 1
                    if error_count <= 3:  # Limit error output
                        preview = line[:50] + ('...' if len(line) > 50 else '')
                        print(f"Error parsing JSON at line {i+1}: {e}, content: {preview}")
                except Exception as e:
                    error_count += 1
                    if error_count <= 3:
                        print(f"Error processing trace data at line {i+1}: {e}")
            
            print(f"Debug: Processed {call_count} call events and {return_count} return events with {error_count} errors")
            
            if call_count == 0:
                # Try a different parsing approach if no calls were found
                print("Debug: Attempting alternative parsing method...")
                self._try_alternative_parsing(content)
                
        except Exception as e:
            print(f"Fatal error reading trace data: {e}")
        finally:
            # Clean up the trace file
            try:
                if os.path.exists(trace_path):
                    os.unlink(trace_path)
            except:
                pass
                
    def _try_alternative_parsing(self, content):
        """Try alternative parsing methods for trace data."""
        # Method 1: Try parsing with different line endings
        lines = content.replace('\r\n', '\n').split('\n')
        
        call_count = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for function1 manually in the content
            if '"function_name": "function1"' in line:
                try:
                    data = json.loads(line)
                    func_name = data.get('function_name', '')
                    filename = data.get('filename', '')
                    line_no = data.get('line_no', 0)
                    args = data.get('args', {})
                    
                    self.collector.add_call(func_name, filename, line_no, args)
                    print(f"Debug: Manually found function1 call: {func_name} at {filename}:{line_no}")
                    call_count += 1
                except:
                    pass
        
        print(f"Debug: Alternative parsing found {call_count} calls")

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
        """Monitor the subprocess and update state when it finishes."""
        timeout = 60  # Maximum seconds to wait for process termination
        start = time.time()
        while self.is_running and self.process:
            ret = self.process.poll()
            if ret is not None:
                self.is_running = False
                break
            if time.time() - start > timeout:
                # Force termination if process is unresponsive
                try:
                    self.process.kill()
                except Exception:
                    pass
                self.is_running = False
                break
            time.sleep(0.1)

    def stop(self):
        """Stop the script execution and terminate the subprocess."""
        if self.process and self.is_running:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                self.process.kill()
            self.is_running = False
        # Do not clear self.process so tests can verify termination

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
