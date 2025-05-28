#!/usr/bin/env python3
"""
Whisper.cpp Streaming STT Engine
High accuracy real-time speech recognition using whisper.cpp
"""
import os
import time
import subprocess
import tempfile
import threading
import queue
import numpy as np
import sounddevice as sd
import soundfile as sf
from pathlib import Path
from typing import Optional, Callable


class WhisperCppStreaming:
    """High-accuracy streaming STT using whisper.cpp"""
    
    def __init__(self, model_name: str = "base.en"):
        """
        Initialize Whisper.cpp streaming engine
        
        Args:
            model_name: Model to use (base.en, small.en, medium.en, large-v3)
        """
        print(f"🎤 Initializing Whisper.cpp streaming with {model_name}...")
        
        self.model_name = model_name
        self.sample_rate = 16000
        
        # Find model file
        models_dir = Path(__file__).parent / "models" / "whisper-cpp"
        self.model_path = models_dir / f"ggml-{model_name}.bin"
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        
        # Check whisper-cli installation
        try:
            result = subprocess.run(['whisper-cli', '--help'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                raise RuntimeError("whisper-cli not working")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            raise RuntimeError("whisper-cli not installed or not in PATH")
        
        # Voice activity detection settings
        self.silence_threshold = 0.01
        self.min_chunk_duration = 1.0  # Minimum audio length for transcription
        
        # Voice calibration
        self.is_calibrated = False
        self.user_voice_profile = None
        
        print(f"✅ Whisper.cpp ready with {model_name} model")
    
    def _detect_voice_activity(self, audio_data: np.ndarray) -> bool:
        """Simple voice activity detection"""
        rms = np.sqrt(np.mean(audio_data ** 2))
        return rms > self.silence_threshold
    
    def transcribe_chunk(self, audio_data: np.ndarray) -> str:
        """Transcribe a single audio chunk using whisper.cpp"""
        if len(audio_data) < self.sample_rate * self.min_chunk_duration:
            return ""  # Too short
        
        try:
            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Write audio to file
            sf.write(temp_path, audio_data, self.sample_rate)
            
            # Run whisper-cli
            cmd = [
                'whisper-cli',
                '-m', str(self.model_path),
                '-f', temp_path,
                '--output-txt',
                '--no-timestamps',
                '--language', 'en',
                '--threads', '4',  # Use multiple threads for speed
                '--no-prints'  # Reduce output noise
            ]
            
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            elapsed = time.time() - start_time
            
            # Clean up temp file
            os.unlink(temp_path)
            
            if result.returncode == 0:
                # Extract text from output - whisper-cli outputs directly to stdout
                text = result.stdout.strip()
                
                # Clean up the output (remove timestamps and extra whitespace)
                lines = text.split('\n')
                clean_lines = []
                for line in lines:
                    line = line.strip()
                    # Skip empty lines and timestamp lines
                    if line and not line.startswith('[') and '-->' not in line:
                        clean_lines.append(line)
                
                final_text = ' '.join(clean_lines)
                
                if final_text:
                    return final_text.strip()
            else:
                pass  # Silent failure
            
            return ""
            
        except subprocess.TimeoutExpired:
            return ""
        except Exception as e:
            return ""
    
    def listen_streaming(
        self,
        max_duration: float = 30.0,
        chunk_duration: float = 0.5,
        silence_timeout: float = 2.0,
        overlap_duration: float = 0.2
    ) -> str:
        """
        Stream audio and transcribe in real-time with overlapping chunks
        
        Args:
            max_duration: Maximum recording time
            chunk_duration: Size of each audio chunk
            silence_timeout: How long to wait after speech ends
            overlap_duration: Overlap between chunks for better accuracy
        """
        print("🎙️ Listening...")
        
        try:
            audio_buffer = []
            speech_detected = False
            silence_start = None
            total_duration = 0
            
            while total_duration < max_duration:
                # Record chunk
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
                        speech_detected = True
                    
                    audio_buffer.append(chunk_flat)
                    silence_start = None
                    
                elif speech_detected:
                    # Add silence chunk but check for timeout
                    audio_buffer.append(chunk_flat)
                    
                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start > silence_timeout:
                        break
                
                total_duration += chunk_duration
            
            if not audio_buffer:
                return ""
            
            # Final transcription of complete audio
            full_audio = np.concatenate(audio_buffer)
            final_text = self.transcribe_chunk(full_audio)
            
            return final_text
            
        except Exception as e:
            return ""
    
    def test_transcription(self, duration: float = 3.0) -> bool:
        """Test the transcription system"""
        print(f"🎤 Testing Whisper.cpp for {duration} seconds...")
        print("💬 Please speak clearly...")
        
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
                text = self.transcribe_chunk(audio_data.flatten())
                
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
            print(f"❌ Test failed: {e}")
            return False
    
    def calibrate_voice(self) -> bool:
        """Calibrate the system to the user's voice"""
        print("🎯 Voice Calibration")
        print("Please read these sentences clearly:")
        
        calibration_sentences = [
            "Hello, my name is and I'm testing the voice system.",
            "The quick brown fox jumps over the lazy dog.",
            "I want to have a natural conversation with my AI companion.",
            "Please remember what I say and respond appropriately.",
            "This calibration helps improve speech recognition accuracy."
        ]
        
        calibration_audio = []
        
        for i, sentence in enumerate(calibration_sentences, 1):
            print(f"\n{i}/5: \"{sentence}\"")
            print("Press Enter when ready, then speak...")
            input()
            
            # Record calibration sentence
            print("🎤 Recording...")
            audio_data = sd.rec(
                int(5.0 * self.sample_rate),  # 5 seconds max
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32
            )
            sd.wait()
            
            # Check if we got audio
            avg_level = np.sqrt(np.mean(audio_data ** 2))
            if avg_level > self.silence_threshold:
                calibration_audio.append(audio_data.flatten())
                
                # Test transcription
                transcription = self.transcribe_chunk(audio_data.flatten())
                if transcription:
                    print(f"✅ Heard: \"{transcription}\"")
                else:
                    print("⚠️ No transcription - please speak louder")
            else:
                print("❌ No audio detected - skipping")
        
        if len(calibration_audio) >= 3:
            # Combine all calibration audio for voice profile
            self.user_voice_profile = np.concatenate(calibration_audio)
            self.is_calibrated = True
            
            # Adjust silence threshold based on user's voice
            voice_levels = [np.sqrt(np.mean(audio ** 2)) for audio in calibration_audio]
            avg_voice_level = np.mean(voice_levels)
            self.silence_threshold = max(0.005, avg_voice_level * 0.3)
            
            print(f"\n✅ Voice calibration complete!")
            print(f"📊 Adjusted silence threshold to: {self.silence_threshold:.3f}")
            return True
        else:
            print(f"\n❌ Calibration failed - need at least 3 good recordings")
            return False


if __name__ == "__main__":
    # Test the Whisper.cpp streaming engine
    print("🧪 Testing Whisper.cpp Streaming STT...")
    
    try:
        stt = WhisperCppStreaming("base.en")
        
        # Test basic transcription
        print("\n🔄 Testing basic transcription...")
        stt.test_transcription(5.0)
        
        # Test streaming
        print("\n🔄 Testing streaming transcription...")
        result = stt.listen_streaming(max_duration=15.0)
        print(f"Final result: {result}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    print("\n✅ Whisper.cpp streaming test complete!") 