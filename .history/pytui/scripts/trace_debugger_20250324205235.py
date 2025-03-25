"""
Diagnostic tool to debug tracing issues.

This script helps diagnose issues with the pytui tracer by providing
detailed logs and test scenarios that validate tracer behavior.
"""

import sys
import os
import timetr
from pathlib import Path

# Add the parent directory to sys.path to allow importing pytui modules
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from pytui.tracer import install_trace, trace_function, _should_skip_file
from pytui.collector import DataCollector


def run_test_case(name, func):
    """Run a test case and report results."""
    print(f"\n=== Running test: {name} ===")
    start_time = time.time()
    
    # Create a fresh collector
    collector = DataCollector()
    install_trace(collector)
    
    try:
        # Run the test function
        result = func()
        duration = time.time() - start_time
        
        # Output stats
        print(f"- Duration: {duration:.4f}s")
        print(f"- Output events: {len(collector.output)}")
        print(f"- Call events: {len(collector.calls)}")
        print(f"- Return events: {len(collector.returns)}")
        print(f"- Exception events: {len(collector.exceptions)}")
        
        # Show all captured function calls
        if collector.calls:
            print("\nCaptured function calls:")
            for call in collector.calls:
                print(f"  - {call.function_name} @ {call.filename}:{call.line_no}")
        
        return True, result
    except Exception as e:
        print(f"ERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False, Nonec()
    finally:rn False, None
        # Clean up
        sys.settrace(None)
        sys.settrace(None)

def test_simple_function():
    """Test tracing a simple function."""
    def simple_function(x, y):unction."""
        return x + y
    def simple_function(x, y):
    result = simple_function(5, 10)
    return result
    result = simple_function(5, 10)
    return result
def test_exception_handling():
    """Test capturing exceptions."""
    def function_with_exception():
        try:capturing exceptions."""
            1/0
        except ZeroDivisionError as e:
            # Handled exception
            return f"Caught: {e}"
        except ZeroDivisionError as e:
    result = function_with_exception()
    return resultn f"Caught: {e}"

    result = function_with_exception()
def test_skip_internal():
    """Test that internal modules are skipped."""
    filename1 = "/path/to/pytui/tracer.py"
    filename2 = "/path/to/user/script.py"
    """Test that internal modules are skipped."""
    print(f"Should skip {filename1}: {_should_skip_file(filename1)}")
    print(f"Should skip {filename2}: {_should_skip_file(filename2)}")
    return _should_skip_file(filename1) and not _should_skip_file(filename2)
    print(f"Should skip {filename1}: {_should_skip_file(filename1)}")
    print(f"Should skip {filename2}: {_should_skip_file(filename2)}")
def test_nested_functions():_should_skip_file(filename1) and not _should_skip_file(filename2)
    """Test tracing nested function calls."""
    def outer_function(x):
        def inner_function(y):
            return y * 2"""Run all diagnostics."""
        return inner_function(x) + 1Diagnostic Tool")
    ==========================")
    result = outer_function(5)  # Should trace both outer and inner functions
    return result

   ("Simple Function", test_simple_function),
def test_large_output():    ("Exception Handling", test_exception_handling),
    """Test handling large function outputs."""nternal Modules", test_skip_internal),
    def generate_large_output():
        # Generate a large string (about 10KB)
        return "x" * 10240
    for name, func in tests:
    result = generate_large_output()sult = run_test_case(name, func)
    return f"Length: {len(result)}"success, result))


def test_concurrent_execution():
    """Test tracing with concurrent execution."""for name, success, result in results:
    import threadingif success else "FAIL"
    
    results = []
    
    def worker(n):name for name, success, _ in results if not success]
        results.append(n * n)ilures:
    sts failed: {', '.join(failures)}")
    threads = []
    for i in range(5):    else:
        t = threading.Thread(target=worker, args=(i,))        print("\nAll tests passed!")
        threads.append(t)
        t.start()
    













































    sys.exit(main())if __name__ == "__main__":        return 0        print("\nAll tests passed!")    else:        return 1        print(f"\n{len(failures)} tests failed: {', '.join(failures)}")    if failures:    failures = [name for name, success, _ in results if not success]    # Print any failures            print(f"{status}: {name}")        status = "PASS" if success else "FAIL"    for name, success, result in results:    print("\n=== Summary ===")    # Print summary            results.append((name, success, result))        success, result = run_test_case(name, func)    for name, func in tests:    results = []        ]        ("Concurrent Execution", test_concurrent_execution),        ("Large Output", test_large_output),        ("Nested Functions", test_nested_functions),        ("Skip Internal Modules", test_skip_internal),        ("Exception Handling", test_exception_handling),        ("Simple Function", test_simple_function),    tests = [    # Run all test cases        print("============================")    print("PyTUI Tracer Diagnostic Tool")    """Run all diagnostics."""def main():    return sum(results)            t.join()    for t in threads:if __name__ == "__main__":
    sys.exit(main())
