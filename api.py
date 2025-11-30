from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid
from datetime import datetime

from src.core.models import AnalysisRequest, AnalysisResponse
from src.agents.coordinator import CoordinatorAgent
from src.observability.logger import get_logger, set_trace_id_for_all
from src.observability.tracer import get_tracer
from src.observability.metrics import get_metrics

logger = get_logger(__name__)
metrics = get_metrics()

app = FastAPI(
    title="MisinfoGuard v2 - Multi-Agent System",
    version="2.0.0",
    description="Advanced misinformation detection with multi-agent architecture"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize coordinator agent
coordinator = CoordinatorAgent()

@app.middleware("http")
async def add_trace_id(request, call_next):
    """Add trace ID to all requests"""
    trace_id = str(uuid.uuid4())[:8]
    set_trace_id_for_all(trace_id)
    get_tracer().start_trace(trace_id)
    
    response = await call_next(request)
    response.headers["X-Trace-ID"] = trace_id
    return response

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_topic(request: AnalysisRequest):
    """
    Multi-agent analysis endpoint
    
    Demonstrates:
    - Multi-agent coordination
    - Parallel agent execution
    - Memory bank usage
    - Distributed tracing
    - Metrics collection
    """
    start_time = time.time()
    topic = request.topic.strip()
    
    logger.info(f"📥 Analysis request", topic=topic)
    metrics.counter("analysis_requests_total").inc()
    
    try:
        # Execute multi-agent analysis
        claims = await coordinator.analyze(topic)
        
        processing_time = time.time() - start_time
        
        # Record metrics
        metrics.histogram("analysis_duration_seconds").observe(processing_time)
        metrics.counter("claims_analyzed_total").inc(len(claims))
        
        # Check if from cache
        cached = any(claim.cached for claim in claims) if claims else False
        if cached:
            metrics.counter("cache_hits_total").inc()
        
        logger.info(
            f"✅ Analysis complete",
            topic=topic,
            claims_count=len(claims),
            duration_ms=round(processing_time * 1000, 2),
            cached=cached
        )
        
        return AnalysisResponse(
            claims=claims,
            topic=topic,
            analyzed_at=datetime.now(),
            processing_time=processing_time,
            cached=cached
        )
        
    except Exception as e:
        metrics.counter("analysis_errors_total").inc()
        logger.error(f"❌ Analysis failed", topic=topic, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """API info"""
    return {
        "name": "MisinfoGuard v2",
        "version": "2.0.0",
        "architecture": "Multi-Agent System",
        "features": [
            "Parallel agent execution",
            "Memory bank (long-term storage)",
            "Distributed tracing",
            "Metrics collection",
            "Credibility assessment"
        ],
        "endpoints": {
            "analyze": "POST /analyze - Main analysis endpoint",
            "health": "GET /health - Health check",
            "metrics": "GET /metrics - Performance metrics",
            "memory": "GET /memory/stats - Memory bank statistics"
        }
    }

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "agents": {
            "coordinator": "active",
            "evidence_gatherer": "active",
            "fact_checker": "active",
            "credibility_assessor": "active",
            "explainer": "active"
        }
    }

@app.get("/metrics")
async def get_metrics_endpoint():
    """Get performance metrics"""
    return metrics.get_metrics()

@app.get("/memory/stats")
async def get_memory_stats():
    """Get memory bank statistics"""
    return coordinator.memory_bank.get_stats()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
