import os
import asyncio
import google.generativeai as genai
from typing import List, Optional, Dict
from datetime import datetime
import json
from dotenv import load_dotenv

from src.core.models import ClaimAnalysis, Evidence
from src.memory.memory_bank import MemoryBank
from src.observability.logger import get_logger
from src.observability.tracer import trace_operation

load_dotenv()

logger = get_logger(__name__)

class BaseAgent:
    """Base class for all agents with common functionality"""
    
    def __init__(self, name: str):
        self.name = name
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        logger.info(f"✅ Initialized {name}")
    
    async def execute(self, **kwargs):
        """Override in subclass"""
        raise NotImplementedError

class EvidenceGathererAgent(BaseAgent):
    """Specialized agent for gathering evidence from web sources"""
    
    def __init__(self):
        super().__init__("EvidenceGatherer")
        from src.tools.search import SearchTool
        self.search_tool = SearchTool()
    
    @trace_operation("evidence_gathering")
    async def gather(self, topic: str) -> List[Evidence]:
        """Gather evidence from multiple sources in parallel"""
        logger.info(f"🔎 Gathering evidence for: {topic}")
        
        # Parallel search queries
        queries = [
            topic,
            f"{topic} fact check",
            f"{topic} misinformation analysis"
        ]
        
        # Execute searches in parallel
        tasks = [
            asyncio.to_thread(self.search_tool.search, query, max_results=3)
            for query in queries
        ]
        
        results_list = await asyncio.gather(*tasks)
        
        # Deduplicate and convert to Evidence
        all_evidence = []
        seen_urls = set()
        
        for results in results_list:
            for result in results:
                url = result.get('href')
                if url and url not in seen_urls:
                    evidence = Evidence(
                        title=result.get('title', 'Unknown'),
                        url=url,
                        snippet=result.get('body', '')[:200]
                    )
                    all_evidence.append(evidence)
                    seen_urls.add(url)
        
        logger.info(f"✅ Gathered {len(all_evidence)} evidence sources")
        return all_evidence[:8]  # Top 8 sources

class FactCheckerAgent(BaseAgent):
    """Specialized agent for fact-checking claims"""
    
    def __init__(self):
        super().__init__("FactChecker")
    
    @trace_operation("fact_checking")
    async def check(self, topic: str, evidence: List[Evidence]) -> List[Dict]:
        """Analyze topic and identify misinformation claims"""
        logger.info(f"🔍 Fact-checking topic: {topic}")
        
        evidence_summary = "\n".join([
            f"- {e.title}: {e.snippet}"
            for e in evidence
        ])
        
        prompt = f"""Analyze this topic for misinformation:

Topic: "{topic}"

Evidence:
{evidence_summary}

Identify 1-3 specific claims that are MISINFORMATION only.
Return JSON array:
[
  {{
    "claim": "exact claim text",
    "verdict": "MISINFORMATION",
    "confidence": 0.85,
    "reasoning": "why this is false"
  }}
]

Return [] if no misinformation found."""
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            result_text = response.text.strip()
            result_text = result_text.replace("```json", "").replace("```", "").strip()
            
            claims = json.loads(result_text)
            logger.info(f"✅ Found {len(claims)} misinformation claims")
            return claims if isinstance(claims, list) else [claims]
            
        except Exception as e:
            logger.error(f"❌ Fact-checking error: {e}")
            return []

class CredibilityAssessorAgent(BaseAgent):
    """Assesses credibility of evidence sources"""
    
    def __init__(self):
        super().__init__("CredibilityAssessor")
    
    @trace_operation("credibility_assessment")
    async def assess(self, evidence: List[Evidence]) -> Dict[str, str]:
        """Assess credibility of evidence sources"""
        logger.info(f"📊 Assessing credibility of {len(evidence)} sources")
        
        # Simple heuristic-based assessment
        credibility_map = {}
        
        for ev in evidence:
            domain = ev.url.split('/')[2] if '/' in ev.url else ev.url
            
            # High credibility domains
            if any(trusted in domain.lower() for trusted in 
                   ['edu', 'gov', 'reuters', 'apnews', 'bbc', 'factcheck']):
                credibility = "high"
            # Low credibility domains
            elif any(untrusted in domain.lower() for untrusted in 
                     ['blog', 'wordpress', 'medium']):
                credibility = "low"
            else:
                credibility = "medium"
            
            credibility_map[ev.url] = credibility
        
        logger.info(f"✅ Credibility assessment complete")
        return credibility_map

