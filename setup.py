#!/usr/bin/env python3
"""
Sonanima Setup Script
Combined environment setup and CSM model configuration
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🌟 {title}")
    print(f"{'='*60}")

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def setup_environment():
    """Setup Python environment and dependencies"""
    print_section("Environment Setup")
    
    # Check Python version
    python_version = sys.version_info
    print(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    # Create directories
    dirs_to_create = [
        "memory",                   # Top-level memory directory
        "src/sonanima/stt/models",  # STT models with STT code
        "src/sonanima/tts/models",  # TTS models with TTS code
        "src/sonanima/bio"          # Future: biometric data processing
    ]
    
    for dir_path in dirs_to_create:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {dir_path}")
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        return False
    
    print("✅ Environment setup complete!")
    return True

def test_csm_access():
    """Test CSM model access and setup"""
    print_section("CSM Model Access Test")
    
    try:
        from huggingface_hub import HfApi, login
        import torch
        from transformers import AutoModel
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("💡 Run: pip install transformers huggingface_hub")
        return False
    
    # Check for HF token
    token_file = Path.home() / ".cache" / "huggingface" / "token"
    if not token_file.exists():
        print("⚠️ No Hugging Face token found")
        print("💡 Please run: huggingface-cli login")
        return False
    
    # Test model access
    models_to_test = [
        "SeamlessM4T/Sesame_CSM-1B", 
        "meta-llama/Llama-3.2-1B"
    ]
    
    api = HfApi()
    access_status = {}
    
    for model_id in models_to_test:
        try:
            # Try to access model info
            model_info = api.model_info(model_id)
            print(f"✅ {model_id}: Access confirmed")
            access_status[model_id] = True
            
            # Try to download (small test) to TTS models directory
            try:
                AutoModel.from_pretrained(model_id, cache_dir="src/sonanima/tts/models")
                print(f"📥 {model_id}: Download successful")
            except Exception as e:
                print(f"⚠️ {model_id}: Download failed - {e}")
                
        except Exception as e:
            print(f"❌ {model_id}: Access denied - {e}")
            access_status[model_id] = False
    
    return access_status

def setup_audio():
    """Setup and test audio components"""
    print_section("Audio System Setup")
    
    try:
        # Test TTS
        print("🔊 Testing text-to-speech...")
        from src.sonanima.tts import SonanimaTts
        tts = SonanimaTts()
        tts.speak("Sonanima setup test", "neutral")
        print("✅ TTS working")
        
        # Test microphone (if available)
        print("🎤 Testing microphone access...")
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            print(f"📱 Found {len(devices)} audio devices")
            print("✅ Audio system ready")
        except Exception as e:
            print(f"⚠️ Microphone test failed: {e}")
            print("💡 Grant microphone permissions in System Preferences")
            
    except Exception as e:
        print(f"❌ Audio setup failed: {e}")
        return False
    
    return True

def main():
    """Main setup routine"""
    print_section("Sonanima Setup")
    print("🌟 Setting up your voice companion...")
    
    # Step 1: Environment
    if not setup_environment():
        print("❌ Environment setup failed")
        sys.exit(1)
    
    # Step 2: CSM Access (optional)
    csm_status = test_csm_access()
    if any(csm_status.values()):
        print("✅ Some CSM models accessible")
    else:
        print("⚠️ CSM models not accessible (will use fallback)")
    
    # Step 3: Audio
    if setup_audio():
        print("✅ Audio system ready")
    else:
        print("⚠️ Audio issues detected")
    
    # Final status
    print_section("Setup Complete")
    print("🎉 Sonanima is ready!")
    print("\n🚀 To start:")
    print("   python sonanima.py")
    print("\n📚 For help:")
    print("   python sonanima.py --help")

if __name__ == "__main__":
    main()