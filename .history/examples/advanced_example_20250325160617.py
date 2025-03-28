"""Advanced example demonstrating complex features and async operations."""

import asyncio
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DataPoint:
    """Example data structure for processing."""
    timestamp: datetime
    value: float
    category: str
    processed: bool = False

class DataProcessor:
    """Complex class demonstrating various pytui features."""

    def __init__(self):
        """Initialize processor with empty data."""
        self.data: List[DataPoint] = []
        self.results: Dict[str, List[float]] = {}
        self._processing = False

    async def generate_data(self, num_points: int) -> None:
        """Generate sample data asynchronously."""
        categories = ['A', 'B', 'C']
        for _ in range(num_points):
            await asyncio.sleep(0.05)  # Simulate I/O
            point = DataPoint(
                timestamp=datetime.now(),
                value=random.uniform(0, 100),
                category=random.choice(categories)
            )
            self.data.append(point)
            await self._notify_data_added(point)

    async def _notify_data_added(self, point: DataPoint) -> None:
        """Internal notification method."""
        print(f"New data point added: {point.category} = {point.value:.2f}")

    async def process_data(self) -> Dict[str, Any]:
        """Process data with complex operations."""
        self._processing = True
        try:
            results = await self._analyze_data()
            summary = await self._generate_summary(results)
            return {
                "results": results,
                "summary": summary,
                "timestamp": datetime.now().isoformat()
            }
        finally:
            self._processing = False

    async def _analyze_data(self) -> Dict[str, List[float]]:
        """Internal analysis method."""
        categories: Dict[str, List[float]] = {}
        
        for point in self.data:
            if not point.processed:
                await asyncio.sleep(0.02)  # Simulate processing time
                if point.category not in categories:
                    categories[point.category] = []
                categories[point.category].append(point.value)
                point.processed = True

        return categories

    async def _generate_summary(self, results: Dict[str, List[float]]) -> Dict[str, Any]:
        """Generate statistical summary."""
        summary = {}
        for category, values in results.items():
            if values:
                summary[category] = {
                    "count": len(values),
                    "average": sum(values) / len(values),
                    "max": max(values),
                    "min": min(values)
                }
        return summary

class AsyncTaskManager:
    """Manager for async tasks demonstration."""

    def __init__(self):
        """Initialize task manager."""
        self.tasks: List[asyncio.Task] = []
        self.results: List[Any] = []

    async def add_task(self, coro) -> None:
        """Add a new task to manage."""
        task = asyncio.create_task(self._wrap_task(coro))
        self.tasks.append(task)

    async def _wrap_task(self, coro) -> None:
        """Wrap and monitor task execution."""
        try:
            result = await coro
            self.results.append(result)
        except Exception as e:
            print(f"Task error: {e}")
            raise

    async def wait_all(self) -> List[Any]:
        """Wait for all tasks to complete."""
        if self.tasks:
            await asyncio.gather(*self.tasks)
        return self.results

async def main():
    """Main async function demonstrating advanced features."""
    # Initialize processor and task manager
    processor = DataProcessor()
    manager = AsyncTaskManager()

    # Add tasks for data generation and processing
    await manager.add_task(processor.generate_data(5))
    await asyncio.sleep(0.1)  # Allow some data to generate
    await manager.add_task(processor.process_data())

    # Wait for all tasks and get results
    results = await manager.wait_all()

    # Demonstrate error handling
    try:
        await processor.process_data()
    except Exception as e:
        print(f"Error during processing: {e}")

    # Print final results
    if results:
        print("\nProcessing Results:")
        for result in results:
            if isinstance(result, dict) and "summary" in result:
                print("\nCategory Summaries:")
                for category, stats in result["summary"].items():
                    print(f"\nCategory {category}:")
                    for key, value in stats.items():
                        print(f"  {key}: {value}")

if __name__ == "__main__":
    asyncio.run(main())
