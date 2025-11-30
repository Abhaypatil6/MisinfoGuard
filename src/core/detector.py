import os
import google.generativeai as genai
from typing import List, Optional
from datetime import datetime
import json
import time
from dotenv import load_dotenv

from src.core.models import ClaimAnalysis, Evidence
from src.tools.search import SearchTool

load_dotenv()

class MisinfoDetector:
    """
    Unified agent that analyzes claims for misinformation in a single pass.
    Replaces the previous 3-agent system (Monitor, Verifier, Explainer).
    """
    
    SYSTEM_PROMPT = """You are an expert misinformation analyst and fact-checker.

TASK: Analyze claims about a given topic and identify potential misinformation.

PROCESS:
1. Identify 1-3 key claims related to the topic
2. For each claim, determine if it's MISINFORMATION, VERIFIED, or UNCERTAIN
3. Provide confidence score (0.0-1.0) and clear explanation
4. Reference credible evidence

VERDICT GUIDELINES:
- MISINFORMATION: Demonstrably false, contradicts credible sources (confidence ≥ 0.8)
- VERIFIED: Supported by credible evidence from reliable sources
- UNCERTAIN: Insufficient evidence or conflicting information (confidence < 0.7)

IMPORTANT: Return ONLY valid JSON (no markdown, no code blocks) in this exact format:
[
  {
    "claim": "Specific claim statement",
    "verdict": "MISINFORMATION" | "VERIFIED" | "UNCERTAIN",
    "confidence": 0.85,
    "explanation": "Clear explanation with evidence...",
    "key_evidence": ["Fact 1 from source X", "Fact 2 from source Y"]
  }
]

Focus on claims that are actually misinformation. Return empty array [] if no misinformation found."""

    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.search_tool = SearchTool()
    
    def analyze(self, topic: str) -> List[ClaimAnalysis]:
        """
        Analyzes a topic for misinformation claims.
        
        Args:
            topic: The topic to analyze
            
        Returns:
            List of ClaimAnalysis objects
        """
        print(f"🔍 Analyzing topic: {topic}")
        
        # 1. Gather evidence from web search
        evidence_list = self._gather_evidence(topic)
        
        if not evidence_list:
            print("⚠️ No evidence found, returning empty results")
            return []
        
        # 2. Analyze with unified AI prompt
        claims = self._analyze_with_ai(topic, evidence_list)
        
        print(f"✅ Analysis complete. Found {len(claims)} claims.")
        return claims
    
    def _gather_evidence(self, topic: str) -> List[Evidence]:
        """Gather evidence from multiple search queries."""
        print(f"🔎 Gathering evidence...")
        
        # Search strategies
        queries = [
            topic,
            f"{topic} fact check",
            f"{topic} misinformation debunk"
        ]
        
        all_results = []
        seen_urls = set()
        
        for query in queries:
            results = self.search_tool.search(query, max_results=3)
            
            for result in results:
                url = result.get('href')
                if url and url not in seen_urls:
                    evidence = Evidence(
                        title=result.get('title', 'Unknown'),
                        url=url,
                        snippet=result.get('body', '')[:200]
                    )
                    all_results.append(evidence)
                    seen_urls.add(url)
        
        print(f"📚 Gathered {len(all_results)} evidence sources")
        return all_results[:8]  # Limit to top 8 sources
    
    def _analyze_with_ai(self, topic: str, evidence: List[Evidence]) -> List[ClaimAnalysis]:
        """Analyze topic with AI using gathered evidence."""
        
        # Prepare evidence summary for AI
        evidence_summary = "\n".join([
            f"- {e.title}: {e.snippet} (Source: {e.url})"
            for e in evidence
        ])
        
        user_prompt = f"""
Topic: "{topic}"

Available Evidence:
{evidence_summary}

Analyze this topic and identify any potential misinformation claims.
Return JSON array as specified in system prompt.
"""
        
        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🤖 Calling AI (attempt {attempt + 1}/{max_retries})...")
                
                response = self.model.generate_content([
                    {"role": "user", "parts": [self.SYSTEM_PROMPT]},
                    {"role": "model", "parts": ["Understood. I'll analyze topics for misinformation and return JSON."]},
                    {"role": "user", "parts": [user_prompt]}
                ])
                
                result_text = response.text.strip()
                print(f"📝 Raw AI response: {result_text[:200]}...")
                
                # Clean up response
                result_text = result_text.replace("```json", "").replace("```", "").strip()
                
                # Parse JSON
                claims_data = json.loads(result_text)
                
                if not isinstance(claims_data, list):
                    claims_data = [claims_data]
                
                # Convert to ClaimAnalysis objects
                claims = []
                for claim_dict in claims_data[:3]:  # Max 3 claims
                    # Only include misinformation
                    if claim_dict.get('verdict') == 'MISINFORMATION':
                        claim = ClaimAnalysis(
                            claim=claim_dict.get('claim', ''),
                            verdict=claim_dict.get('verdict', 'UNCERTAIN'),
                            confidence=float(claim_dict.get('confidence', 0.5)),
                            explanation=claim_dict.get('explanation', ''),
                            evidence=evidence[:3],  # Top 3 evidence sources
                            analyzed_at=datetime.now(),
                            cached=False
                        )
                        claims.append(claim)
                
                return claims
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return []
                
            except Exception as e:
                print(f"❌ Error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return []
        
        return []
