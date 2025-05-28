#!/usr/bin/env python3
"""
Sonanima Multi-Provider Speech-to-Text System
Optimized for low latency with local-first approach
"""
import os
import time
import json
import numpy as np
import sounddevice as sd
import soundfile as sf
from pathlib import Path
from typing import Optional, Callable

# Provider imports with fallbacks
try:
    import whisper
    HAS_OPENAI_WHISPER = True
except ImportError:
    whisper = None
    HAS_OPENAI_WHISPER = False

try:
    from .whisper_cpp_streaming import WhisperCppStreaming
    HAS_WHISPER_CPP = True
except ImportError:
    WhisperCppStreaming = None
    HAS_WHISPER_CPP = False

try:
    import vosk
    HAS_VOSK = True
except ImportError:
    vosk = None
    HAS_VOSK = False

try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError:
    sr = None
    HAS_SPEECH_RECOGNITION = False

try:
    import torch
    from faster_whisper import WhisperModel
    HAS_FASTER_WHISPER = True
except ImportError:
    torch = None
    WhisperModel = None
    HAS_FASTER_WHISPER = False


class OpenAIWhisperLocal:
    """High-accuracy local STT using OpenAI Whisper"""
    
    def __init__(self, model_size: str = "base"):
        """Initialize OpenAI Whisper local engine"""
        if not HAS_OPENAI_WHISPER:
            raise ImportError("OpenAI Whisper not installed: pip install git+https://github.com/openai/whisper.git")
        
        print(f"🎤 Loading OpenAI Whisper {model_size} model...")
        self.model_size = model_size
        self.sample_rate = 16000
        
        # Load the model
        try:
            self.model = whisper.load_model(model_size)
            print(f"✅ OpenAI Whisper {model_size} ready")
        except Exception as e:
            print(f"❌ Failed to load Whisper model: {e}")
            raise
        
        # Voice activity detection settings
        self.silence_threshold = 0.01
        self.min_chunk_duration = 1.0
    
    def transcribe_chunk(self, audio_data: np.ndarray) -> str:
        """Transcribe a single audio chunk using OpenAI Whisper"""
        if len(audio_data) < self.sample_rate * self.min_chunk_duration:
            return ""  # Too short
        
        try:
            # Whisper expects audio to be normalized to [-1, 1]
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize audio
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_data = audio_data / max_val
            
            # Pad or trim to 30 seconds (Whisper's expected input length)
            target_length = 30 * self.sample_rate
            if len(audio_data) > target_length:
                audio_data = audio_data[:target_length]
            else:
                audio_data = np.pad(audio_data, (0, target_length - len(audio_data)))
            
            # Transcribe with Whisper
            result = self.model.transcribe(
                audio_data,
                language="en",
                task="transcribe",
                fp16=False,  # Use fp32 for better compatibility
                verbose=False
            )
            
            text = result["text"].strip()
            return text
            
        except Exception as e:
            print(f"❌ Whisper transcription failed: {e}")
            return ""


