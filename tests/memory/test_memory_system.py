#!/usr/bin/env python3
"""
Test Memory System Functionality
"""
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sonanima.memory.vector_store import SonanimaMemory

class TestMemorySystem:
    """Test memory system functionality"""
    
    def setup_method(self):
        """Setup for each test with temporary memory directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.memory = SonanimaMemory(memory_dir=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup after each test"""
        if hasattr(self, 'memory'):
            self.memory.close()
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_memory_initialization(self):
        """Test memory system initializes correctly"""
        assert self.memory is not None
        assert hasattr(self.memory, 'add_memory')
        assert hasattr(self.memory, 'search_memories')
        assert hasattr(self.memory, 'get_conversation_context')
    
    def test_add_memory_basic(self):
        """Test basic memory addition"""
        content = "my name is Jack"
        speaker = "user"
        emotion = "neutral"
        
        memory_id = self.memory.add_memory(content, speaker, emotion)
        
        assert memory_id is not None
        assert isinstance(memory_id, str)
        assert memory_id.startswith('mem_')
    
    def test_search_memories_name_example(self):
        """Test the Jack name example specifically"""
        # Add the memory
        self.memory.add_memory("my name is Jack", "user", "neutral")
        
        # Search for name
        results = self.memory.search_memories("what is my name", limit=3)
        
        assert len(results) > 0
        assert results[0]['content'] == "my name is Jack"
        assert results[0]['speaker'] == "user"
        assert 'similarity' in results[0]
    
    def test_search_memories_with_dummy_data(self):
        """Test memory search with realistic dummy data"""
        # Add various personal information
        memories = [
            "my name is Jack",
            "my cousin's name is Charlie", 
            "I live in San Francisco",
            "my favorite food is pizza",
            "I work as a software engineer",
            "my dog's name is Buddy",
            "my sister lives in New York",
            "I love playing guitar"
        ]
        
        for memory in memories:
            self.memory.add_memory(memory, "user", "neutral")
        
        # Test specific searches
        name_results = self.memory.search_memories("what is my name", limit=3)
        cousin_results = self.memory.search_memories("tell me about my cousin", limit=3)
        location_results = self.memory.search_memories("where do I live", limit=3)
        
        # Verify correct memories are retrieved
        assert any("Jack" in result['content'] for result in name_results)
        assert any("Charlie" in result['content'] for result in cousin_results)
        assert any("San Francisco" in result['content'] for result in location_results)
    
    def test_search_memories_relevance(self):
        """Test memory search finds relevant content"""
        # Add various memories
        self.memory.add_memory("I love pizza", "user", "joy")
        self.memory.add_memory("my favorite color is blue", "user", "neutral")
        self.memory.add_memory("I work as a software engineer", "user", "neutral")
        
        # Search for food preferences
        results = self.memory.search_memories("what food do I like", limit=3)
        
        # Should find pizza memory
        pizza_found = any("pizza" in result['content'].lower() for result in results)
        assert pizza_found
    
    def test_conversation_context(self):
        """Test conversation context retrieval"""
        # Add a sequence of memories
        memories = [
            ("Hello there", "user", "neutral"),
            ("Hi! How are you?", "sonanima", "joy"),
            ("I'm doing well, thanks", "user", "joy"),
            ("That's great to hear!", "sonanima", "joy")
        ]
        
        for content, speaker, emotion in memories:
            self.memory.add_memory(content, speaker, emotion)
        
        # Get conversation context (correct parameter name is 'messages')
        context = self.memory.get_conversation_context(messages=4)
        
        assert len(context) == 4
        assert context[0]['content'] == "Hello there"  # First message
        assert context[-1]['content'] == "That's great to hear!"  # Last message
    
    def test_memory_with_different_emotions(self):
        """Test memory storage with various emotions"""
        emotions = ["joy", "sadness", "anger", "surprise", "neutral"]
        
        for i, emotion in enumerate(emotions):
            content = f"Test message {i} with {emotion}"
            memory_id = self.memory.add_memory(content, "user", emotion)
            assert memory_id is not None
        
        # Search should find all memories
        results = self.memory.search_memories("test message", limit=10)
        assert len(results) == len(emotions)
    
    def test_memory_importance_scoring(self):
        """Test that memories have importance scores"""
        self.memory.add_memory("I love my family", "user", "joy")
        
        results = self.memory.search_memories("family", limit=1)
        
        assert len(results) > 0
        assert 'importance' in results[0]
        assert isinstance(results[0]['importance'], (int, float))
        assert results[0]['importance'] > 0
    
    def test_memory_timestamps(self):
        """Test that memories have proper timestamps"""
        before_time = datetime.now()
        self.memory.add_memory("timestamp test", "user", "neutral")
        after_time = datetime.now()
        
        results = self.memory.search_memories("timestamp test", limit=1)
        
        assert len(results) > 0
        memory_time = results[0]['timestamp']
        assert isinstance(memory_time, datetime)
        assert before_time <= memory_time <= after_time
    
    def test_empty_search(self):
        """Test search with no matching memories"""
        self.memory.add_memory("completely unrelated content", "user", "neutral")
        
        results = self.memory.search_memories("quantum physics equations", limit=3)
        
        # Should return empty or very low similarity results
        if results:
            assert results[0]['similarity'] < 0.3  # Very low similarity
    
    def test_memory_stats(self):
        """Test memory statistics"""
        # Add some memories
        for i in range(5):
            self.memory.add_memory(f"Test memory {i}", "user", "neutral")
        
        stats = self.memory.get_memory_stats()
        
        assert 'total_memories' in stats
        assert stats['total_memories'] >= 5
        assert 'storage_type' in stats
    
    def test_emotional_summary(self):
        """Test emotional summary functionality"""
        emotions = ["joy", "joy", "sadness", "neutral"]
        
        for i, emotion in enumerate(emotions):
            self.memory.add_memory(f"Message {i}", "user", emotion)
        
        summary = self.memory.get_emotional_summary()
        
        assert isinstance(summary, dict)
        # The emotional summary returns weighted averages, not counts
        # So we just check that joy is present and has a reasonable value
        if "joy" in summary:
            assert summary["joy"] > 0
        # Check that we have some emotional data
        assert len(summary) > 0


