#!/usr/bin/env python3
"""
Sonanima Text-to-Speech System
"""
import os
import subprocess
from typing import Optional

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    pyttsx3 = None
    HAS_PYTTSX3 = False

try:
    from .elevenlabs import SonanimaStreamingTTS
    HAS_ELEVENLABS = True
except ImportError:
    SonanimaStreamingTTS = None
    HAS_ELEVENLABS = False


class SonanimaTts:
    """Text-to-Speech engine with voice personality"""
    
    def __init__(self, provider: str = None, voice_name: str = "Rachel"):
        """
        Initialize TTS system
        
        Args:
            provider: TTS provider ('elevenlabs', 'pyttsx3', 'system'). If None, auto-detect
            voice_name: Preferred voice name (e.g., "Rachel", "Bella", "Samantha")
        """
        print("🎵 Initializing TTS system...")
        
        # Determine TTS provider priority: ElevenLabs > pyttsx3 > system
        if provider is None:
            if HAS_ELEVENLABS and os.getenv('ELEVENLABS_API_KEY'):
                self.provider = 'elevenlabs'
            elif HAS_PYTTSX3:
                self.provider = 'pyttsx3'
            else:
                self.provider = 'system'
        else:
            self.provider = provider
        
        self.voice_name = voice_name
        self.engine = None
        self.elevenlabs_tts = None
        
        if self.provider == 'elevenlabs':
            self._setup_elevenlabs()
        elif self.provider == 'pyttsx3':
            self._setup_pyttsx3()
        else:
            self._setup_system_voice()
        
        print("✅ TTS system ready")
    
    def _setup_elevenlabs(self):
        """Setup ElevenLabs streaming TTS"""
        if not HAS_ELEVENLABS:
            print("❌ ElevenLabs not available, falling back to pyttsx3")
            self.provider = 'pyttsx3'
            self._setup_pyttsx3()
            return
        
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key:
            print("⚠️ ELEVENLABS_API_KEY not found, falling back to pyttsx3")
            self.provider = 'pyttsx3'
            self._setup_pyttsx3()
            return
        
        try:
            self.elevenlabs_tts = SonanimaStreamingTTS()
            if self.elevenlabs_tts.setup():
                # Set voice if it's available
                if self.voice_name.lower() in self.elevenlabs_tts.voices:
                    self.elevenlabs_tts.current_voice = self.voice_name.lower()
                print(f"🎵 ElevenLabs streaming TTS ready with voice: {self.voice_name}")
            else:
                raise Exception("Setup failed")
        except Exception as e:
            print(f"❌ ElevenLabs setup failed: {e}")
            print("📢 Falling back to pyttsx3")
            self.provider = 'pyttsx3'
            self._setup_pyttsx3()
    
    def _setup_pyttsx3(self):
        """Setup pyttsx3 engine"""
        try:
            self.engine = pyttsx3.init()
            
            # Find and set preferred voice
            voices = self.engine.getProperty('voices')
            selected_voice = None
            
            for voice in voices:
                if self.voice_name.lower() in voice.name.lower():
                    selected_voice = voice
                    break
            
            if selected_voice:
                self.engine.setProperty('voice', selected_voice.id)
                print(f"🎵 Using voice: {selected_voice.name}")
            else:
                print(f"⚠️ Voice '{self.voice_name}' not found, using default")
            
            # Optimize for conversation
            self.engine.setProperty('rate', 160)  # Natural speed
            self.engine.setProperty('volume', 0.9)
            
            print("✅ pyttsx3 engine initialized")
            
        except Exception as e:
            print(f"❌ pyttsx3 setup failed: {e}")
            print("📢 Falling back to system voice")
            self.provider = 'system'
            self._setup_system_voice()
    
    def _setup_system_voice(self):
        """Setup system voice (macOS 'say' command)"""
        print("📢 Using system voice command")
        
        # Test if 'say' command is available
        try:
            result = subprocess.run(['say', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ System voice command available")
            else:
                print("⚠️ System voice command may not work properly")
        except Exception as e:
            print(f"⚠️ System voice test failed: {e}")
    
    def speak(self, text: str, emotion: str = "neutral") -> bool:
        """
        Speak text with emotional context
        
        Args:
            text: Text to speak
            emotion: Emotional context for voice modulation
            
        Returns:
            Success status
        """
        if not text.strip():
            return False
        
        try:
            if self.provider == 'elevenlabs' and self.elevenlabs_tts:
                # Use ElevenLabs streaming TTS
                return self.elevenlabs_tts.speak_streaming(text, emotion)
                
            elif self.provider == 'pyttsx3' and self.engine:
                # Apply emotional modulation
                self._apply_emotion(emotion)
                
                # Speak using pyttsx3
                self.engine.say(text)
                self.engine.runAndWait()
                
            else:
                # Use system voice with emotional parameters
                cmd = ['say']
                
                # Add voice parameter if specified
                if self.voice_name:
                    cmd.extend(['-v', self.voice_name])
                
                # Add emotional rate modification
                rate = self._get_emotional_rate(emotion)
                if rate:
                    cmd.extend(['-r', str(rate)])
                
                cmd.append(text)
                
                subprocess.run(cmd, check=True)
            
            return True
            
        except Exception as e:
            print(f"❌ TTS failed: {e}")
            return False
    
    def speak_streaming(self, text: str, emotion: str = "neutral") -> bool:
        """
        Speak text with streaming (if supported by provider)
        
        Args:
            text: Text to speak
            emotion: Emotional context for voice modulation
            
        Returns:
            Success status
        """
        if self.provider == 'elevenlabs' and self.elevenlabs_tts:
            return self.elevenlabs_tts.speak_streaming(text, emotion)
        else:
            # Fallback to regular speak for non-streaming providers
            return self.speak(text, emotion)
    
    def _speak_system(self, text: str, emotion: str = "neutral") -> bool:
        """
        Speak using system voice command
        
        Args:
            text: Text to speak
            emotion: Emotional context for voice modulation
            
        Returns:
            Success status
        """
        try:
            cmd = ['say']
            
            # Add voice parameter if specified
            if self.voice_name:
                cmd.extend(['-v', self.voice_name])
            
            # Add emotional rate modification
            rate = self._get_emotional_rate(emotion)
            if rate:
                cmd.extend(['-r', str(rate)])
            
            cmd.append(text)
            
            subprocess.run(cmd, check=True)
            return True
            
        except Exception as e:
            print(f"❌ System TTS failed: {e}")
            return False
    
    def _apply_emotion(self, emotion: str):
        """Apply emotional modulation to pyttsx3 engine"""
        if not self.engine:
            return
        
        # Emotional voice parameters
        emotion_params = {
            'joy': {'rate': 180, 'volume': 0.9},
            'excitement': {'rate': 200, 'volume': 1.0},
            'sadness': {'rate': 140, 'volume': 0.7},
            'anger': {'rate': 170, 'volume': 0.9},
            'fear': {'rate': 190, 'volume': 0.8},
            'calm': {'rate': 150, 'volume': 0.8},
            'empathy': {'rate': 155, 'volume': 0.8},
            'comfort': {'rate': 150, 'volume': 0.8},
            'warmth': {'rate': 160, 'volume': 0.9},
            'interest': {'rate': 165, 'volume': 0.9},
            'neutral': {'rate': 160, 'volume': 0.9}
        }
        
        params = emotion_params.get(emotion, emotion_params['neutral'])
        
        self.engine.setProperty('rate', params['rate'])
        self.engine.setProperty('volume', params['volume'])
    
    def _get_emotional_rate(self, emotion: str) -> Optional[int]:
        """Get speech rate for system voice based on emotion"""
        emotion_rates = {
            'joy': 180,
            'excitement': 200,
            'sadness': 140,
            'anger': 170,
            'fear': 190,
            'calm': 150,
            'empathy': 155,
            'comfort': 150,
            'warmth': 160,
            'interest': 165,
            'neutral': 160
        }
        
        return emotion_rates.get(emotion)
    
    def test_voice(self):
        """Test the TTS system"""
        test_messages = [
            ("Hello! I'm testing the text-to-speech system.", "neutral"),
            ("This is exciting! Everything seems to be working perfectly.", "joy"),
            ("I'm here to help and support you through anything.", "empathy"),
            ("Let me know if you have any questions about my voice.", "warmth")
        ]
        
        print("🧪 Testing TTS system...")
        
        for text, emotion in test_messages:
            print(f"🎵 Speaking ({emotion}): {text}")
            success = self.speak(text, emotion)
            if not success:
                print(f"❌ Failed to speak: {text}")
                return False
        
        print("✅ TTS test complete!")
        return True
    
    def get_available_voices(self) -> list:
        """Get list of available voices"""
        voices = []
        
        if self.provider == 'elevenlabs' and self.elevenlabs_tts:
            # ElevenLabs voices are handled by the streaming TTS
            return [{'name': self.voice_name, 'engine': 'elevenlabs'}]
        
        if self.provider == 'pyttsx3' and self.engine:
            try:
                pyttsx3_voices = self.engine.getProperty('voices')
                for voice in pyttsx3_voices:
                    voices.append({
                        'id': voice.id,
                        'name': voice.name,
                        'languages': getattr(voice, 'languages', []),
                        'engine': 'pyttsx3'
                    })
            except:
                pass
        
        # Add system voices (macOS)
        try:
            result = subprocess.run(['say', '-v', '?'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split()
                        if parts:
                            voices.append({
                                'name': parts[0],
                                'engine': 'system',
                                'description': ' '.join(parts[1:]) if len(parts) > 1 else ''
                            })
        except:
            pass
        
        return voices
    
    def close(self):
        """Clean up TTS resources"""
        if self.elevenlabs_tts:
            try:
                self.elevenlabs_tts.close()
            except:
                pass
        
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass 