#!/usr/bin/env python3
"""
Sonanima Test Runner
Comprehensive testing for all components
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main test runner interface"""
    print("🎯 Sonanima Test Runner")
    print("=" * 40)
    print("1. Multi-Provider Tests (STT/TTS/LLM)")
    print("2. Memory System Tests")
    print("3. API Integration Tests")
    print("4. Voice Companion Tests")
    print("5. All Tests (comprehensive)")
    print("6. Show test directories")
    
    choice = input("Choose test (1-6): ").strip()
    
    if choice == "1":
        run_provider_tests()
    elif choice == "2":
        run_memory_tests()
    elif choice == "3":
        run_api_tests()
    elif choice == "4":
        run_voice_tests()
    elif choice == "5":
        run_all_tests()
    elif choice == "6":
        show_test_structure()
    else:
        print("Invalid choice")

def run_provider_tests():
    """Run multi-provider tests"""
    print("\n🔄 Running Multi-Provider Tests...")
    
    tests = [
        "tests/stt/test_multi_provider_stt.py",
        "tests/tts/test_multi_provider_tts.py", 
        "tests/llm/test_multi_provider_llm.py"
    ]
    
    for test in tests:
        if Path(test).exists():
            print(f"\n📋 Running {test}...")
            subprocess.run([sys.executable, test])
        else:
            print(f"⚠️ Test not found: {test}")

def run_memory_tests():
    """Run memory system tests"""
    print("\n🧠 Running Memory System Tests...")
    
    test_file = "tests/memory/test_memory_system.py"
    if Path(test_file).exists():
        print(f"📋 Running {test_file}...")
        subprocess.run([sys.executable, test_file])
    else:
        print(f"⚠️ Test not found: {test_file}")

def run_api_tests():
    """Run API integration tests"""
    print("\n🌐 Running API Tests...")
    print("💡 Starting API server for testing...")
    
    # TODO: Add API-specific tests
    print("⚠️ API tests not yet implemented")
    print("💡 You can test the API manually:")
    print("   python src/api/main.py")
    print("   Visit: http://localhost:8000/docs")

def run_voice_tests():
    """Run voice companion tests"""
    print("\n🎤 Running Voice Companion Tests...")
    
    # Test basic companion functionality
    try:
        print("📋 Testing companion import...")
        sys.path.insert(0, str(Path.cwd() / "src"))
        from sonanima.core.companion import SonanimaCompanion
        
        print("📋 Testing companion initialization...")
        companion = SonanimaCompanion()
        
        print("📋 Testing memory integration...")
        companion.memory.add_memory("test memory", "user", "neutral")
        
        print("📋 Testing response generation...")
        response, emotion = companion.generate_response("hello", "neutral")
        
        companion.close()
        print("✅ Voice companion tests passed!")
        
    except Exception as e:
        print(f"❌ Voice companion test failed: {e}")

def run_all_tests():
    """Run comprehensive test suite"""
    print("\n🚀 Running All Tests...")
    
    print("\n1️⃣ Multi-Provider Tests")
    run_provider_tests()
    
    print("\n2️⃣ Memory System Tests") 
    run_memory_tests()
    
    print("\n3️⃣ Voice Companion Tests")
    run_voice_tests()
    
    print("\n✅ All tests completed!")

def show_test_structure():
    """Show test directory structure"""
    print("\n📁 Test Structure:")
    
    test_dirs = [
        "tests/stt/",
        "tests/tts/", 
        "tests/llm/",
        "tests/memory/"
    ]
    
    for test_dir in test_dirs:
        path = Path(test_dir)
        if path.exists():
            print(f"\n📂 {test_dir}")
            for file in path.glob("*.py"):
                if file.name != "__init__.py":
                    print(f"   📄 {file.name}")
        else:
            print(f"⚠️ {test_dir} not found")

if __name__ == "__main__":
    main() 