#!/usr/bin/env python3
"""
Sonanima ElevenLabs Integration - Premium Voice Quality
"""
import os
import time
import requests
import tempfile
import subprocess
from typing import Optional, Dict, List
import json

class SonanimaElevenLabs:
    """Premium ElevenLabs TTS for Sonanima"""
    
    def __init__(self):
        self.api_key = os.getenv('ELEVENLABS_API_KEY')
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # Popular voice IDs (you can browse more at elevenlabs.io)
        self.voices = {
            'rachel': '21m00Tcm4TlvDq8ikWAM',      # Young female, warm
            'domi': 'AZnzlk1XvdvUeBnXmlld',        # Young female, strong  
            'bella': 'EXAVITQu4vr4xnSDxMaL',       # Young female, soft
            'antoni': 'ErXwobaYiN019PkySvjV',      # Young male, well-rounded
            'elli': 'MF3mGyEYCl7XYWbV9V6O',       # Young female, emotional
            'josh': 'TxGEqnHWrfWFTfGW9XjX',       # Young male, deep
            'arnold': 'VR6AewLTigWG4xSOukaG',      # Middle-aged male, crisp
            'adam': 'pNInz6obpgDQGcFmaJgB',       # Middle-aged male, deep
            'sam': 'yoZ06aMxZJJ28mfd3POQ',        # Young male, raspy
        }
        
        self.default_voice = 'rachel'  # Great for voice assistants
        
        if not self.api_key:
            print("⚠️  ElevenLabs API key not found!")
            print("🔑 Set your API key: export ELEVENLABS_API_KEY='your-key-here'")
            self.ready = False
        else:
            print("✅ ElevenLabs TTS ready!")
            self.ready = True
    
    def get_voices(self) -> Dict:
        """Get available voices from ElevenLabs"""
        if not self.ready:
            return {}
        
        try:
            headers = {'xi-api-key': self.api_key}
            response = requests.get(f"{self.base_url}/voices", headers=headers)
            response.raise_for_status()
            
            voices_data = response.json()
            print("🎭 Available voices:")
            for voice in voices_data.get('voices', []):
                print(f"  • {voice['name']}: {voice['voice_id']}")
            
            return voices_data
            
        except Exception as e:
            print(f"❌ Failed to get voices: {e}")
            return {}
    
    def speak(self, text: str, voice: str = None, emotion: str = "neutral", save_file: str = None) -> bool:
        """Generate speech with ElevenLabs"""
        if not self.ready:
            print("❌ ElevenLabs not ready - check API key")
            return False
        
        # Use default voice if none specified
        voice = voice or self.default_voice
        voice_id = self.voices.get(voice, voice)  # Allow direct voice_id too
        
        print(f"🎵 Sonanima ({voice}): '{text[:50]}{'...' if len(text) > 50 else ''}'")
        
        try:
            start_time = time.time()
            
            # Adjust voice settings based on emotion
            voice_settings = self._get_emotion_settings(emotion)
            
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            headers = {
                'Accept': 'audio/mpeg',
                'Content-Type': 'application/json',
                'xi-api-key': self.api_key
            }
            
            data = {
                'text': text,
                'model_id': 'eleven_monolingual_v1',
                'voice_settings': voice_settings
            }
            
            print(f"🚀 Generating with {emotion} emotion...")
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            # Save audio
            if save_file:
                output_path = save_file
            else:
                temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                output_path = temp_file.name
                temp_file.close()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            # Play immediately
            subprocess.run(['afplay', output_path], check=True)
            
            # Clean up temp file
            if not save_file:
                os.unlink(output_path)
            
            elapsed = time.time() - start_time
            print(f"✅ Generated in {elapsed:.2f}s")
            
            if save_file:
                print(f"💾 Saved to: {save_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ ElevenLabs generation failed: {e}")
            return False
    
    def _get_emotion_settings(self, emotion: str) -> Dict:
        """Get voice settings for different emotions"""
        emotion_map = {
            'neutral': {'stability': 0.5, 'similarity_boost': 0.5},
            'happy': {'stability': 0.7, 'similarity_boost': 0.8},
            'excited': {'stability': 0.3, 'similarity_boost': 0.9},
            'calm': {'stability': 0.8, 'similarity_boost': 0.3},
            'sad': {'stability': 0.6, 'similarity_boost': 0.2},
            'angry': {'stability': 0.2, 'similarity_boost': 0.7},
            'whisper': {'stability': 0.9, 'similarity_boost': 0.1},
        }
        
        return emotion_map.get(emotion, emotion_map['neutral'])
    
    def change_voice(self, voice_name: str):
        """Change the default voice"""
        if voice_name in self.voices:
            self.default_voice = voice_name
            print(f"🎭 Switched to {voice_name}")
        else:
            print(f"⚠️  Voice '{voice_name}' not found")
            print(f"Available: {list(self.voices.keys())}")
    


def quick_setup():
    """Quick setup and test"""
    print("🚀 Sonanima ElevenLabs Setup")
    print("=" * 40)
    
    # Check if API key is set
    if not os.getenv('ELEVENLABS_API_KEY'):
        print("❌ No API key found!")
        print("\n🔑 Setup Instructions:")
        print("1. Go to: https://elevenlabs.io/app/speech-synthesis")
        print("2. Sign up/login and get your API key")
        print("3. Run: export ELEVENLABS_API_KEY='your-key-here'")
        print("4. Run this script again")
        return False
    
    # Test the integration
    tts = SonanimaElevenLabs()
    
    if tts.ready:
        print("\n🧪 Quick test...")
        tts.speak("Hello! I'm Sonanima with premium ElevenLabs voice quality!")
        
        print("\n🎭 Available voices:")
        for name in tts.voices.keys():
            print(f"  • {name}")
        
        return True
    
    return False

if __name__ == "__main__":
    if quick_setup():
        print("\n💡 Next steps:")
        print("• Use SonanimaElevenLabs() in your main companion")
        print("• Try different voices with .change_voice('bella')")
        print("• Use emotions: .speak(text, emotion='happy')")
        print("• Test voices: .test_voices()") 