class SonanimaStt:
    """Multi-provider Speech-to-Text engine optimized for low latency"""
    
    def __init__(self, provider: str = None, model_size: str = "small"):
        """
        Initialize STT with provider priority: vosk > speech_recognition > faster_whisper
        
        Args:
            provider: Force specific provider ('vosk', 'speech_recognition', 'faster_whisper')
            model_size: Model size for Whisper (tiny, base, small, medium)
        """
        print(f"🎤 Initializing Multi-Provider STT...")
        
        # Determine provider priority: openai_whisper > whisper_cpp > vosk > speech_recognition > faster_whisper
        if provider is None:
            if HAS_OPENAI_WHISPER:
                self.provider = 'openai_whisper'
            elif HAS_WHISPER_CPP:
                self.provider = 'whisper_cpp'
            elif HAS_VOSK:
                self.provider = 'vosk'
            elif HAS_SPEECH_RECOGNITION:
                self.provider = 'speech_recognition'
            elif HAS_FASTER_WHISPER:
                self.provider = 'faster_whisper'
            else:
                raise RuntimeError("No STT providers available!")
        else:
            self.provider = provider
        
        # Audio settings
        self.sample_rate = 16000  # Standard for most STT engines
        
        # Voice activity detection settings (optimized for speed)
        self.silence_threshold = 0.01
        self.speech_threshold = 0.02
        
        # Initialize the selected provider
        self.engine = None
        if self.provider == 'openai_whisper':
            self._setup_openai_whisper(model_size)
        elif self.provider == 'whisper_cpp':
            self._setup_whisper_cpp(model_size)
        elif self.provider == 'vosk':
            self._setup_vosk()
        elif self.provider == 'speech_recognition':
            self._setup_speech_recognition()
        elif self.provider == 'faster_whisper':
            self._setup_faster_whisper(model_size)
        
        print(f"✅ STT ready with {self.provider} provider")
    
    def _setup_openai_whisper(self, model_size: str):
        """Setup OpenAI Whisper for highest accuracy local STT"""
        if not HAS_OPENAI_WHISPER:
            raise RuntimeError("OpenAI Whisper not available")
        
        self.engine = OpenAIWhisperLocal(model_size)
        print("🚀 OpenAI Whisper ready (highest accuracy local)")
    
    def _setup_whisper_cpp(self, model_size: str):
        """Setup Whisper.cpp for highest accuracy streaming"""
        if not HAS_WHISPER_CPP:
            raise RuntimeError("Whisper.cpp not available")
        
        # Map model sizes to whisper.cpp model names
        model_map = {
            'tiny': 'tiny.en',
            'base': 'base.en', 
            'small': 'small.en',
            'medium': 'medium.en',
            'large': 'large-v3'
        }
        
        model_name = model_map.get(model_size, 'base.en')
        self.engine = WhisperCppStreaming(model_name)
        print("🚀 Whisper.cpp ready (highest accuracy)")
    
    def _setup_vosk(self):
        """Setup Vosk for ultra-fast local STT"""
        if not HAS_VOSK:
            raise RuntimeError("Vosk not available")
        
        # Download model if needed
        model_dir = Path(__file__).parent / "models" / "vosk"
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to find existing model or download small one
        model_path = None
        for model_name in ["vosk-model-small-en-us-0.15", "vosk-model-en-us-0.22"]:
            potential_path = model_dir / model_name
            if potential_path.exists():
                model_path = str(potential_path)
                break
        
        if not model_path:
            print("📥 Downloading Vosk model (first time only)...")
            # For now, user needs to download manually
            print("💡 Please download a Vosk model:")
            print("   wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip")
            print(f"   unzip to {model_dir}/")
            raise RuntimeError("Vosk model not found - please download manually")
        
        self.engine = vosk.Model(model_path)
        self.recognizer = vosk.KaldiRecognizer(self.engine, self.sample_rate)
        print("🚀 Vosk ready (ultra-fast local)")
    
    def _setup_speech_recognition(self):
        """Setup SpeechRecognition with multiple backends"""
        if not HAS_SPEECH_RECOGNITION:
            raise RuntimeError("SpeechRecognition not available")
        
        self.engine = sr.Recognizer()
        self.microphone = sr.Microphone(sample_rate=self.sample_rate)
        
        # Optimize for speed
        self.engine.energy_threshold = 300
        self.engine.dynamic_energy_threshold = True
        self.engine.pause_threshold = 0.5  # Shorter pause for faster response
        
        print("⚡ SpeechRecognition ready (fast local)")
    
    def _setup_faster_whisper(self, model_size: str):
        """Setup Faster-Whisper as fallback"""
        if not HAS_FASTER_WHISPER:
            raise RuntimeError("Faster-Whisper not available")
        
        # Use CPU for reliability (MPS has issues)
        device = "cpu"
        compute_type = "int8"  # Fastest on CPU
        
        models_dir = Path(__file__).parent / "models" / "whisper"
        models_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            self.engine = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
                download_root=str(models_dir)
            )
            print(f"🤖 Faster-Whisper ready ({model_size} model, CPU)")
        except Exception as e:
            print(f"❌ Whisper setup failed: {e}")
            raise
    
    def _detect_voice_activity(self, audio_data: np.ndarray) -> bool:
        """Fast voice activity detection"""
        rms = np.sqrt(np.mean(audio_data ** 2))
        return rms > self.silence_threshold
    
    def _preprocess_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Minimal preprocessing for speed"""
        # Handle empty audio
        if len(audio_data) == 0:
            return audio_data
        
        # Just normalize to prevent clipping
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            audio_data = audio_data / max_val * 0.95
        return audio_data
    
    def transcribe_vosk(self, audio_data: np.ndarray) -> str:
        """Ultra-fast transcription with Vosk"""
        try:
            # Convert to bytes
            audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
            
            # Process audio
            if self.recognizer.AcceptWaveform(audio_bytes):
                result = json.loads(self.recognizer.Result())
                return result.get('text', '').strip()
            else:
                # Get partial result
                partial = json.loads(self.recognizer.PartialResult())
                return partial.get('partial', '').strip()
                
        except Exception as e:
            print(f"❌ Vosk transcription failed: {e}")
            return ""
    
    def transcribe_speech_recognition(self, audio_data: np.ndarray) -> str:
        """Fast transcription with SpeechRecognition"""
        try:
            # Create AudioData object
            audio_data_sr = sr.AudioData(
                (audio_data * 32767).astype(np.int16).tobytes(),
                self.sample_rate,
                2  # 16-bit
            )
            
            # Try multiple engines in order of speed
            try:
                # PocketSphinx (fastest, offline)
                return self.engine.recognize_sphinx(audio_data_sr)
            except:
                try:
                    # Google (online, accurate)
                    return self.engine.recognize_google(audio_data_sr)
                except:
                    return ""
                    
        except Exception as e:
            print(f"❌ SpeechRecognition failed: {e}")
            return ""
    
    def transcribe_faster_whisper(self, audio_data: np.ndarray) -> str:
        """Fallback transcription with Faster-Whisper"""
        try:
            # Save temporary file
            temp_path = "temp_whisper_audio.wav"
            sf.write(temp_path, audio_data, self.sample_rate)
            
            # Transcribe
            segments, info = self.engine.transcribe(
                temp_path,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=300)
            )
            
            text = " ".join([segment.text.strip() for segment in segments])
            
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return text.strip()
            
        except Exception as e:
            print(f"❌ Faster-Whisper transcription failed: {e}")
            return ""
    
    def transcribe_audio(self, audio_data: np.ndarray) -> str:
        """Transcribe audio using the configured provider"""
        start_time = time.time()
        
        # Handle empty audio
        if len(audio_data) == 0:
            return ""
        
        # Preprocess audio
        audio_data = self._preprocess_audio(audio_data)
        
        # Transcribe based on provider
        if self.provider == 'openai_whisper':
            text = self.engine.transcribe_chunk(audio_data)
        elif self.provider == 'whisper_cpp':
            text = self.engine.transcribe_chunk(audio_data)
        elif self.provider == 'vosk':
            text = self.transcribe_vosk(audio_data)
        elif self.provider == 'speech_recognition':
            text = self.transcribe_speech_recognition(audio_data)
        elif self.provider == 'faster_whisper':
            text = self.transcribe_faster_whisper(audio_data)
        else:
            text = ""
        
        elapsed = time.time() - start_time
        if text:
            print(f"⚡ Transcribed in {elapsed:.2f}s: {text}")
        
        return text
    
    def listen_realtime(
        self,
        max_duration: float = 30.0,
        chunk_duration: float = 0.3,  # Smaller chunks for faster response
        silence_timeout: float = 1.5,  # Shorter timeout
        min_speech_chunks: int = 2
    ) -> str:
        """Real-time voice activity detection and transcription"""
        print("🎙️ Listening... (speak now)")
        
        try:
            audio_chunks = []
            speech_detected = False
            silence_start = None
            total_duration = 0
            
            while total_duration < max_duration:
                # Record small chunk
                chunk = sd.rec(
                    int(chunk_duration * self.sample_rate),
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype=np.float32
                )
                sd.wait()
                
                chunk_flat = chunk.flatten()
                has_voice = self._detect_voice_activity(chunk_flat)
                
                if has_voice:
                    if not speech_detected:
                        print("🎤 Speech detected...")
                        speech_detected = True
                    
                    audio_chunks.append(chunk_flat)
                    silence_start = None
                    
                elif speech_detected:
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > silence_timeout:
                        print("🔇 Speech ended")
                        break
                    
                    audio_chunks.append(chunk_flat)
                
                total_duration += chunk_duration
                
                # Real-time feedback
                if speech_detected:
                    print(".", end="", flush=True)
            
            print()  # New line
            
            if not audio_chunks:
                print("🔇 No speech detected")
                return ""
            
            # Check minimum speech requirement
            speech_chunks = sum(1 for chunk in audio_chunks if self._detect_voice_activity(chunk))
            if speech_chunks < min_speech_chunks:
                print(f"🔇 Too little speech detected ({speech_chunks} chunks)")
                return ""
            
            # Combine and transcribe
            full_audio = np.concatenate(audio_chunks)
            return self.transcribe_audio(full_audio)
            
        except Exception as e:
            print(f"❌ Real-time recording failed: {e}")
            return ""
    
    def listen_once(self, duration: float = 5.0, **kwargs) -> str:
        """Legacy method - redirects to realtime"""
        return self.listen_realtime(max_duration=duration, **kwargs)
    
    def test_microphone(self, duration: float = 3.0) -> bool:
        """Test microphone and transcription"""
        print(f"🎤 Testing microphone for {duration} seconds...")
        print("💬 Please speak something...")
        
        try:
            # Record test audio
            audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32
            )
            sd.wait()
            
            # Check audio levels
            max_level = np.max(np.abs(audio_data))
            avg_level = np.sqrt(np.mean(audio_data ** 2))
            
            print(f"📊 Audio stats:")
            print(f"   Max level: {max_level:.3f}")
            print(f"   Average level: {avg_level:.3f}")
            print(f"   Voice detected: {'✅' if avg_level > self.silence_threshold else '❌'}")
            
            if avg_level > self.silence_threshold:
                print("🔄 Testing transcription...")
                text = self.transcribe_audio(audio_data.flatten())
                
                if text:
                    print(f"✅ Transcription: '{text}'")
                    return True
                else:
                    print("❌ No transcription produced")
                    return False
            else:
                print("❌ Audio level too low")
                return False
                
        except Exception as e:
            print(f"❌ Microphone test failed: {e}")
            return False
    
    def close(self):
        """Clean up resources"""
        pass


if __name__ == "__main__":
    # Test the multi-provider STT system
    print("🧪 Testing Multi-Provider STT...")
    
    # Test each available provider
    providers = []
    if HAS_OPENAI_WHISPER:
        providers.append('openai_whisper')
    if HAS_WHISPER_CPP:
        providers.append('whisper_cpp')
    if HAS_VOSK:
        providers.append('vosk')
    if HAS_SPEECH_RECOGNITION:
        providers.append('speech_recognition')
    if HAS_FASTER_WHISPER:
        providers.append('faster_whisper')
    
    print(f"Available providers: {providers}")
    
    for provider in providers:
        try:
            print(f"\n🔄 Testing {provider}...")
            stt = SonanimaStt(provider=provider)
            stt.test_microphone(3.0)
        except Exception as e:
            print(f"❌ {provider} failed: {e}")
    
    print("\n✅ Multi-provider STT test complete!") 