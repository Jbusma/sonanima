#!/usr/bin/env python3
"""
Fast Local TTS Options for Sonanima
"""
import time
import torch
import torchaudio
from pathlib import Path

class FastLocalTTS:
    """Fast local TTS alternatives"""
    
    def __init__(self):
        self.engines = {}
        self._setup_engines()
    
    def _setup_engines(self):
        """Setup various fast TTS engines"""
        print("🚀 Setting up fast TTS engines...")
        
        # Option 1: Enhanced pyttsx3 (fastest)
        try:
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            if voices:
                engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)
            engine.setProperty('rate', 200)
            engine.setProperty('volume', 0.8)
            self.engines['pyttsx3'] = engine
            print("✅ pyttsx3 ready (fastest)")
        except:
            print("⚠️  pyttsx3 not available")
        
        # Option 2: System say command (fast, macOS only)
        try:
            import subprocess
            subprocess.run(['say', '--version'], check=True, capture_output=True)
            self.engines['system_say'] = True
            print("✅ macOS say command ready (fast)")
        except:
            print("⚠️  macOS say not available")
        
        # Option 3: Coqui TTS (medium speed, good quality)
        try:
            from TTS.api import TTS
            tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
            self.engines['coqui'] = tts
            print("✅ Coqui TTS ready (medium speed)")
        except Exception as e:
            print(f"⚠️  Coqui TTS not available: {e}")
    
    def speak_fast(self, text: str, engine: str = "pyttsx3"):
        """Fast speech generation"""
        start_time = time.time()
        
        if engine == "pyttsx3" and "pyttsx3" in self.engines:
            self.engines['pyttsx3'].say(text)
            self.engines['pyttsx3'].runAndWait()
            
        elif engine == "system_say" and "system_say" in self.engines:
            import subprocess
            subprocess.run(['say', text], check=True)
            
        elif engine == "coqui" and "coqui" in self.engines:
            output_path = "temp_coqui.wav"
            self.engines['coqui'].tts_to_file(text=text, file_path=output_path)
            # Play the file
            import subprocess
            subprocess.run(['afplay', output_path], check=True)
            
        elapsed = time.time() - start_time
        print(f"⚡ {engine}: {elapsed:.2f}s")
        return elapsed

def speed_comparison():
    """Compare different TTS speeds"""
    print("🏃‍♂️ TTS Speed Comparison")
    print("=" * 40)
    
    fast_tts = FastLocalTTS()
    test_text = "Hello! This is a speed test for Sonanima's voice."
    
    print(f"\nTesting: '{test_text}'\n")
    
    # Test available engines
    for engine in ['pyttsx3', 'system_say', 'coqui']:
        if engine in fast_tts.engines:
            print(f"Testing {engine}...")
            try:
                elapsed = fast_tts.speak_fast(test_text, engine)
                print(f"✅ {engine}: {elapsed:.2f}s\n")
            except Exception as e:
                print(f"❌ {engine} failed: {e}\n")
    
    print("🎯 Recommendation: Use pyttsx3 or system say for real-time conversation")

if __name__ == "__main__":
    speed_comparison() 