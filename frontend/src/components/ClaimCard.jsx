import React, { memo } from 'react';
import ReactMarkdown from 'react-markdown';

const ClaimCard = memo(({ claim }) => {
    // Claim is now a complete ClaimAnalysis object from the API
    const {
        claim: claimText,
        verdict,
        confidence,
        explanation,
        evidence,
        cached
    } = claim;

    return (
        <div className="card">
            <h3 style={{ marginTop: 0 }}>{claimText}</h3>

            <div className="result">
                <div className={`status-banner status-${verdict?.toLowerCase() || 'misinformation'}`}>
                    {verdict === 'MISINFORMATION' && '⚠️ '}
                    {verdict === 'VERIFIED' && '✅ '}
                    {verdict || 'MISINFORMATION'}
                </div>

                {/* Confidence Score */}
                <div className="confidence-bar">
                    <div className="confidence-label">
                        Confidence: {(confidence * 100).toFixed(0)}%
                    </div>
                    <div className="confidence-indicator">
                        <div
                            className="confidence-fill"
                            style={{ width: `${confidence * 100}%` }}
                        ></div>
                    </div>
                </div>

                <div className="explanation">
                    <ReactMarkdown>{explanation}</ReactMarkdown>
                </div>

                {evidence && Array.isArray(evidence) && evidence.length > 0 && (
                    <div className="evidence-section">
                        <h4>Evidence & Sources (Top {Math.min(evidence.length, 3)}):</h4>
                        <ul className="evidence-list">
                            {evidence.slice(0, 3).map((item, idx) => (
                                <li key={idx}>
                                    <a href={item?.url || '#'} target="_blank" rel="noopener noreferrer">
                                        {item?.title || 'Source ' + (idx + 1)}
                                    </a>
                                    {item?.snippet && (
                                        <p className="evidence-snippet">{item.snippet}</p>
                                    )}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {cached && (
                    <div className="cache-indicator">
                        ⚡ Retrieved from memory bank
                    </div>
                )}
            </div>
        </div>
    );
});

ClaimCard.displayName = 'ClaimCard';

export default ClaimCard;
