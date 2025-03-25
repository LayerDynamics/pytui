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

# Add file-level pylint disables to suppress some warnings:
# pylint: disable=redefined-outer-name, unused-variable, f-string-without-interpolation, too-few-public-methods, too-many-locals

@pytest.fixture
def performance_script():amedTemporaryFile(suffix=".py", delete=False, mode="w") as f:
    """Create a script for performance testing."""
    with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w') as f: """
        f.write("""# Performance test script
# Performance test script
import time
:
def fibonacci(n):
    if n <= 1:        return n
        return ncci(n-1) + fibonacci(n-2)
    return fibonacci(n-1) + fibonacci(n-2)
:
def factorial(n):
    if n <= 1:        return 1
        return 1ial(n-1)
    return n * factorial(n-1)
compute_values():
def compute_values():
    start = time.time()
    th moderate values
    # Call fibonacci with moderate values
    results = []
    for i in range(20):    results.append(fibonacci(i))
        results.append(fibonacci(i)))
    print(f"Fibonacci results: {results}")
    th moderate values
    # Call factorial with moderate values
    fact_results = []
    for i in range(10):    fact_results.append(factorial(i))
        fact_results.append(factorial(i)) results: {fact_results}")
    print(f"Factorial results: {fact_results}")
    
    end = time.time()    print(f"Total computation time: {end - start:.4f} seconds")
    print(f"Total computation time: {end - start:.4f} seconds")ts, fact_results
    return results, fact_results

compute_values()
""")
    yield Path(f.name)    yield Path(f.name)
    # Clean up
    os.unlink(f.name)

@pytest.mark.slow
def test_executor_overhead(performance_script):
    """Measure overhead of running a script through the executor vs directly."""
    # First run the script directly to get baselineunning a script through the executor vs directly."""
    direct_start = time.time()baseline
    _ = os.system(f"{sys.executable} {performance_script}")  # unused resultdirect_start = time.time()
    direct_end = time.time()sys.executable} {performance_script}")
    direct_time = direct_end - direct_startme.time()
    irect_start
    # Run through executor
    executor = None
    executor_start = time.time()
    try:utor_start = time.time()
        executor = ScriptExecutor(performance_script)
        executor.start()
        
        # Wait for completion
        max_wait = 30  # Longer wait time for performance test# Wait for completion
        start_time = time.time()
        completed = False
        
        while time.time() - start_time < max_wait and not completed:
            if any("Total computation time" in line.content for line in executor.collector.output):e time.time() - start_time < max_wait and not completed:
                completed = True
            time.sleep(0.1)ent
                    for line in executor.collector.output
        executor_end = time.time()
        executor_time = executor_end - executor_start
            time.sleep(0.1)
        # Verify script completed
        assert completed, "Script did not complete in the expected time"
        utor_start
        # Calculate and print overhead
        overhead = executor_time / direct_time
        print("\nPerformance comparison:")n the expected time"
        print("  Direct execution time: {:.4f} seconds".format(direct_time))
        print("  Executor execution time: {:.4f} seconds".format(executor_time))
        print("  Overhead factor: {:.2f}x".format(overhead))
        print(f"\nPerformance comparison:")
        # Executor will be slower, but not unreasonably soirect_time:.4f} seconds")
        assert overhead < 20, f"Executor overhead too high: {overhead:.2f}x"
        
        # Verify tracing data was collected
        fib_calls = len([call for call in executor.collector.calls if call.function_name == "fibonacci"]) so
        fact_calls = len([call for call in executor.collector.calls if call.function_name == "factorial"])gh: {overhead:.2f}x"
        
        print(f"  Fibonacci calls traced: {fib_calls}")
        print(f"  Factorial calls traced: {fact_calls}")
        
        # We should have traced multiple calls to both functions        call
        assert fib_calls > 0, "No fibonacci calls were traced"    for call in executor.collector.calls
        assert fact_calls > 0, "No factorial calls were traced"function_name == "fibonacci"
        
    finally:
        # Ensure cleanup        fact_calls = len(
        if executor:
            executor.stop()
 in executor.collector.calls
