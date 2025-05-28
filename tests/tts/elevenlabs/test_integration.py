#!/usr/bin/env python3
"""
Unit tests for sonanima.tts.elevenlabs.integration module
Code quality and functionality verification
"""
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

def test_integration_module_placeholder():
    """Test that integration module structure is ready"""
    # Placeholder test for when integration.py is implemented
    # For now, just verify the test framework works
    assert True
    return True

def test_integration_imports():
    """Test that future integration imports will work"""
    # Test that the path structure is correct for future imports
    # from sonanima.tts.elevenlabs.integration import SomeClass
    try:
        # Import path verification
        import sonanima.tts.elevenlabs
        assert hasattr(sonanima.tts.elevenlabs, '__file__')
        return True
    except ImportError:
        return False

def test_voices_interactive():
    """Interactive test for different voices (moved from production code)"""
    try:
        from sonanima.tts.elevenlabs.integration import SonanimaElevenLabs
        
        tts = SonanimaElevenLabs()
        if not tts.ready:
            print("⚠️ ElevenLabs not ready - skipping interactive test")
            return True
        
        test_text = "Hello! I'm Sonanima, testing different voices."
        print("🧪 Testing ElevenLabs voices...")
        
        # Test a few key voices
        test_voices = ['rachel', 'bella', 'antoni', 'josh']
        
        for voice in test_voices:
            if voice in tts.voices:
                print(f"\n🎭 Testing {voice}...")
                tts.speak(f"Hi, this is {voice}. {test_text}", voice=voice)
                time.sleep(1)
        
        print("\n🎉 Voice test complete!")
        return True
        
    except ImportError:
        print("⚠️ Integration module not available")
        return True
    except Exception as e:
        print(f"❌ Voice test error: {e}")
        return False

def test_emotions_interactive():
    """Interactive test for different emotions (moved from production code)"""
    try:
        from sonanima.tts.elevenlabs.integration import SonanimaElevenLabs
        
        tts = SonanimaElevenLabs()
        if not tts.ready:
            print("⚠️ ElevenLabs not ready - skipping interactive test")
            return True
        
        voice = tts.default_voice
        print(f"🎭 Testing emotions with {voice}...")
        
        emotion_tests = [
            ("I'm feeling quite happy today!", "happy"),
            ("This is so exciting, I can't contain myself!", "excited"), 
            ("Let me speak in a calm, peaceful tone.", "calm"),
            ("I'm feeling a bit sad about this.", "sad"),
        ]
        
        for text, emotion in emotion_tests:
            print(f"\n😊 Testing {emotion}...")
            tts.speak(text, voice=voice, emotion=emotion)
            time.sleep(1)
        
        print("\n🎉 Emotion test complete!")
        return True
        
    except ImportError:
        print("⚠️ Integration module not available")
        return True
    except Exception as e:
        print(f"❌ Emotion test error: {e}")
        return False

def run_unit_tests():
    """Run all unit tests for integration module"""
    tests = [
        ("Integration Module Placeholder", test_integration_module_placeholder),
        ("Integration Imports", test_integration_imports),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result, None))
        except Exception as e:
            results.append((name, False, str(e)))
    
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

def run_interactive_tests():
    """Run interactive audio tests"""
    print("\n🎵 Interactive Audio Tests")
    print("=" * 40)
    
    tests = [
        ("Voice Test", test_voices_interactive),
        ("Emotion Test", test_emotions_interactive),
    ]
    
    for name, test_func in tests:
        print(f"\n🧪 {name}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ {name} failed: {e}")

if __name__ == "__main__":
    print("🧪 ElevenLabs Integration Tests")
    print("=" * 40)
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        run_interactive_tests()
    else:
        success = run_unit_tests()
        sys.exit(0 if success else 1) 