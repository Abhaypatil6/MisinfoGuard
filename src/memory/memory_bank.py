import sqlite3
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
from src.core.models import ClaimAnalysis

class MemoryBank:
    """
    Long-term persistent storage for verified claims
    Demonstrates: Sessions & Memory concept from course
    """
    
    def __init__(self, db_path: str = "memory_bank.db"):
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_hash TEXT NOT NULL,
                topic TEXT NOT NULL,
                claims_json TEXT NOT NULL,
                stored_at TIMESTAMP NOT NULL,
                accessed_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_topic_hash 
            ON claims(topic_hash)
        ''')
        
        conn.commit()
        conn.close()
        print("💾 Memory Bank initialized")
    
    def _hash_topic(self, topic: str) -> str:
        """Generate consistent hash for topic"""
        return hashlib.md5(topic.lower().strip().encode()).hexdigest()
    
    def get(self, topic: str) -> Optional[List[ClaimAnalysis]]:
        """
        Retrieve claims from memory bank if available
        Returns None if not found or expired (24hr TTL)
        """
        topic_hash = self._hash_topic(topic)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT claims_json, stored_at 
            FROM claims 
            WHERE topic_hash = ? 
            ORDER BY stored_at DESC 
            LIMIT 1
        ''', (topic_hash,))
        
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return None
        
        claims_json, stored_at = result
        
        # Check if expired (24 hours TTL)
        stored_time = datetime.fromisoformat(stored_at)
        if datetime.now() - stored_time > timedelta(hours=24):
            print(f"🗑️ Memory expired for: {topic}")
            conn.close()
            return None
        
        # Update access tracking
        cursor.execute('''
            UPDATE claims 
            SET accessed_count = accessed_count + 1,
                last_accessed = ?
            WHERE topic_hash = ?
        ''', (datetime.now().isoformat(), topic_hash))
        
        conn.commit()
        conn.close()
        
        # Deserialize claims
        claims_data = json.loads(claims_json)
        claims = [ClaimAnalysis(**claim) for claim in claims_data]
        
        # Mark as cached
        for claim in claims:
            claim.cached = True
        
        print(f"✅ Memory hit for: {topic}")
        return claims
    
    def store(self, topic: str, claims: List[ClaimAnalysis]):
        """Store claims in memory bank"""
        topic_hash = self._hash_topic(topic)
        
        claims_json = json.dumps(
            [claim.model_dump() for claim in claims],
            default=str
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO claims (topic_hash, topic, claims_json, stored_at)
            VALUES (?, ?, ?, ?)
        ''', (topic_hash, topic, claims_json, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        print(f"💾 Stored in memory bank: {topic}")
    
    def get_stats(self) -> dict:
        """Get memory bank statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM claims')
        total_entries = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(accessed_count) FROM claims')
        total_accesses = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total_entries": total_entries,
            "total_accesses": total_accesses,
            "cache_hit_rate": total_accesses / max(total_entries, 1)
        }
