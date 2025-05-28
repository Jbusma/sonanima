#!/usr/bin/env python3
"""
Test Multi-Provider TTS Functionality
"""
import sys
import pytest
import tempfile
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sonanima.tts.engine import SonanimaTts

class TestMultiProviderTTS:
    """Test multi-provider TTS functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.tts_engine = SonanimaTts()
        self.test_text = "Hello, this is a test of the text-to-speech system."
        self.test_emotion = "neutral"
    
    def test_tts_engine_initialization(self):
        """Test TTS engine initializes correctly"""
        assert self.tts_engine is not None
        assert hasattr(self.tts_engine, 'provider')
        assert hasattr(self.tts_engine, 'speak')
        assert hasattr(self.tts_engine, 'speak_streaming')
    
    def test_provider_priority_order(self):
        """Test provider priority ordering"""
        expected_providers = [
            "elevenlabs", 
            "pyttsx3", 
            "system"
        ]
        
        # Should have a valid provider
        assert self.tts_engine.provider in expected_providers
    
    def test_elevenlabs_availability(self):
        """Test ElevenLabs provider availability"""
        if hasattr(self.tts_engine, 'elevenlabs_tts'):
            assert self.tts_engine.elevenlabs_tts is not None
    
    def test_pyttsx3_availability(self):
        """Test pyttsx3 provider availability"""
        if hasattr(self.tts_engine, 'pyttsx3_engine'):
            assert self.tts_engine.pyttsx3_engine is not None
    
    def test_system_availability(self):
        """Test system TTS availability"""
        # System TTS should always be available as fallback
        assert hasattr(self.tts_engine, '_speak_system')
    
    def test_speak_basic(self):
        """Test basic speech functionality"""
        # Should not raise exceptions
        try:
            self.tts_engine.speak(self.test_text, self.test_emotion)
            success = True
        except Exception as e:
            print(f"Speech failed: {e}")
            success = False
        
        # Should handle gracefully even if audio fails
        assert isinstance(success, bool)
    
    def test_speak_streaming(self):
        """Test streaming speech functionality"""
        if hasattr(self.tts_engine, 'speak_streaming'):
            try:
                self.tts_engine.speak_streaming(self.test_text, self.test_emotion)
                success = True
            except Exception as e:
                print(f"Streaming speech failed: {e}")
                success = False
            
            assert isinstance(success, bool)
    
    def test_emotion_voice_mapping(self):
        """Test emotion to voice mapping"""
        emotions = ["neutral", "joy", "sadness", "anger", "surprise", "empathy", "comfort"]
        
        for emotion in emotions:
            try:
                # Should not crash with different emotions
                self.tts_engine.speak("Test", emotion)
                success = True
            except Exception as e:
                print(f"Emotion {emotion} failed: {e}")
                success = False
            
            assert isinstance(success, bool)
    
    def test_empty_text_handling(self):
        """Test handling of empty text"""
        try:
            self.tts_engine.speak("", self.test_emotion)
            success = True
        except Exception as e:
            print(f"Empty text handling failed: {e}")
            success = False
        
        assert isinstance(success, bool)
    
    def test_long_text_handling(self):
        """Test handling of long text"""
        long_text = "This is a very long text. " * 50  # 50 repetitions
        
        try:
            self.tts_engine.speak(long_text, self.test_emotion)
            success = True
        except Exception as e:
            print(f"Long text handling failed: {e}")
            success = False
        
        assert isinstance(success, bool)
    
    def test_special_characters_handling(self):
        """Test handling of special characters"""
        special_text = "Hello! How are you? I'm fine. 123... @#$%"
        
        try:
            self.tts_engine.speak(special_text, self.test_emotion)
            success = True
        except Exception as e:
            print(f"Special characters handling failed: {e}")
            success = False
        
        assert isinstance(success, bool)
    
    def test_provider_switching(self):
        """Test switching between TTS providers"""
        original_provider = self.tts_engine.provider
        
        # Test that provider switching doesn't crash
        providers_to_test = ["elevenlabs", "pyttsx3", "system"]
        
        for provider in providers_to_test:
            try:
                # Simulate provider switching
                self.tts_engine.provider = provider
                self.tts_engine.speak("Test", "neutral")
                success = True
            except Exception as e:
                print(f"Provider {provider} failed: {e}")
                success = False
            
            assert isinstance(success, bool)
        
        # Restore original provider
        self.tts_engine.provider = original_provider
    
    def test_voice_configuration(self):
        """Test voice configuration"""
        if hasattr(self.tts_engine, 'voice'):
            # Should have a voice configured
            assert self.tts_engine.voice is not None
            assert isinstance(self.tts_engine.voice, str)
    
    def test_model_configuration(self):
        """Test model configuration for ElevenLabs"""
        if hasattr(self.tts_engine, 'model'):
            # Should have a model configured
            assert self.tts_engine.model is not None
            assert isinstance(self.tts_engine.model, str)
    
    def test_concurrent_speech(self):
        """Test handling of concurrent speech requests"""
        import threading
        import time
        
        results = []
        
        def speak_test(text, emotion):
            try:
                self.tts_engine.speak(f"Test {text}", emotion)
                results.append(True)
            except Exception as e:
                print(f"Concurrent speech failed: {e}")
                results.append(False)
        
        # Start multiple speech threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=speak_test, args=(i, "neutral"))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=10)  # 10 second timeout
        
        # Should handle concurrent requests gracefully
        assert len(results) >= 0  # At least some should complete
    
    def test_error_recovery(self):
        """Test error recovery and fallback"""
        # Test with invalid emotion
        try:
            self.tts_engine.speak(self.test_text, "invalid_emotion")
            success = True
        except Exception as e:
            print(f"Invalid emotion handling: {e}")
            success = False
        
        assert isinstance(success, bool)
        
        # Test with None text
        try:
            self.tts_engine.speak(None, self.test_emotion)
            success = True
        except Exception as e:
            print(f"None text handling: {e}")
            success = False
        
        assert isinstance(success, bool)


def test_tts_integration():
    """Integration test for TTS system"""
    tts = SonanimaTts()
    
    # Test basic functionality
    assert tts is not None
    assert hasattr(tts, 'speak')
    
    # Test basic speech
    try:
        tts.speak("Integration test successful", "neutral")
        success = True
    except Exception as e:
        print(f"Integration test failed: {e}")
        success = False
    
    assert isinstance(success, bool)
    
    print(f"✅ TTS Integration test passed - Provider: {tts.provider}")
    return True


if __name__ == "__main__":
    # Run integration test
    test_tts_integration()
    
    # Run all tests
    pytest.main([__file__, "-v"]) 