class ExplainerAgent(BaseAgent):
    """Generates user-friendly explanations"""
    
    def __init__(self):
        super().__init__("Explainer")
    
    @trace_operation("explanation_generation")
    async def explain(self, claim: str, reasoning: str, evidence: List[Evidence]) -> str:
        """Generate clear explanation"""
        logger.info(f"📝 Generating explanation")
        
        evidence_text = "\n".join([
            f"- [{e.title}]({e.url})"
            for e in evidence[:3]
        ])
        
        prompt = f"""Create a clear, concise explanation (2-3 paragraphs):

Claim: "{claim}"
Why it's false: {reasoning}

Sources:
{evidence_text}

Write in friendly, authoritative tone with Markdown formatting."""
        
        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            return response.text
        except Exception as e:
            logger.error(f"❌ Explanation error: {e}")
            return reasoning

class CoordinatorAgent(BaseAgent):
    """Main coordinator orchestrating all specialized agents"""
    
    def __init__(self):
        super().__init__("Coordinator")
        self.evidence_agent = EvidenceGathererAgent()
        self.fact_agent = FactCheckerAgent()
        self.credibility_agent = CredibilityAssessorAgent()
        self.explainer_agent = ExplainerAgent()
        self.memory_bank = MemoryBank()
    
    @trace_operation("coordination")
    async def analyze(self, topic: str) -> List[ClaimAnalysis]:
        """
        Orchestrate multi-agent analysis workflow
        
        1. Check memory for cached results
        2. Execute parallel agents (evidence + credibility)
        3. Fact-check with gathered evidence
        4. Generate explanations
        5. Store in memory
        """
        logger.info(f"🎯 Coordinating analysis for: {topic}")
        
        # Step 1: Check memory
        cached_result = self.memory_bank.get(topic)
        if cached_result:
            logger.info(f"⚡ Retrieved from memory bank")
            return cached_result
        
        # Step 2: Parallel evidence gathering and initial setup
        logger.info(f"🚀 Launching parallel agents")
        evidence, _ = await asyncio.gather(
            self.evidence_agent.gather(topic),
            asyncio.sleep(0)  # Placeholder for other parallel ops
        )
        
        if not evidence:
            logger.warning(f"⚠️ No evidence found")
            return []
        
        # Step 3: Assess credibility in parallel with fact-checking
        credibility_map, fact_check_results = await asyncio.gather(
            self.credibility_agent.assess(evidence),
            self.fact_agent.check(topic, evidence)
        )
        
        # Step 4: Generate explanations and create ClaimAnalysis objects
        claims = []
        for fact in fact_check_results[:3]:  # Max 3 claims
            # Filter evidence by credibility
            high_cred_evidence = [
                e for e in evidence
                if credibility_map.get(e.url) == "high"
            ]
            
            # Use high credibility evidence first, fallback to all
            selected_evidence = (high_cred_evidence or evidence)[:3]
            
            # Generate explanation
            explanation = await self.explainer_agent.explain(
                fact['claim'],
                fact.get('reasoning', ''),
                selected_evidence
            )
            
            claim = ClaimAnalysis(
                claim=fact['claim'],
                verdict="MISINFORMATION",
                confidence=float(fact.get('confidence', 0.8)),
                explanation=explanation,
                evidence=selected_evidence,
                analyzed_at=datetime.now(),
                cached=False
            )
            claims.append(claim)
        
        # Step 5: Store in memory
        if claims:
            self.memory_bank.store(topic, claims)
            logger.info(f"💾 Stored {len(claims)} claims in memory")
        
        logger.info(f"✅ Coordination complete: {len(claims)} claims")
        return claims