def test_tracer_function_performance():n_name == "factorial"
    """Test the performance of the trace_function with profiling."""        ]
    # Create a collector
    collector = DataCollector()
        print(f"  Fibonacci calls traced: {fib_calls}")
    # Install tracing traced: {fact_calls}")
    install_trace(collector)
    lls to both functions
    # Create fake frames to traceNo fibonacci calls were traced"
    class MockCode:orial calls were traced"
        def __init__(self, name, filename):
            self.co_name = namefinally:
            self.co_filename = filenameanup
            self.co_firstlineno = 1
    
    class MockFrame:
        def __init__(self, func_name, filename, lineno, locals_dict=None):
            self.f_code = MockCode(func_name, filename)cer_function_performance():
            self.f_lineno = linenoction with profiling."""
            self.f_locals = locals_dict or {"arg1": "value1"}
             DataCollector()
    # Profile trace_function for call events
    pr = cProfile.Profile()
    pr.enable()or)
    
    # Call trace_function many times
    for i in range(1000):s MockCode:
        frame = MockFrame(f"test_func{i}", "test.py", i, {"index": i})ame, filename):
        trace_function(frame, "call", None)= name
        
    # Call for return events
    for i in range(1000):
        frame = MockFrame(f"test_func{i}", "test.py", i)ame:
        trace_function(frame, "return", f"result{i}")    def __init__(self, func_name, filename, lineno, locals_dict=None):
    ockCode(func_name, filename)
    pr.disable()neno = lineno
    }
    # Print profiling stats
    s = io.StringIO()# Profile trace_function for call events
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    ps.print_stats(20)  # Print top 20 functions by cumulative time
    
    print("\nTracer Performance Profile:")es
    print(s.getvalue())
    
    # Verify events were collected    trace_function(frame, "call", None)
    assert len(collector.calls) == 1000, "Not all calls were traced"
    assert len(collector.returns) == 1000, "Not all returns were traced"
    
    # Calculate average time    frame = MockFrame(f"test_func{i}", "test.py", i)
    total_time = sum(stat.cumulative for _, stat in ps.stats.items() if "trace_function" in str(_[2]))
    avg_time = total_time / 2000  # 1000 calls + 1000 returns
    
    print("Average time per trace_function call: {:.6f} ms".format(avg_time*1000))
        # Print profiling stats
    # Time should be reasonably small (adjust threshold as needed))
    assert avg_time < 0.001, f"trace_function too slow: {avg_time*1000:.6f} ms per call"ts("cumulative")
 time
@pytest.mark.asyncio
async def test_collector_event_throughput():print("\nTracer Performance Profile:")
    """Test throughput of the collector's event processing.""")
    import asyncio
    # Verify events were collected
    # Create collectortor.calls) == 1000, "Not all calls were traced"
    collector = DataCollector()urns) == 1000, "Not all returns were traced"
    
    # Add many events
    start_time = time.time()
     "trace_function" in str(_[2])
    # Add events in a tight loop
    for i in range(10000):/ 2000  # 1000 calls + 1000 returns
        collector.add_output(f"Output line {i}", "stdout")
        nction call: {avg_time*1000:.6f} ms")
    mid_time = time.time()
    ably small (adjust threshold as needed)
    # Measure time to retrieve eventsassert avg_time < 0.001, f"trace_function too slow: {avg_time*1000:.6f} ms per call"
    received_count = 0
    get_start = time.time()
    
    # Create multiple consumers_throughput():
    async def consumer(consumer_id, count):"""
        nonlocal received_count
        for _ in range(count):
            event_type, event = await collector.get_event()
            received_count += 1collector = DataCollector()
            if received_count % 1000 == 0:
                print(f"Consumer {consumer_id} received {received_count} events") events
    time()
    # Start multiple consumers
    tasks = []# Add events in a tight loop
    consumer_count = 4
    events_per_consumer = 2500  # Total 10000 events
    
    for i in range(consumer_count):mid_time = time.time()
        task = asyncio.create_task(consumer(i, events_per_consumer))
        tasks.append(task)vents
    received_count = 0
    # Wait for all consumers to finish()
    await asyncio.gather(*tasks)
    
    get_end = time.time()count):
    
    # Calculate and print metrics    for _ in range(count):
    add_time = mid_time - start_time await collector.get_event()
    get_time = get_end - get_start
            if received_count % 1000 == 0:
    add_rate = 10000 / add_timeumer_id} received {received_count} events")
    get_rate = 10000 / get_time
    
    print(f"\nCollector performance:")tasks = []
    print(f"  Add 10000 events: {add_time:.4f} seconds ({add_rate:.2f} events/sec)")
    print(f"  Get 10000 events: {get_time:.4f} seconds ({get_rate:.2f} events/sec)")
    
    # Verify event throughput is reasonable
    assert add_rate > 1000, f"Event add rate too low: {add_rate:.2f} events/sec"        task = asyncio.create_task(consumer(i, events_per_consumer))



    assert received_count == 10000, f"Not all events were received: {received_count}/10000"    assert get_rate > 100, f"Event get rate too low: {get_rate:.2f} events/sec"        tasks.append(task)

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
    assert (
        received_count == 10000
    ), f"Not all events were received: {received_count}/10000"
