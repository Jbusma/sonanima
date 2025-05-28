#!/usr/bin/env python3
"""
Unit tests for sonanima.tts.elevenlabs.streaming module
Code quality and functionality verification
"""
import asyncio
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from sonanima.tts.elevenlabs.streaming import SonanimaStreamingTTS

def test_module_import():
    """Test that the streaming module imports correctly"""
    assert SonanimaStreamingTTS is not None
    return True

def test_class_initialization():
    """Test TTS class initializes with correct defaults"""
    tts = SonanimaStreamingTTS()
    assert tts.current_voice == 'rachel'
    assert tts.model_id == 'eleven_flash_v2_5'
    assert not tts.ready
    assert len(tts.voices) > 0
    return True

def test_voice_configuration():
    """Test voice switching functionality"""
    tts = SonanimaStreamingTTS()
    original_voice = tts.current_voice
    
    # Test valid voice change
    tts.current_voice = 'bella'
    assert tts.current_voice == 'bella'
    
    # Restore original
    tts.current_voice = original_voice
    assert tts.current_voice == original_voice
    return True

def test_environment_loading():
    """Test environment file loading functionality"""
    tts = SonanimaStreamingTTS()
    # This should not crash even if .env doesn't exist
    result = tts.load_env_file()
    assert isinstance(result, bool)
    return True

def test_setup_configuration():
    """Test setup method handles missing API key gracefully"""
    tts = SonanimaStreamingTTS()
    # Should return False if API key not available, but not crash
    result = tts.setup()
    assert isinstance(result, bool)
    return True

async def test_websocket_method_exists():
    """Test that streaming methods exist and are callable"""
    tts = SonanimaStreamingTTS()
    
    # Test method exists
    assert hasattr(tts, 'stream_speech_websocket')
    assert hasattr(tts, 'stream_and_play')
    assert hasattr(tts, 'stream_speech_sync')
    
    # These should be async generators/methods
    assert asyncio.iscoroutinefunction(tts.stream_and_play)
    # Note: stream_speech_websocket is an async generator, different check needed
    assert hasattr(tts.stream_speech_websocket, '__call__')
    return True

def run_unit_tests():
    """Run all unit tests for streaming module"""
    tests = [
        ("Module Import", test_module_import),
        ("Class Initialization", test_class_initialization),
        ("Voice Configuration", test_voice_configuration),
        ("Environment Loading", test_environment_loading),
        ("Setup Configuration", test_setup_configuration),
    ]
    
    # Add async test
    async def run_async_tests():
        return await test_websocket_method_exists()
    
    results = []
    
    # Run sync tests
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result, None))
        except Exception as e:
            results.append((name, False, str(e)))
    
    # Run async test
    try:
        async_result = asyncio.run(run_async_tests())
        results.append(("WebSocket Methods", async_result, None))
    except Exception as e:
        results.append(("WebSocket Methods", False, str(e)))
    
    # Print results
    passed = 0
    for name, success, error in results:
        if success:
            print(f"✅ {name}")
            passed += 1
        else:
            print(f"❌ {name}: {error}")
    
    total = len(results)
    print(f"\n📊 Unit Tests: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All unit tests passed!")
        return True
    else:
        print("❌ Some unit tests failed")
        return False

if __name__ == "__main__":
    print("🧪 ElevenLabs Streaming Unit Tests")
    print("=" * 40)
    success = run_unit_tests()
    sys.exit(0 if success else 1) 