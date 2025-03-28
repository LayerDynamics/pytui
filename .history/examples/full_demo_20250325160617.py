"""Full demonstration of pytui capabilities."""

import asyncio
import random
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class MetricPoint:
    """Data structure for metrics."""
    name: str
    value: float
    timestamp: datetime

class SystemMonitor:
    """Complex system monitoring demonstration."""
    
    def __init__(self):
        """Initialize the monitor."""
        self.metrics: List[MetricPoint] = []
        self._running = False
        self._callbacks: List[callable] = []

    def add_callback(self, callback: callable) -> None:
        """Add a metric callback."""
        self._callbacks.append(callback)

    async def start_monitoring(self) -> None:
        """Start monitoring metrics."""
        self._running = True
        while self._running:
            await self._collect_metrics()
            await self._process_metrics()
            await asyncio.sleep(0.5)

    async def _collect_metrics(self) -> None:
        """Collect system metrics."""
        metric = MetricPoint(
            name="cpu_usage",
            value=random.uniform(0, 100),
            timestamp=datetime.now()
        )
        self.metrics.append(metric)
        for callback in self._callbacks:
            await callback(metric)

    async def _process_metrics(self) -> Dict[str, float]:
        """Process collected metrics."""
        if not self.metrics:
            return {}

        latest_metrics = self.metrics[-10:]
        avg_value = sum(m.value for m in latest_metrics) / len(latest_metrics)
        return {"average": avg_value}

    def stop(self) -> None:
        """Stop monitoring."""
        self._running = False

class DataProcessor:
    """Complex data processing demonstration."""

    def __init__(self):
        """Initialize processor."""
        self.data: List[Dict[str, Any]] = []
        self.processed: List[Dict[str, Any]] = []
        self._monitor = SystemMonitor()

    async def initialize(self) -> None:
        """Initialize the processor."""
        await self._setup_monitoring()
        await self._prepare_data()

    async def _setup_monitoring(self) -> None:
        """Set up system monitoring."""
        self._monitor.add_callback(self._metric_callback)
        asyncio.create_task(self._monitor.start_monitoring())

    async def _metric_callback(self, metric: MetricPoint) -> None:
        """Handle new metrics."""
        print(f"New metric: {metric.name} = {metric.value:.2f}")

    async def _prepare_data(self) -> None:
        """Prepare initial data."""
        for i in range(5):
            self.data.append({
                "id": i,
                "value": random.random(),
                "timestamp": datetime.now()
            })

    async def process_all(self) -> List[Dict[str, Any]]:
        """Process all data items."""
        results = []
        for item in self.data:
            try:
                result = await self._process_item(item)
                results.append(result)
            except Exception as e:
                print(f"Error processing item {item['id']}: {e}")
        return results

    async def _process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single data item."""
        await asyncio.sleep(0.1)  # Simulate processing
        return {
            "id": item["id"],
            "processed_value": item["value"] * 2,
            "processing_time": datetime.now()
        }

class AsyncWorker:
    """Asynchronous worker demonstration."""

    def __init__(self, name: str):
        """Initialize worker."""
        self.name = name
        self.tasks_completed = 0
        self._running = False

    async def start(self) -> None:
        """Start the worker."""
        self._running = True
        while self._running:
            await self._process_task()
            self.tasks_completed += 1

    async def _process_task(self) -> None:
        """Process a single task."""
        await asyncio.sleep(random.uniform(0.1, 0.5))
        print(f"Worker {self.name} completed task {self.tasks_completed + 1}")

    def stop(self) -> None:
        """Stop the worker."""
        self._running = False

async def main():
    """Main demonstration function."""
    # Initialize components
    processor = DataProcessor()
    workers = [AsyncWorker(f"Worker-{i}") for i in range(3)]

    # Start initialization
    print("Initializing system...")
    await processor.initialize()

    # Start workers
    worker_tasks = [asyncio.create_task(worker.start()) for worker in workers]

    # Process data
    print("\nProcessing data...")
    results = await processor.process_all()
    print(f"Processed {len(results)} items")

    # Run for a while to demonstrate monitoring
    print("\nRunning system...")
    await asyncio.sleep(3)

    # Cleanup
    print("\nShutting down...")
    for worker in workers:
        worker.stop()
    processor._monitor.stop()

    # Wait for workers to finish
    await asyncio.gather(*worker_tasks, return_exceptions=True)
    print("Demonstration complete!")

if __name__ == "__main__":
    asyncio.run(main())
