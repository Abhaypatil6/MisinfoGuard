# MisinfoGuard v2.0 🛡️

AI-powered misinformation detection system using **multi-agent architecture** with distributed tracing and memory management.

## 🌟 Features

- **Multi-Agent System** - Coordinator orchestrates 4 specialized agents
- **Parallel Execution** - Evidence gathering & analysis run concurrently
- **Memory Bank** - SQLite-based caching for instant repeated queries
- **Confidence Scores** - Visual indicators of analysis certainty
- **Full Observability** - Structured logging, distributed tracing, and metrics
- **Credibility Assessment** - Automated source reliability rating

## 🏗️ Architecture

```
CoordinatorAgent
├── EvidenceGathererAgent (parallel web searches)
├── FactCheckerAgent (claim verification)
├── CredibilityAssessorAgent (source rating)
└── ExplainerAgent (user-friendly output)
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google Gemini API key

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GOOGLE_API_KEY=your_api_key_here" > .env

# Start backend
uvicorn api:app --reload
```

Backend runs at http://localhost:8000

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173

## 📡 API Endpoints

### Main Analysis
```http
POST /analyze
{
  "topic": "Climate Change"
}
```

### Monitoring
- `GET /health` - Agent health status
- `GET /metrics` - Performance metrics
- `GET /memory/stats` - Cache statistics

## 🎓 Course Concepts Demonstrated

This project demonstrates 5+ advanced agentic AI concepts:

1. ✅ **Multi-Agent System** - Coordinator + specialized agents
2. ✅ **Parallel Agents** - Concurrent execution with asyncio
3. ✅ **Memory Bank** - Long-term persistence with SQLite
4. ✅ **Custom Tools** - Enhanced search with parallel queries
5. ✅ **Observability** - Logging, tracing, and metrics

## 📁 Project Structure

```
Capstone/
├── api.py                      # FastAPI application
├── src/
│   ├── agents/
│   │   └── coordinator.py      # Multi-agent orchestration
│   ├── memory/
│   │   └── memory_bank.py      # SQLite caching
│   ├── observability/
│   │   ├── logger.py           # Structured logging
│   │   ├── tracer.py           # Distributed tracing
│   │   └── metrics.py          # Metrics collection
│   ├── core/
│   │   └── models.py           # Pydantic models
│   └── tools/
│       └── search.py           # Search tool
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── components/
│           └── ClaimCard.jsx
└── memory_bank.db              # SQLite database
```

## 🧪 Testing

1. **Fresh Analysis**: Search for "Climate Change"
2. **Cache Test**: Search same topic again (< 100ms)
3. **Metrics**: Visit http://localhost:8000/metrics
4. **Memory Stats**: Visit http://localhost:8000/memory/stats

## 📊 Performance

| Metric | v1.0 | v2.0 | Improvement |
|--------|------|------|-------------|
| API calls/claim | 3 | 1 | 66% ↓ |
| Parallel ops | 0 | 2-3 | 2x faster |
| Cached response | N/A | <100ms | Instant |

## 🛠️ Technologies

**Backend:**
- FastAPI
- Google Gemini AI
- SQLite
- DuckDuckGo Search

**Frontend:**
- React
- Vite
- ReactMarkdown

## 📝 License

MIT

## 🤝 Contributing

This is a course submission project demonstrating multi-agent systems and observability patterns.
