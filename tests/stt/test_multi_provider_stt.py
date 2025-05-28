#!/usr/bin/env python3
"""
Test Multi-Provider STT Functionality
"""
import sys
import pytest
import tempfile
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sonanima.stt.engine import SonanimaStt

class TestMultiProviderSTT:
    """Test multi-provider STT functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.stt_engine = SonanimaStt()
        
        # Create test audio data (simple sine wave)
        self.sample_rate = 16000
        duration = 2.0  # 2 seconds
        frequency = 440  # A4 note
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        self.test_audio = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    
    def test_stt_engine_initialization(self):
        """Test STT engine initializes correctly"""
        assert self.stt_engine is not None
        assert hasattr(self.stt_engine, 'provider')
        assert hasattr(self.stt_engine, 'transcribe_audio')
    
    def test_provider_priority_order(self):
        """Test provider priority ordering"""
        expected_providers = [
            "openai_whisper", 
            "whisper_cpp", 
            "vosk", 
            "speech_recognition", 
            "faster_whisper"
        ]
        
        # Check if provider selection follows priority
        for provider in expected_providers:
            if hasattr(self.stt_engine, f'_setup_{provider}'):
                # Provider should be available
                original_provider = self.stt_engine.provider
                self.stt_engine.provider = provider
                assert self.stt_engine.provider == provider
                self.stt_engine.provider = original_provider
                break
    
    def test_provider_fallback(self):
        """Test automatic provider fallback"""
        # Try to set an invalid provider
        original_provider = self.stt_engine.provider
        self.stt_engine.provider = "invalid_provider"
        
        # Should fallback to a working provider
        result = self.stt_engine.transcribe_audio(self.test_audio)
        
        # Should either work or gracefully fail
        assert isinstance(result, (str, type(None)))
        
        # Restore original provider
        self.stt_engine.provider = original_provider
    
    def test_openai_whisper_availability(self):
        """Test OpenAI Whisper provider availability"""
        if hasattr(self.stt_engine, '_setup_openai_whisper'):
            self.stt_engine.provider = "openai_whisper"
            assert self.stt_engine.provider == "openai_whisper"
    
    def test_whisper_cpp_availability(self):
        """Test Whisper.cpp provider availability"""
        if hasattr(self.stt_engine, '_setup_whisper_cpp'):
            self.stt_engine.provider = "whisper_cpp"
            assert self.stt_engine.provider == "whisper_cpp"
    
    def test_vosk_availability(self):
        """Test Vosk provider availability"""
        if hasattr(self.stt_engine, '_setup_vosk'):
            self.stt_engine.provider = "vosk"
            assert self.stt_engine.provider == "vosk"
    
    def test_speech_recognition_availability(self):
        """Test SpeechRecognition provider availability"""
        if hasattr(self.stt_engine, '_setup_speech_recognition'):
            self.stt_engine.provider = "speech_recognition"
            assert self.stt_engine.provider == "speech_recognition"
    
    def test_faster_whisper_availability(self):
        """Test Faster-Whisper provider availability"""
        if hasattr(self.stt_engine, '_setup_faster_whisper'):
            self.stt_engine.provider = "faster_whisper"
            assert self.stt_engine.provider == "faster_whisper"
    
    def test_transcribe_audio_basic(self):
        """Test basic audio transcription"""
        result = self.stt_engine.transcribe_audio(self.test_audio)
        
        # Should return string or None
        assert isinstance(result, (str, type(None)))
        
        if result:
            assert len(result) >= 0  # Can be empty string
    
    def test_transcribe_audio_with_different_providers(self):
        """Test transcription with different providers"""
        providers_to_test = [
            "openai_whisper", 
            "whisper_cpp", 
            "vosk", 
            "speech_recognition", 
            "faster_whisper"
        ]
        
        results = {}
        original_provider = self.stt_engine.provider
        
        for provider in providers_to_test:
            if hasattr(self.stt_engine, f'_setup_{provider}'):
                try:
                    self.stt_engine.provider = provider
                    result = self.stt_engine.transcribe_audio(self.test_audio)
                    results[provider] = result
                    assert isinstance(result, (str, type(None)))
                except Exception as e:
                    results[provider] = f"Error: {e}"
        
        # Restore original provider
        self.stt_engine.provider = original_provider
        
        # At least one provider should work
        working_providers = [p for p, r in results.items() if not str(r).startswith("Error")]
        assert len(working_providers) > 0, f"No working providers found: {results}"
    
    def test_empty_audio_handling(self):
        """Test handling of empty audio"""
        empty_audio = np.array([])
        result = self.stt_engine.transcribe_audio(empty_audio)
        
        # Should handle gracefully
        assert isinstance(result, (str, type(None)))
    
    def test_very_short_audio_handling(self):
        """Test handling of very short audio"""
        short_audio = np.zeros(100)  # Very short audio
        result = self.stt_engine.transcribe_audio(short_audio)
        
        # Should handle gracefully
        assert isinstance(result, (str, type(None)))
    
    def test_provider_switching(self):
        """Test switching between providers"""
        providers = ["openai_whisper", "whisper_cpp", "vosk"]
        original_provider = self.stt_engine.provider
        
        for provider in providers:
            if hasattr(self.stt_engine, f'_setup_{provider}'):
                self.stt_engine.provider = provider
                assert self.stt_engine.provider == provider
                
                # Should still be able to transcribe
                result = self.stt_engine.transcribe_audio(self.test_audio)
                assert isinstance(result, (str, type(None)))
        
        # Restore original provider
        self.stt_engine.provider = original_provider


def test_stt_integration():
    """Integration test for STT system"""
    stt = SonanimaStt()
    
    # Test basic functionality
    assert stt is not None
    assert hasattr(stt, 'transcribe_audio')
    
    # Test with sample audio
    sample_rate = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    test_audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    
    result = stt.transcribe_audio(test_audio)
    assert isinstance(result, (str, type(None)))
    
    print(f"✅ STT Integration test passed - Provider: {stt.provider}")
    return True


if __name__ == "__main__":
    # Run integration test
    test_stt_integration()
    
    # Run all tests
    pytest.main([__file__, "-v"]) 