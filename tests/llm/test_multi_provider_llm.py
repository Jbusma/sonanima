#!/usr/bin/env python3
"""
Test Multi-Provider LLM Functionality
"""
import sys
import pytest
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sonanima.core.companion import SonanimaCompanion

class TestMultiProviderLLM:
    """Test multi-provider LLM functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.companion = SonanimaCompanion()
    
    def test_companion_initialization(self):
        """Test companion initializes correctly"""
        assert self.companion is not None
        assert hasattr(self.companion, 'llm_client')
        assert hasattr(self.companion, 'llm_provider')
        assert hasattr(self.companion, 'llm_model')
    
    def test_provider_detection(self):
        """Test LLM provider auto-detection"""
        # Should detect available providers
        assert self.companion.llm_provider in ["anthropic", "openai", "ollama"]
    
    def test_anthropic_setup(self):
        """Test Anthropic Claude setup"""
        original_provider = self.companion.llm_provider
        
        self.companion.llm_provider = "anthropic"
        self.companion._setup_llm()
        
        assert self.companion.llm_provider == "anthropic"
        # Should have client if API key available
        if os.getenv('ANTHROPIC_API_KEY'):
            assert self.companion.llm_client is not None
        
        # Restore original provider
        self.companion.llm_provider = original_provider
        self.companion._setup_llm()
    
    def test_openai_setup(self):
        """Test OpenAI GPT setup"""
        original_provider = self.companion.llm_provider
        
        self.companion.llm_provider = "openai"
        self.companion._setup_llm()
        
        assert self.companion.llm_provider == "openai"
        # Should have client if API key available
        if os.getenv('OPENAI_API_KEY'):
            assert self.companion.llm_client is not None
        
        # Restore original provider
        self.companion.llm_provider = original_provider
        self.companion._setup_llm()
    
    def test_ollama_setup(self):
        """Test Ollama local LLM setup"""
        original_provider = self.companion.llm_provider
        
        self.companion.llm_provider = "ollama"
        self.companion._setup_llm()
        
        assert self.companion.llm_provider == "ollama"
        # Client availability depends on Ollama running locally
        
        # Restore original provider
        self.companion.llm_provider = original_provider
        self.companion._setup_llm()
    
    def test_invalid_provider_handling(self):
        """Test handling of invalid provider"""
        original_provider = self.companion.llm_provider
        
        self.companion.llm_provider = "invalid_provider"
        self.companion._setup_llm()
        
        # Should handle gracefully
        assert self.companion.llm_provider == "invalid_provider"
        assert self.companion.llm_client is None
        
        # Restore original provider
        self.companion.llm_provider = original_provider
        self.companion._setup_llm()
    
    def test_model_configuration(self):
        """Test model configuration for different providers"""
        # Test default models (flexible matching for actual vs expected)
        test_cases = [
            ("anthropic", ["claude-3-5-sonnet", "claude-sonnet-4"]),
            ("openai", ["gpt-4"]),
            ("ollama", ["llama3.2", "llama"])
        ]
        
        original_provider = self.companion.llm_provider
        original_model = self.companion.llm_model
        
        for provider, expected_models in test_cases:
            self.companion.llm_provider = provider
            model = self.companion._get_default_model()
            # Check if any expected model pattern is in the actual model
            assert any(expected in model for expected in expected_models), f"Model {model} doesn't match expected patterns {expected_models}"
        
        # Restore original settings
        self.companion.llm_provider = original_provider
        self.companion.llm_model = original_model
    
    def test_llm_response_generation(self):
        """Test LLM response generation"""
        if self.companion.llm_client is None:
            pytest.skip("No LLM client available")
        
        # Test basic response generation
        test_input = "Hello, how are you?"
        response, emotion = self.companion._generate_llm_response(test_input, "neutral")
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert isinstance(emotion, str)
    
    def test_emotion_detection(self):
        """Test emotion detection from text"""
        test_cases = [
            ("I'm so happy today!", "joy"),
            ("I feel terrible and sad", "sadness"),
            ("I'm really worried about this", "anxiety"),
            ("This makes me so angry!", "anger"),
            ("Wow, that's incredible!", "surprise"),
            ("The weather is nice", "neutral")
        ]
        
        for text, expected_emotion in test_cases:
            detected = self.companion.detect_emotion(text)
            assert detected == expected_emotion
    
    def test_topic_extraction(self):
        """Test conversation topic extraction"""
        test_cases = [
            ("I love my job and my colleagues", ["work"]),
            ("My family is very important to me", ["family"]),
            ("I need to see a doctor about my health", ["health"]),
            ("I enjoy reading books and playing games", ["hobbies"]),
            ("I want to achieve my goals in the future", ["future"])
        ]
        
        for text, expected_topics in test_cases:
            topics = self.companion.extract_topics(text)
            for expected_topic in expected_topics:
                assert expected_topic in topics
    
    def test_conversation_context(self):
        """Test conversation context management"""
        # Test that companion maintains context
        assert hasattr(self.companion, 'conversation_topics')
        assert hasattr(self.companion, 'emotional_context')
        assert hasattr(self.companion, 'user_name')
    
    def test_memory_integration(self):
        """Test memory system integration"""
        assert self.companion.memory is not None
        assert hasattr(self.companion.memory, 'add_memory')
        assert hasattr(self.companion.memory, 'search_memories')
    
    def test_provider_switching(self):
        """Test switching between LLM providers"""
        if not any(os.getenv(key) for key in ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY']):
            pytest.skip("No API keys available for testing")
        
        original_provider = self.companion.llm_provider
        providers_to_test = ["anthropic", "openai", "ollama"]
        
        for provider in providers_to_test:
            self.companion.llm_provider = provider
            self.companion._setup_llm()
            assert self.companion.llm_provider == provider
        
        # Restore original provider
        self.companion.llm_provider = original_provider
        self.companion._setup_llm()
    
    def test_response_emotion_mapping(self):
        """Test response emotion mapping"""
        test_cases = [
            ("joy", ["joy"]),
            ("sadness", ["empathy"]),
            ("anxiety", ["comfort"]),
            ("anger", ["calm"]),
            ("surprise", ["interest"]),
            ("neutral", ["interest"])
        ]
        
        for user_emotion, valid_responses in test_cases:
            response_emotion = self.companion._get_response_emotion(user_emotion)
            assert response_emotion in valid_responses
    
    def test_fallback_response(self):
        """Test fallback response generation"""
        test_input = "Hello there"
        response, emotion = self.companion._generate_fallback_response(test_input, "neutral")
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert isinstance(emotion, str)
        assert emotion in ["interest", "empathy", "joy", "comfort", "calm"]


def test_llm_integration():
    """Integration test for LLM system"""
    companion = SonanimaCompanion()
    
    # Test basic functionality
    assert companion is not None
    assert hasattr(companion, 'llm_provider')
    
    # Test emotion detection
    emotion = companion.detect_emotion("I'm feeling great today!")
    assert emotion in ["joy", "neutral"]
    
    # Test topic extraction
    topics = companion.extract_topics("I love working on computer projects")
    assert "work" in topics or "technology" in topics
    
    print(f"✅ LLM Integration test passed - Provider: {companion.llm_provider}")
    return True


if __name__ == "__main__":
    # Run integration test
    test_llm_integration()
    
    # Run all tests
    pytest.main([__file__, "-v"]) 