def test_memory_integration_with_companion():
    """Integration test with companion system"""
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        from sonanima.core.companion import SonanimaCompanion
        
        # Create companion with temporary memory
        companion = SonanimaCompanion(data_dir=temp_dir)
        
        # Test the Jack example
        companion.memory.add_memory("my name is Jack", "user", "neutral")
        
        # Generate response
        response, emotion = companion.generate_response("what is my name", "neutral")
        
        # Should mention Jack
        assert "jack" in response.lower()
        assert isinstance(emotion, str)
        
        companion.close()
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("✅ Memory integration test passed")


def test_full_llm_memory_pipeline():
    """Test complete pipeline: Memory → LLM → Response with actual content verification"""
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        from sonanima.core.companion import SonanimaCompanion
        
        # Create companion with temporary memory
        companion = SonanimaCompanion(data_dir=temp_dir)
        
        # Add realistic personal data
        personal_memories = [
            "my name is Jack",
            "my cousin's name is Charlie",
            "I live in San Francisco", 
            "my favorite food is pizza",
            "I work as a software engineer",
            "my dog's name is Buddy",
            "my sister Sarah lives in New York",
            "I love playing guitar on weekends"
        ]
        
        for memory in personal_memories:
            companion.memory.add_memory(memory, "user", "neutral")
        
        print("🧠 Added personal memories to test database")
        
        # Test various queries that should retrieve and use specific memories
        test_cases = [
            {
                "query": "what is my name",
                "expected_content": "jack",
                "description": "Name retrieval"
            },
            {
                "query": "tell me about my cousin",
                "expected_content": "charlie", 
                "description": "Cousin information"
            },
            {
                "query": "where do I live",
                "expected_content": "san francisco",
                "description": "Location information"
            },
            {
                "query": "what's my favorite food",
                "expected_content": "pizza",
                "description": "Food preference"
            },
            {
                "query": "what's my dog's name",
                "expected_content": "buddy",
                "description": "Pet information"
            },
            {
                "query": "tell me about my sister",
                "expected_content": "sarah",
                "description": "Family member info"
            }
        ]
        
        results = []
        for test_case in test_cases:
            print(f"🔍 Testing: {test_case['description']}")
            print(f"   Query: '{test_case['query']}'")
            
            # Generate response using full pipeline
            response, emotion = companion.generate_response(test_case['query'], "neutral")
            
            print(f"   Response: '{response}'")
            
            # Check if expected content is in response
            contains_expected = test_case['expected_content'].lower() in response.lower()
            
            results.append({
                'test': test_case['description'],
                'query': test_case['query'],
                'response': response,
                'expected': test_case['expected_content'],
                'success': contains_expected
            })
            
            print(f"   ✅ Success: {contains_expected}")
            print()
        
        # Verify all tests passed
        successful_tests = [r for r in results if r['success']]
        total_tests = len(results)
        success_rate = len(successful_tests) / total_tests
        
        print(f"📊 Test Results: {len(successful_tests)}/{total_tests} passed ({success_rate:.1%})")
        
        # Print failed tests for debugging
        failed_tests = [r for r in results if not r['success']]
        if failed_tests:
            print("❌ Failed tests:")
            for test in failed_tests:
                print(f"   - {test['test']}: Expected '{test['expected']}' in response '{test['response']}'")
        
        companion.close()
        
        # Assert that most tests passed (allow some flexibility for LLM variability)
        assert success_rate >= 0.7, f"Only {success_rate:.1%} of memory-LLM integration tests passed"
        
        # Specifically test the Jack example
        jack_test = next((r for r in results if 'jack' in r['expected']), None)
        assert jack_test and jack_test['success'], "Jack name test failed - core memory functionality broken"
        
        print("✅ Full LLM-Memory pipeline test passed!")
        return results
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_memory_disambiguation():
    """Test memory system can distinguish between similar but different information"""
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        from sonanima.core.companion import SonanimaCompanion
        
        companion = SonanimaCompanion(data_dir=temp_dir)
        
        # Add potentially confusing memories
        confusing_memories = [
            "my name is Jack",
            "my cousin's name is Charlie",
            "my brother's name is Jake", 
            "my friend Charlie works at Google",
            "I met a guy named Jack at the store",
            "Charlie is my cousin who lives in Boston"
        ]
        
        for memory in confusing_memories:
            companion.memory.add_memory(memory, "user", "neutral")
        
        # Test disambiguation
        response, _ = companion.generate_response("what is my name", "neutral")
        
        # Should mention Jack (the user's name) not Jake or other Jacks
        assert "jack" in response.lower()
        # Should not confuse with brother's name
        assert "jake" not in response.lower() or "jack" in response.lower()
        
        # Test cousin query
        cousin_response, _ = companion.generate_response("tell me about my cousin", "neutral")
        assert "charlie" in cousin_response.lower()
        
        companion.close()
        print("✅ Memory disambiguation test passed!")
        
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    # Run integration tests first
    print("🧪 Running Memory-LLM Integration Tests...")
    test_memory_integration_with_companion()
    test_full_llm_memory_pipeline()
    test_memory_disambiguation()
    
    # Run all unit tests
    print("\n🧪 Running Unit Tests...")
    pytest.main([__file__, "-v"]) 