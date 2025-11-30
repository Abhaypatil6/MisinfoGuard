from collections import defaultdict
from typing import Dict
import time

class MetricsCollector:
    """
    Simple metrics collector for monitoring
    Demonstrates: Observability - Metrics concept
    """
    
    def __init__(self):
        self.counters: Dict[str, int] = defaultdict(int)
        self.histograms: Dict[str, list] = defaultdict(list)
        self.gauges: Dict[str, float] = {}
    
    def counter(self, name: str) -> 'Counter':
        """Get or create a counter metric"""
        return Counter(name, self)
    
    def histogram(self, name: str) -> 'Histogram':
        """Get or create a histogram metric"""
        return Histogram(name, self)
    
    def gauge(self, name: str) -> 'Gauge':
        """Get or create a gauge metric"""
        return Gauge(name, self)
    
    def get_metrics(self) -> Dict:
        """Get all metrics as dict"""
        return {
            "counters": dict(self.counters),
            "histograms": {
                name: {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0
                }
                for name, values in self.histograms.items()
            },
            "gauges": dict(self.gauges)
        }

class Counter:
    """Counter metric - monotonically increasing value"""
    
    def __init__(self, name: str, collector: MetricsCollector):
        self.name = name
        self.collector = collector
    
    def inc(self, value: int = 1):
        """Increment counter"""
        self.collector.counters[self.name] += value
    
    def get(self) -> int:
        """Get current value"""
        return self.collector.counters[self.name]

class Histogram:
    """Histogram metric - track distribution of values"""
    
    def __init__(self, name: str, collector: MetricsCollector):
        self.name = name
        self.collector = collector
    
    def observe(self, value: float):
        """Record observation"""
        self.collector.histograms[self.name].append(value)
    
    def get_stats(self) -> Dict:
        """Get statistics"""
        values = self.collector.histograms[self.name]
        if not values:
            return {"count": 0, "sum": 0, "avg": 0}
        
        return {
            "count": len(values),
            "sum": sum(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values)
        }

class Gauge:
    """Gauge metric - can go up or down"""
    
    def __init__(self, name: str, collector: MetricsCollector):
        self.name = name
        self.collector = collector
    
    def set(self, value: float):
        """Set gauge value"""
        self.collector.gauges[self.name] = value
    
    def get(self) -> float:
        """Get current value"""
        return self.collector.gauges.get(self.name, 0.0)

# Global metrics collector
_metrics = MetricsCollector()

def get_metrics() -> MetricsCollector:
    """Get the global metrics collector"""
    return _metrics
