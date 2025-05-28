#!/usr/bin/env python3
"""
Sonanima Unified Memory System
Combines SQLite reliability with vector search capabilities
"""
import os
import json
import sqlite3
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

# Optional advanced vector database
try:
    import lancedb
    HAS_LANCEDB = True
except ImportError:
    lancedb = None
    HAS_LANCEDB = False


@dataclass
class MemoryEntry:
    """Single memory entry with metadata"""
    id: str
    content: str
    timestamp: datetime
    emotion: str
    conversation_id: str
    speaker: str  # 'user' or 'sonanima'
    importance: float  # 0.0 to 1.0
    context: Dict[str, Any]
    
    def to_dict(self):
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class SonanimaMemory:
    """Unified memory system with SQLite + optional vector acceleration"""
    
    def __init__(self, memory_dir: str = "memory", use_vector_db: bool = None):
        """
        Initialize memory system
        
        Args:
            memory_dir: Directory for memory storage (defaults to top-level 'memory/')
            use_vector_db: Force vector DB on/off. If None, auto-detect availability
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine vector DB usage
        if use_vector_db is None:
            self.use_vector_db = HAS_LANCEDB
        else:
            self.use_vector_db = use_vector_db and HAS_LANCEDB
        
        # Initialize SQLite database (always present as backup)
        self.db_path = self.memory_dir / "memories.db"
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.execute("PRAGMA journal_mode=WAL")
        
        # Initialize embedding model
        print("🧠 Loading memory embedding model...")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Setup storage systems
        self._setup_sqlite()
        if self.use_vector_db:
            self._setup_vector_db()
        
        # Conversation tracking
        self.current_conversation_id = self._generate_conversation_id()
        self.conversation_history = []
        
        storage_type = "SQLite + Vector DB" if self.use_vector_db else "SQLite only"
        print(f"✅ Sonanima memory system initialized ({storage_type})")
    
    def _setup_sqlite(self):
        """Setup SQLite database schema"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                emotion TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                speaker TEXT NOT NULL,
                importance REAL NOT NULL,
                context TEXT NOT NULL,
                embedding TEXT NOT NULL
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversation ON memories(conversation_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_speaker ON memories(speaker)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_emotion ON memories(emotion)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_importance ON memories(importance)")
        
        self.conn.commit()
        
        # Count existing memories
        cursor.execute("SELECT COUNT(*) FROM memories")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"📚 Loaded {count} existing memories from SQLite")
    
    def _setup_vector_db(self):
        """Setup optional vector database for fast similarity search"""
        try:
            self.vector_db_path = self.memory_dir / "vector_db"
            self.vector_db = lancedb.connect(str(self.vector_db_path))
            
            # Try to open existing table
            try:
                self.vector_table = self.vector_db.open_table("memories")
                print(f"📊 Loaded existing vector table with {len(self.vector_table)} entries")
            except:
                # Create new table
                sample_data = [{
                    "id": "sample",
                    "content": "sample",
                    "timestamp": datetime.now().isoformat(),
                    "importance": 0.5,
                    "embedding": [0.0] * 384  # MiniLM embedding size
                }]
                
                self.vector_table = self.vector_db.create_table("memories", data=sample_data)
                self.vector_table.delete("id = 'sample'")
                print("🆕 Created new vector table")
                
        except Exception as e:
            print(f"⚠️ Vector DB setup failed: {e}")
            print("📝 Falling back to SQLite-only mode")
            self.use_vector_db = False
            self.vector_table = None
    
    def _generate_conversation_id(self) -> str:
        """Generate unique conversation ID"""
        return f"conv_{int(time.time())}_{hash(str(datetime.now())) % 10000}"
    
    def _calculate_importance(self, content: str, emotion: str, context: Dict) -> float:
        """Calculate memory importance score"""
        importance = 0.3  # Base importance
        
        # Emotional intensity increases importance
        emotion_weights = {
            'joy': 0.8, 'excitement': 0.9, 'love': 0.9,
            'sadness': 0.7, 'anger': 0.6, 'fear': 0.6,
            'surprise': 0.5, 'neutral': 0.3, 'empathy': 0.6,
            'comfort': 0.6, 'warmth': 0.7, 'interest': 0.4
        }
        importance += emotion_weights.get(emotion, 0.3) * 0.4
        
        # Length and complexity
        if len(content) > 100:
            importance += 0.2
        
        # Special keywords that indicate important topics
        important_keywords = [
            'remember', 'important', 'love', 'hate', 'dream', 'goal',
            'family', 'friend', 'work', 'passion', 'fear', 'hope',
            'name', 'birthday', 'anniversary'
        ]
        if any(keyword in content.lower() for keyword in important_keywords):
            importance += 0.3
        
        # Questions and deep topics
        if '?' in content:
            importance += 0.1
        
        return min(importance, 1.0)
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        a = np.array(a)
        b = np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def add_memory(
        self, 
        content: str, 
        speaker: str, 
        emotion: str = "neutral",
        context: Optional[Dict] = None
    ) -> str:
        """Add new memory to the system"""
        
        if not content.strip():
            return None
            
        context = context or {}
        
        # Create memory entry
        memory_id = f"mem_{int(time.time())}_{hash(content) % 10000}"
        importance = self._calculate_importance(content, emotion, context)
        
        # Generate embedding
        embedding = self.embedder.encode(content).tolist()
        timestamp = datetime.now().isoformat()
        
        # Store in SQLite (always)
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO memories (id, content, timestamp, emotion, conversation_id, 
                                speaker, importance, context, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory_id, content.strip(), timestamp, emotion,
            self.current_conversation_id, speaker, importance,
            json.dumps(context), json.dumps(embedding)
        ))
        self.conn.commit()
        
        # Store in vector DB if available
        if self.use_vector_db and self.vector_table is not None:
            try:
                self.vector_table.add([{
                    "id": memory_id,
                    "content": content.strip(),
                    "timestamp": timestamp,
                    "importance": importance,
                    "embedding": embedding
                }])
            except Exception as e:
                print(f"⚠️ Vector DB storage failed: {e}")
        
        # Add to current conversation
        memory = MemoryEntry(
            id=memory_id,
            content=content.strip(),
            timestamp=datetime.now(),
            emotion=emotion,
            conversation_id=self.current_conversation_id,
            speaker=speaker,
            importance=importance,
            context=context
        )
        self.conversation_history.append(memory)
        
        # Silently store memory
        return memory_id
    
    def search_memories(
        self, 
        query: str, 
        limit: int = 5,
        min_importance: float = 0.0,
        time_range_days: Optional[int] = None
    ) -> List[Dict]:
        """Search memories by semantic similarity"""
        
        if not query.strip():
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedder.encode(query).tolist()
        except Exception as e:
            print(f"⚠️ Memory search failed: {e}")
            return []
        
        # Try vector DB first (faster)
        if self.use_vector_db and self.vector_table is not None:
            try:
                results = self.vector_table.search(
                    query_embedding, 
                    vector_column_name="embedding"
                ).limit(limit * 2).to_list()  # Get extra for filtering
                
                # Filter and enhance results
                filtered_results = []
                cutoff_time = datetime.now() - timedelta(days=time_range_days) if time_range_days else None
                
                for result in results:
                    timestamp = datetime.fromisoformat(result['timestamp'])
                    
                    if result['importance'] < min_importance:
                        continue
                    if cutoff_time and timestamp < cutoff_time:
                        continue
                    
                    # Get full details from SQLite
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT * FROM memories WHERE id = ?", (result['id'],))
                    full_memory = cursor.fetchone()
                    
                    if full_memory:
                        filtered_results.append({
                            'id': full_memory[0],
                            'content': full_memory[1],
                            'timestamp': datetime.fromisoformat(full_memory[2]),
                            'emotion': full_memory[3],
                            'conversation_id': full_memory[4],
                            'speaker': full_memory[5],
                            'importance': full_memory[6],
                            'context': json.loads(full_memory[7]),
                            'similarity': result.get('_distance', 0.0)
                        })
                    
                    if len(filtered_results) >= limit:
                        break
                
                return filtered_results
                
            except Exception as e:
                print(f"⚠️ Vector search failed: {e}, falling back to SQLite")
        
        try:
            # Fallback to SQLite with manual similarity calculation
            cursor = self.conn.cursor()
            
            # Build SQL query with filters
            sql = "SELECT * FROM memories WHERE importance >= ?"
            params = [min_importance]
            
            if time_range_days:
                cutoff = datetime.now() - timedelta(days=time_range_days)
                sql += " AND timestamp >= ?"
                params.append(cutoff.isoformat())
            
            cursor.execute(sql, params)
            memories = cursor.fetchall()
            
            # Calculate similarities and rank
            scored_memories = []
            for memory in memories:
                memory_embedding = json.loads(memory[8])  # embedding column
                similarity = self._cosine_similarity(query_embedding, memory_embedding)
                
                scored_memories.append({
                    'id': memory[0],
                    'content': memory[1],
                    'timestamp': datetime.fromisoformat(memory[2]),
                    'emotion': memory[3],
                    'conversation_id': memory[4],
                    'speaker': memory[5],
                    'importance': memory[6],
                    'context': json.loads(memory[7]),
                    'similarity': similarity
                })
            
            # Sort by similarity and return top results
            scored_memories.sort(key=lambda x: x['similarity'], reverse=True)
            return scored_memories[:limit]
        
        except Exception as e:
            print(f"⚠️ SQLite memory search failed: {e}")
            return []
    
    def get_conversation_context(self, messages: int = 10) -> List[Dict]:
        """Get recent conversation context"""
        if not self.conversation_history:
            return []
        
        # Convert MemoryEntry objects to dictionaries for compatibility
        recent_entries = self.conversation_history[-messages:]
        return [
            {
                'speaker': entry.speaker,
                'content': entry.content,
                'emotion': entry.emotion,
                'timestamp': entry.timestamp,
                'importance': entry.importance
            }
            for entry in recent_entries
        ]
    
    def get_emotional_summary(self, days: int = 7) -> Dict[str, float]:
        """Get emotional state summary over time"""
        cutoff = datetime.now() - timedelta(days=days)
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT emotion, importance FROM memories 
            WHERE timestamp >= ?
        """, (cutoff.isoformat(),))
        
        memories = cursor.fetchall()
        
        emotions = {}
        total_weight = 0
        
        for emotion, importance in memories:
            emotions[emotion] = emotions.get(emotion, 0) + importance
            total_weight += importance
        
        # Normalize to percentages
        if total_weight > 0:
            emotions = {k: v / total_weight for k, v in emotions.items()}
        
        return emotions
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        cursor = self.conn.cursor()
        
        # Total memories
        cursor.execute("SELECT COUNT(*) FROM memories")
        total_memories = cursor.fetchone()[0]
        
        if total_memories == 0:
            return {"total_memories": 0}
        
        # Recent emotions
        cursor.execute("SELECT emotion, COUNT(*) FROM memories GROUP BY emotion")
        emotions = dict(cursor.fetchall())
        
        # Speaker distribution
        cursor.execute("SELECT speaker, COUNT(*) FROM memories GROUP BY speaker")
        speakers = dict(cursor.fetchall())
        
        # Average importance
        cursor.execute("SELECT AVG(importance) FROM memories")
        avg_importance = cursor.fetchone()[0] or 0
        
        return {
            "total_memories": total_memories,
            "recent_emotions": emotions,
            "speaker_distribution": speakers,
            "average_importance": round(avg_importance, 3),
            "current_conversation_length": len(self.conversation_history),
            "storage_type": "Hybrid SQLite+Vector" if self.use_vector_db else "SQLite only"
        }
    
    def start_new_conversation(self):
        """Start a new conversation session"""
        self.current_conversation_id = self._generate_conversation_id()
        self.conversation_history = []
        print(f"💬 Started new conversation: {self.current_conversation_id}")
    
    def export_memories(self, filepath: Optional[str] = None) -> str:
        """Export memories to JSON file"""
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.memory_dir / f"memory_export_{timestamp}.json"
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM memories ORDER BY timestamp")
        memories = cursor.fetchall()
        
        # Convert to dict format
        memory_list = []
        for memory in memories:
            memory_dict = {
                'id': memory[0],
                'content': memory[1],
                'timestamp': memory[2],
                'emotion': memory[3],
                'conversation_id': memory[4],
                'speaker': memory[5],
                'importance': memory[6],
                'context': json.loads(memory[7])
            }
            memory_list.append(memory_dict)
        
        with open(filepath, 'w') as f:
            json.dump(memory_list, f, indent=2, default=str)
        
        print(f"📤 Exported {len(memory_list)} memories to {filepath}")
        return str(filepath)
    
    def close(self):
        """Close database connections"""
        self.conn.close()


if __name__ == "__main__":
    # Test the unified memory system
    print("🧪 Testing Unified Sonanima Memory System...")
    
    memory = SonanimaMemory()
    
    # Add test memories
    memory.add_memory("I love spending time in nature", "user", "joy")
    memory.add_memory("That sounds wonderful! Tell me about your favorite outdoor activities", "sonanima", "interest")
    memory.add_memory("I'm worried about my presentation tomorrow", "user", "anxiety")
    memory.add_memory("I understand that nervous feeling. You've got this!", "sonanima", "empathy")
    
    # Search memories
    results = memory.search_memories("nature outdoor activities")
    print(f"\n🔍 Search results for 'nature outdoor activities':")
    for result in results:
        print(f"  - {result['content'][:50]}... (similarity: {result['similarity']:.3f})")
    
    # Get stats
    stats = memory.get_memory_stats()
    print(f"\n📊 Memory stats: {stats}")
    
    memory.close()
    print("\n✅ Unified memory system test complete!") 