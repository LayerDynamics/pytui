"""Performance tests for pytui components."""

import os
import sys
import time
import tempfile
import pytest
from pathlib import Path
import cProfile
import pstats
import io

from pytui.executor import ScriptExecutor
from pytui.collector import DataCollector
from pytui.tracer import install_trace, trace_function

@pytest.fixture
def performance_script():
    """Create a script for performance testing."""
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as f:
        f.write("""
# Performance test script
import time

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)

def compute_values():
    start = time.time()
    
    # Call fibonacci with moderate values
    results = []
    for i in range(20):
        results.append(fibonacci(i))
    print(f"Fibonacci results: {results}")
    
    # Call factorial with moderate values
    fact_results = []
    for i in range(10):
        fact_results.append(factorial(i))
    print(f"Factorial results: {fact_results}")
    
    end = time.time()
    print(f"Total computation time: {end - start:.4f} seconds")
    return results, fact_results

compute_values()
""")
    yield Path(f.name)
    # Clean up
    os.unlink(f.name)

@pytest.mark.slow
def test_executor_overhead(performance_script):
    """Measure overhead of running a script through the executor vs directly."""
    # First run the script directly to get baseline
    direct_start = time.time()
    result = os.system(f"{sys.executable} {performance_script}")
    direct_end = time.time()
    direct_time = direct_end - direct_start
    
    # Run through executor
    executor = None
    executor_start = time.time()
    try:
        executor = ScriptExecutor(performance_script)
        executor.start()
        
        # Wait for completion
        max_wait = 30  # Longer wait time for performance test
        start_time = time.time()
        completed = False
        
        while time.time() - start_time < max_wait and not completed:
            if any("Total computation time" in line.content for line in executor.collector.output):
                completed = True
            time.sleep(0.1)
            
        executor_end = time.time()
        executor_time = executor_end - executor_start
        
        # Verify script completed
        assert completed, "Script did not complete in the expected time"
        
        # Calculate and print overhead
        overhead = executor_time / direct_time
        print(f"\nPerformance comparison:")
        print(f"  Direct execution time: {direct_time:.4f} seconds")
        print(f"  Executor execution time: {executor_time:.4f} seconds")
        print(f"  Overhead factor: {overhead:.2f}x")
        
        # Executor will be slower, but not unreasonably so
        assert overhead < 20, f"Executor overhead too high: {overhead:.2f}x"
        
        # Verify tracing data was collected
        fib_calls = len([call for call in executor.collector.calls if call.function_name == "fibonacci"])
        fact_calls = len([call for call in executor.collector.calls if call.function_name == "factorial"])
        
        print(f"  Fibonacci calls traced: {fib_calls}")
        print(f"  Factorial calls traced: {fact_calls}")
        
        # We should have traced multiple calls to both functions
        assert fib_calls > 0, "No fibonacci calls were traced"
        assert fact_calls > 0, "No factorial calls were traced"
        
    finally:
        # Ensure cleanup
        if executor:
            executor.stop()

def test_tracer_function_performance():
    """Test the performance of the trace_function with profiling."""
    # Create a collector
    collector = DataCollector()
    
    # Install tracing
    install_trace(collector)
    
    # Create fake frames to trace
    class MockCode:
        def __init__(self, name, filename):
            self.co_name = name
            self.co_filename = filename
            self.co_firstlineno = 1
    
    class MockFrame:
        def __init__(self, func_name, filename, lineno, locals_dict=None):
            self.f_code = MockCode(func_name, filename)
            self.f_lineno = lineno
            self.f_locals = locals_dict or {"arg1": "value1"}
            
    # Profile trace_function for call events
    pr = cProfile.Profile()
    pr.enable()
    
    # Call trace_function many times
    for i in range(1000):
        frame = MockFrame(f"test_func{i}", "test.py", i, {"index": i})
        trace_function(frame, "call", None)
        
    # Call for return events
    for i in range(1000):
        frame = MockFrame(f"test_func{i}", "test.py", i)
        trace_function(frame, "return", f"result{i}")
    
    pr.disable()
    
    # Print profiling stats
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(20)  # Print top 20 functions by cumulative time
    
    print("\nTracer Performance Profile:")
    print(s.getvalue())
    
    # Verify events were collected
    assert len(collector.calls) == 1000, "Not all calls were traced"
    assert len(collector.returns) == 1000, "Not all returns were traced"
    
    # Calculate average time
    total_time = sum(stat.cumulative for _, stat in ps.stats.items() if "trace_function" in str(_[2]))
    avg_time = total_time / 2000  # 1000 calls + 1000 returns
    
    print(f"Average time per trace_function call: {avg_time*1000:.6f} ms")
    
    # Time should be reasonably small (adjust threshold as needed)
    assert avg_time < 0.001, f"trace_function too slow: {avg_time*1000:.6f} ms per call"

@pytest.mark.asyncio
async def test_collector_event_throughput():
    """Test throughput of the collector's event processing."""
    import asyncio
    
    # Create collector
    collector = DataCollector()
    
    # Add many events
    start_time = time.time()
    
    # Add events in a tight loop
    for i in range(10000):
        collector.add_output(f"Output line {i}", "stdout")
        
    mid_time = time.time()
    
    # Measure time to retrieve events
    received_count = 0
    get_start = time.time()
    
    # Create multiple consumers
    async def consumer(consumer_id, count):
        nonlocal received_count
        for _ in range(count):
            event_type, event = await collector.get_event()
            received_count += 1
            if received_count % 1000 == 0:
                print(f"Consumer {consumer_id} received {received_count} events")
    
    # Start multiple consumers
    tasks = []
    consumer_count = 4
    events_per_consumer = 2500  # Total 10000 events
    
    for i in range(consumer_count):
        task = asyncio.create_task(consumer(i, events_per_consumer))
        tasks.append(task)
    
    # Wait for all consumers to finish
    await asyncio.gather(*tasks)
    
    get_end = time.time()
    
    # Calculate and print metrics
    add_time = mid_time - start_time
    get_time = get_end - get_start
    
    add_rate = 10000 / add_time
    get_rate = 10000 / get_time
    
    print(f"\nCollector performance:")
    print(f"  Add 10000 events: {add_time:.4f} seconds ({add_rate:.2f} events/sec)")
    print(f"  Get 10000 events: {get_time:.4f} seconds ({get_rate:.2f} events/sec)")
    
    # Verify event throughput is reasonable
    assert add_rate > 1000, f"Event add rate too low: {add_rate:.2f} events/sec"
    assert get_rate > 100, f"Event get rate too low: {get_rate:.2f} events/sec"
    assert received_count == 10000, f"Not all events were received: {received_count}/10000"
