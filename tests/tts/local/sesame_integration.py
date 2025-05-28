#!/usr/bin/env python3
"""
Sonanima Sesame CSM Integration - Production Ready
"""
import os
import sys
import torch
import torchaudio
from pathlib import Path
from typing import Optional, List
import traceback

# Add models directory
MODELS_DIR = Path(__file__).parent / "models"
sys.path.insert(0, str(MODELS_DIR))

class SonanimaCSM:
    """Production Sesame CSM integration for Sonanima"""
    
    def __init__(self, speaker_id: int = 0):
        """
        Initialize Sonanima's voice with Sesame CSM
        
        Args:
            speaker_id: Default speaker (0 or 1)
        """
        self.speaker_id = speaker_id
        self.sample_rate = 24000
        self.generator = None
        self.ready = False
        
        print("🎤 Initializing Sonanima's Sesame Voice...")
        self._setup()
    
    def _setup(self):
        """Set up CSM components"""
        try:
            # Set environment
            os.environ['LOCAL_LLAMA_PATH'] = "/Users/mac/.llama/checkpoints/Llama3.2-1B"
            os.environ['TOKENIZERS_PARALLELISM'] = "false"  # Suppress warnings
            
            # Device setup
            if torch.backends.mps.is_available():
                self.device = "mps"
                print("🍎 Using Apple Silicon acceleration")
            elif torch.cuda.is_available():
                self.device = "cuda"
                print("🟢 Using NVIDIA GPU acceleration")
            else:
                self.device = "cpu"
                print("💻 Using CPU")
            
            # Load CSM components
            from models import Model
            from generator import Generator
            
            print("📥 Loading Sesame CSM-1B...")
            model = Model.from_pretrained("sesame/csm-1b")
            model.to(device=self.device, dtype=torch.bfloat16)
            
            self.generator = Generator(model)
            self.ready = True
            
            print("✅ Sonanima's voice is ready!")
            
        except Exception as e:
            print(f"⚠️  CSM setup failed: {e}")
            print("🔄 Falling back to basic TTS...")
            self._setup_fallback()
    
    def _setup_fallback(self):
        """Setup fallback TTS"""
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            
            # Configure voice
            voices = self.tts_engine.getProperty('voices')
            if voices and len(voices) > 1:
                # Use a pleasant voice (usually index 1 on macOS)
                self.tts_engine.setProperty('voice', voices[1].id)
            
            self.tts_engine.setProperty('rate', 180)  # Comfortable speed
            self.tts_engine.setProperty('volume', 0.8)
            
            print("✅ Fallback TTS ready")
            
        except Exception as e:
            print(f"❌ Fallback TTS failed: {e}")
            self.tts_engine = None
    
    def speak(self, text: str, emotion: str = "neutral", save_audio: bool = False) -> Optional[str]:
        """
        Make Sonanima speak with emotion
        
        Args:
            text: What to say
            emotion: Emotion hint (neutral, happy, excited, calm)
            save_audio: Whether to save audio file
            
        Returns:
            Path to saved audio file if save_audio=True
        """
        if not text.strip():
            return None
        
        print(f"🎵 Sonanima: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        
        if self.ready and self.generator:
            return self._speak_with_csm(text, emotion, save_audio)
        else:
            self._speak_with_fallback(text, emotion)
            return None
    
    def _speak_with_csm(self, text: str, emotion: str, save_audio: bool) -> Optional[str]:
        """Generate speech with CSM"""
        try:
            # Adjust generation parameters based on emotion
            temperature, topk = self._get_emotion_params(emotion)
            
            # Generate speech
            audio = self.generator.generate(
                text=text,
                speaker=self.speaker_id,
                context=[],  # Could add conversation history here
                max_audio_length_ms=20_000,  # 20 seconds max
                temperature=temperature,
                topk=topk
            )
            
            # Play immediately
            self._play_audio_tensor(audio)
            
            # Save if requested
            if save_audio:
                filename = f"sonanima_speech_{hash(text) % 10000}.wav"
                torchaudio.save(filename, audio.unsqueeze(0).cpu(), self.sample_rate)
                print(f"💾 Saved: {filename}")
                return filename
            
            return None
            
        except Exception as e:
            print(f"⚠️  CSM speech failed: {e}")
            self._speak_with_fallback(text, emotion)
            return None
    
    def _speak_with_fallback(self, text: str, emotion: str):
        """Fallback speech with pyttsx3"""
        if not self.tts_engine:
            print(f"🔊 Sonanima would say: {text}")
            return
        
        # Adjust voice for emotion
        rate = 180
        volume = 0.8
        
        if emotion == "excited":
            rate = 200
            volume = 0.9
        elif emotion == "calm":
            rate = 160
            volume = 0.7
        elif emotion == "happy":
            rate = 190
            volume = 0.85
        
        self.tts_engine.setProperty('rate', rate)
        self.tts_engine.setProperty('volume', volume)
        
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
    
    def _get_emotion_params(self, emotion: str) -> tuple:
        """Get generation parameters for emotions"""
        emotion_map = {
            "neutral": (0.9, 50),
            "happy": (1.0, 60),     # More varied
            "excited": (1.1, 70),   # Very expressive
            "calm": (0.7, 40),      # More controlled
        }
        return emotion_map.get(emotion, (0.9, 50))
    
    def _play_audio_tensor(self, audio: torch.Tensor):
        """Play audio tensor immediately"""
        try:
            import tempfile
            import subprocess
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
                torchaudio.save(temp_path, audio.unsqueeze(0).cpu(), self.sample_rate)
            
            # Play with afplay (macOS)
            subprocess.run(['afplay', temp_path], check=True)
            
            # Clean up
            os.unlink(temp_path)
            
        except Exception as e:
            print(f"⚠️  Audio playback failed: {e}")
    
    def change_speaker(self, speaker_id: int):
        """Change speaker voice (0 or 1)"""
        if speaker_id in [0, 1]:
            self.speaker_id = speaker_id
            print(f"🎭 Switched to speaker {speaker_id}")
        else:
            print("⚠️  Speaker ID must be 0 or 1")
    
    def test_voice(self):
        """Test Sonanima's voice with different emotions"""
        print("🧪 Testing Sonanima's voice...")
        
        test_phrases = [
            ("Hello! I'm Sonanima, your voice companion.", "happy"),
            ("I'm here to help you with whatever you need.", "neutral"),
            ("This is so exciting! We can have natural conversations now!", "excited"),
            ("Let me think about that for a moment...", "calm"),
        ]
        
        for text, emotion in test_phrases:
            print(f"\n🎭 Testing {emotion} emotion:")
            self.speak(text, emotion=emotion)
            
            # Brief pause between tests
            import time
            time.sleep(1)
        
        print("\n🎉 Voice test complete!")

# Convenience function for quick use
def create_sonanima_voice(speaker_id: int = 0) -> SonanimaCSM:
    """Create and return a Sonanima voice instance"""
    return SonanimaCSM(speaker_id=speaker_id)

if __name__ == "__main__":
    # Test the integration
    voice = create_sonanima_voice(speaker_id=0)
    voice.test_voice() 