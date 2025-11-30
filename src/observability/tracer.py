import time
import uuid
from functools import wraps
from typing import Callable, Any
from contextlib import contextmanager
from src.observability.logger import get_logger

logger = get_logger("tracer")

class Span:
    """
    Simple span implementation for distributed tracing
    Demonstrates: Observability - Tracing concept
    """
    
    def __init__(self, operation_name: str, parent_id: str = None):
        self.span_id = str(uuid.uuid4())[:8]
        self.parent_id = parent_id
        self.operation_name = operation_name
        self.start_time = time.time()
        self.end_time = None
        self.duration = None
        self.tags = {}
    
    def set_tag(self, key: str, value: Any):
        """Add tag to span"""
        self.tags[key] = value
    
    def finish(self):
        """Complete the span"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        
        logger.info(
            f"Span completed: {self.operation_name}",
            span_id=self.span_id,
            parent_span_id=self.parent_id,
            duration_ms=round(self.duration * 1000, 2),
            **self.tags
        )

class Tracer:
    """Simple tracer for operation tracking"""
    
    def __init__(self):
        self.active_span = None
        self.trace_id = None
    
    def start_trace(self, trace_id: str = None):
        """Start a new trace"""
        self.trace_id = trace_id or str(uuid.uuid4())
        return self.trace_id
    
    def start_span(self, operation_name: str) -> Span:
        """Start a new span"""
        parent_id = self.active_span.span_id if self.active_span else None
        span = Span(operation_name, parent_id)
        return span

# Global tracer instance
_tracer = Tracer()

def get_tracer() -> Tracer:
    """Get the global tracer instance"""
    return _tracer

def trace_operation(operation_name: str):
    """
    Decorator to trace function execution
    Usage: @trace_operation("my_operation")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_tracer()
            span = tracer.start_span(operation_name)
            
            try:
                result = await func(*args, **kwargs)
                span.set_tag("status", "success")
                return result
            except Exception as e:
                span.set_tag("status", "error")
                span.set_tag("error", str(e))
                raise
            finally:
                span.finish()
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_tracer()
            span = tracer.start_span(operation_name)
            
            try:
                result = func(*args, **kwargs)
                span.set_tag("status", "success")
                return result
            except Exception as e:
                span.set_tag("status", "error")
                span.set_tag("error", str(e))
                raise
            finally:
                span.finish()
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

@contextmanager
def trace_context(operation_name: str):
    """
    Context manager for tracing code blocks
    Usage:
        with trace_context("my_operation"):
            # code here
    """
    tracer = get_tracer()
    span = tracer.start_span(operation_name)
    
    try:
        yield span
        span.set_tag("status", "success")
    except Exception as e:
        span.set_tag("status", "error")
        span.set_tag("error", str(e))
        raise
    finally:
        span.finish()
