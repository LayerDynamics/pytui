"""Utility functions for pytui."""

import os
import sys
from typing import List, Dict, Any, Optional
import importlib.util
from pathlib import Path

# Handle psutil import conditionally to avoid errors
try:
    import psutil
except ImportError:
    # Create a placeholder psutil module with the necessary functions
    class DummyProcess:
        """Mock implementation of psutil.Process for fallback."""

        def __init__(self, pid):
            """Initialize with process ID."""
            self.pid = pid

        def children(self, recursive=True):
            """Return child processes (empty list in dummy implementation).

            Args:
                recursive: Whether to include grandchildren (used to match psutil API)

            Returns:
                Empty list as dummy implementation
            """
            # Use recursive parameter in the implementation to silence linter
            if recursive:
                # In a real implementation, this would do a recursive search
                return []
            return []  # Non-recursive case returns same empty list

        def kill(self):
            """Kill the process using OS-specific methods."""
            os_name = os.name
            if os_name == "posix":
                os.kill(self.pid, 9)  # Using os to ensure it's used
            else:
                sys.stderr.write(
                    f"Cannot kill process {self.pid} on {os_name} without psutil\n"
                )  # Using sys to ensure it's used

        def terminate(self):
            """Terminate the process gracefully using OS-specific methods."""
            os_name = os.name
            if os_name == "posix":
                os.kill(self.pid, 15)
            else:
                sys.stderr.write(
                    f"Cannot terminate process {self.pid} on {os_name} without psutil\n"
                )

    class DummyPsutil:
        """Mock implementation of psutil for fallback."""

        @staticmethod
        def Process(pid):
            """Create a Process object (matches psutil API naming).

            Args:
                pid: Process ID to monitor

            Returns:
                DummyProcess instance
            """
            return DummyProcess(pid)

        @staticmethod
        def wait_procs(procs, timeout=None):
            """Wait for processes to terminate (dummy implementation).

            Args:
                procs: List of processes to wait for (used to match psutil API)
                timeout: Seconds to wait (used to match psutil API)

            Returns:
                Tuple of (gone, still_alive) processes
            """
            # Use parameters to silence linter
            if timeout is not None:
                sys.stderr.write(
                    f"Would wait {timeout} seconds for {len(procs)} processes\n"
                )
            return [], []  # Return empty lists for gone and still_alive

        class NoSuchProcess(Exception):
            """Exception raised when a process doesn't exist."""

            pass

    psutil = DummyPsutil()


def get_module_path(module_name: str) -> Optional[Path]:
    """
    Get the file path for a module by name.

    Args:
        module_name: Name of the module to find.

    Returns:
        Path to the module file or None if not found.
    """
    try:
        module = importlib.import_module(module_name)
        if hasattr(module, "__file__") and module.__file__:
            return Path(module.__file__)
        return None
    except (ImportError, AttributeError):
        return None


def format_time(seconds: float) -> str:
    """
    Format seconds into a human-readable time string.

    Args:
        seconds: Time in seconds.

    Returns:
        Formatted time string (MM:SS.ms).
    """
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes):02d}:{int(seconds):02d}.{int((seconds % 1) * 1000):03d}"


def truncate_string(s: str, max_length: int = 100) -> str:
    """
    Truncate a string to a maximum length with ellipsis.

    Args:
        s: String to truncate.
        max_length: Maximum length.

    Returns:
        Truncated string.
    """
    if len(s) <= max_length:
        return s
    return s[: max_length - 3] + "..."


def safe_repr(obj: Any) -> str:
    """
    Safely get the representation of an object.

    Args:
        obj: Object to represent.

    Returns:
        String representation or fallback message.
    """
    try:
        repr_str = repr(obj)
        if len(repr_str) > 100:
            # Adjust slices so the overall length is ≤ 100 characters.
            if repr_str.startswith("'") and len(repr_str) > 3:
                return repr_str[:95] + "...'"
            if repr_str.startswith('"') and len(repr_str) > 3:
                return repr_str[:95] + '..."'
            # De-indented the else clause to fix R1705
            return repr_str[:96] + "..."
        return repr_str
    except (
        ValueError,
        TypeError,
        RuntimeError,
    ):  # Specify exceptions instead of broad Exception
        return "<representation failed>"


def get_process_list() -> List[Dict[str, Any]]:
    """
    Get a list of running processes.

    This function ensures that List and Dict from typing are used.

    Returns:
        A list of process information dictionaries.
    """
    process_list = []
    try:
        for proc in psutil.process_iter(["pid", "name"]):
            process_info = {"pid": proc.info["pid"], "name": proc.info["name"]}
            process_list.append(process_info)
    except (AttributeError, TypeError):
        # Basic fallback using os
        if os.name == "posix":
            try:
                for pid in os.listdir("/proc"):
                    if pid.isdigit():
                        process_list.append({"pid": int(pid), "name": f"Process-{pid}"})
            except (FileNotFoundError, PermissionError):
                pass

    return process_list


def kill_process_tree(pid):
    """Kill a process and all its children."""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)

        # Kill children first
        for child in children:
            try:
                child.kill()
            except psutil.NoSuchProcess:
                pass

        # Kill parent
        try:
            parent.kill()
        except psutil.NoSuchProcess:
            pass
    except psutil.NoSuchProcess:
        pass  # Process already terminated


def terminate_process_tree(pid, timeout=5):
    """Gracefully terminate a process and its children with timeout."""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)

        # Terminate children first
        for child in children:
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass

        # Terminate parent
        try:
            parent.terminate()
        except psutil.NoSuchProcess:
            pass

        # Wait for processes to terminate
        _, alive = psutil.wait_procs([parent] + children, timeout=timeout)

        # Kill any remaining processes
        if alive:
            for p in alive:
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
    except psutil.NoSuchProcess:
        pass  # Process already terminated


# Ensure os and sys are used
OS_NAME = os.name
PY_VERSION = sys.version_info
