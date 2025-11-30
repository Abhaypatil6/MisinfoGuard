import json
import hashlib
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
from src.core.models import ClaimAnalysis

class ClaimCache:
    """Simple file-based cache for claim analyses"""
    
    def __init__(self, cache_dir: str = ".cache", ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
    
    def _get_cache_key(self, topic: str) -> str:
        """Generate cache key from topic"""
        return hashlib.md5(topic.lower().strip().encode()).hexdigest()
    
    def get(self, topic: str) -> Optional[List[ClaimAnalysis]]:
        """Retrieve cached analysis if available and not expired"""
        cache_key = self._get_cache_key(topic)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if expired
            cached_at = datetime.fromisoformat(data['cached_at'])
            if datetime.now() - cached_at > self.ttl:
                print(f"🗑️ Cache expired for topic: {topic}")
                cache_file.unlink()  # Delete expired cache
                return None
            
            # Convert back to ClaimAnalysis objects
            claims = [ClaimAnalysis(**claim) for claim in data['claims']]
            
            # Mark as cached
            for claim in claims:
                claim.cached = True
            
            print(f"✅ Cache hit for topic: {topic}")
            return claims
            
        except Exception as e:
            print(f"❌ Cache read error: {e}")
            return None
    
    def set(self, topic: str, claims: List[ClaimAnalysis]) -> None:
        """Store analysis in cache"""
        cache_key = self._get_cache_key(topic)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            data = {
                'topic': topic,
                'cached_at': datetime.now().isoformat(),
                'claims': [claim.model_dump() for claim in claims]
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            print(f"💾 Cached results for topic: {topic}")
            
        except Exception as e:
            print(f"❌ Cache write error: {e}")
    
    def clear_old_entries(self) -> int:
        """Remove expired cache entries. Returns number of entries removed."""
        removed = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                cached_at = datetime.fromisoformat(data['cached_at'])
                if datetime.now() - cached_at > self.ttl:
                    cache_file.unlink()
                    removed += 1
                    
            except Exception:
                continue
        
        if removed > 0:
            print(f"🗑️ Removed {removed} expired cache entries")
        
        return removed
