import React, { useState, useCallback } from 'react';
import './App.css';
import ClaimCard from './components/ClaimCard';

function App() {
  const [topic, setTopic] = useState('');
  const [claims, setClaims] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [metadata, setMetadata] = useState(null);

  const handleScan = useCallback(async () => {
    if (!topic || !topic.trim()) {
      setError('Please enter a topic to scan');
      return;
    }

    if (loading) return;

    setLoading(true);
    setError(null);
    setClaims([]);
    setMetadata(null);

    try {
      const response = await fetch('http://localhost:8000/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: topic.trim() }),
      });

      if (!response.ok) {
        throw new Error(`Failed to analyze topic (${response.status})`);
      }

      const data = await response.json();
      const traceId = response.headers.get('X-Trace-ID');

      if (data.claims && data.claims.length > 0) {
        setClaims(data.claims);
        setMetadata({
          cached: data.cached,
          processing_time: data.processing_time,
          trace_id: traceId
        });
      } else {
        setError('No misinformation found for this topic ✅');
      }
    } catch (err) {
      setError(err.message || 'Failed to analyze topic. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [topic, loading]);

  return (
    <div className="container">
      <header className="header">
        <h1 className="title">MisinfoGuard v2</h1>
        <p className="subtitle">Multi-Agent Misinformation Detection</p>
      </header>

      <div className="search-box">
        <input
          type="text"
          placeholder="Enter a topic (e.g., Climate Change, Vaccines)..."
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !loading && handleScan()}
          disabled={loading}
        />
        <button onClick={handleScan} disabled={loading || !topic.trim()}>
          {loading ? '🔍 Analyzing...' : 'Analyze Topic'}
        </button>
      </div>

      {metadata && (
        <div className="metadata-card">
          {metadata.cached && <span className="cache-badge">⚡ From Cache</span>}
          <span className="timing">⏱️ {(metadata.processing_time * 1000).toFixed(0)}ms</span>
          {metadata.trace_id && <span className="trace-id">🔗 {metadata.trace_id}</span>}
        </div>
      )}

      {error && <div className="card error-card">{error}</div>}

      <div className="claims-grid">
        {claims.map((claim, index) => (
          <ClaimCard key={`${claim.claim}-${index}`} claim={claim} />
        ))}
      </div>
    </div>
  );
}

export default App;
