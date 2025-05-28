#!/usr/bin/env python3
"""
Quick CSM TTS Test - Let's hear Sonanima's voice!
"""
import sys
import os
sys.path.append('csm')

try:
    from generator import load_csm_1b
    import torchaudio
    import torch
    import subprocess
    
    print("🎤 Testing CSM Voice...")
    
    # Set device - Apple Silicon M1/M2/M3 use MPS
    if torch.backends.mps.is_available():
        device = "mps"
        print("🍎 Using Apple Silicon GPU (MPS)")
    elif torch.cuda.is_available():
        device = "cuda"
        print("🟢 Using NVIDIA GPU (CUDA)")
    else:
        device = "cpu"
        print("⚠️  Using CPU - will be slower")
    
    print(f"📥 Loading CSM-1B model on {device}...")
    generator = load_csm_1b(device=device)
    print("✅ CSM loaded successfully!")
    
    # Test message
    test_text = "Hello! I'm Sonanima, your voice companion. It's wonderful to meet you."
    
    print(f"🎵 Generating speech: '{test_text}'")
    
    # Generate speech
    audio = generator.generate(
        text=test_text,
        speaker=0,  # Sonanima's voice
        context=[],  # No conversation context yet
        max_audio_length_ms=10_000,
    )
    
    # Save audio
    output_file = "test_sonanima_voice.wav"
    torchaudio.save(output_file, audio.unsqueeze(0).cpu(), generator.sample_rate)
    print(f"💾 Saved audio to: {output_file}")
    
    # Play audio on macOS
    print("🔊 Playing audio...")
    subprocess.run(['afplay', output_file], check=True)
    
    print("🎉 CSM TTS test successful! Sonanima can speak!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're in the venv: source venv/bin/activate")
    
except Exception as e:
    print(f"❌ Error: {e}")
    if "401" in str(e) or "access" in str(e).lower():
        print("🔑 Please run: huggingface-cli login")
        print("   You need access to Llama-3.2-1B and CSM-1B models")
    else:
        print("💡 Check your setup and model access") 