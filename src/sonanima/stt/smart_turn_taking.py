#!/usr/bin/env python3
"""
Smart Turn-Taking System for Sonanima
Dual-stream processing with user feedback training
"""
import threading
import time
import queue
import numpy as np
import sounddevice as sd
import tempfile
import os
from typing import Optional, Callable, Dict, List
from dataclasses import dataclass
from pathlib import Path
import json
import pickle

@dataclass
class CutoffFeatures:
    """Features extracted at cutoff decision point"""
    pause_duration: float
    energy_trend: List[float]  # Last 1 second of energy levels
    pitch_trend: List[float]   # Pitch contour
    speech_rate: float         # Words per minute estimate
    trailing_silence: float   # Silence after last detected speech
    confidence_score: float   # VAD confidence

@dataclass
class FeedbackSample:
    """Training sample from user feedback"""
    features: CutoffFeatures
    label: str  # "good_cutoff", "too_early", "too_late"
    timestamp: float
    user_phrase: str

class SmartTurnTaking:
    """Intelligent turn-taking with user feedback learning"""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.vad_queue = queue.Queue()
        
        # Threading
        self.vad_thread = None
        self.recording_thread = None
        self.stop_event = threading.Event()
        
        # Turn-taking state
        self.user_speaking = False
        self.last_speech_time = 0
        self.cutoff_threshold = 1.5  # seconds of silence before cutoff
        self.min_speech_duration = 0.5  # minimum speech to consider
        
        # Feedback training
        self.feedback_samples: List[FeedbackSample] = []
        self.model_weights = self._load_or_init_weights()
        
        # Callbacks
        self.on_user_done: Optional[Callable[[str], None]] = None
        self.on_user_interrupted: Optional[Callable[[], None]] = None
        
        # Audio buffer for STT
        self.audio_buffer = []
        self.buffer_lock = threading.Lock()
        
    def _load_or_init_weights(self) -> Dict:
        """Load trained weights or initialize defaults"""
        weights_file = Path("data/turn_taking_weights.pkl")
        if weights_file.exists():
            try:
                with open(weights_file, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        
        # Default weights (will be trained with feedback)
        return {
            'pause_weight': 0.4,
            'energy_weight': 0.3,
            'pitch_weight': 0.2,
            'rate_weight': 0.1,
            'base_threshold': 1.5
        }
    
    def _save_weights(self):
        """Save trained weights"""
        weights_file = Path("data/turn_taking_weights.pkl")
        weights_file.parent.mkdir(exist_ok=True)
        with open(weights_file, 'wb') as f:
            pickle.dump(self.model_weights, f)
    
    def _extract_features(self, audio_chunk: np.ndarray) -> CutoffFeatures:
        """Extract features for cutoff decision"""
        # Energy analysis
        energy = np.sqrt(np.mean(audio_chunk ** 2))
        energy_trend = [energy]  # Simplified - would track over time
        
        # Pitch analysis (simplified)
        # In real implementation, use librosa or similar
        pitch_trend = [0.0]  # Placeholder
        
        # Speech rate estimation (simplified)
        speech_rate = 120.0  # Placeholder - would analyze actual speech
        
        # Silence detection
        silence_threshold = 0.01
        trailing_silence = 0.0
        for i in reversed(range(len(audio_chunk))):
            if abs(audio_chunk[i]) > silence_threshold:
                break
            trailing_silence += 1.0 / self.sample_rate
        
        return CutoffFeatures(
            pause_duration=trailing_silence,
            energy_trend=energy_trend,
            pitch_trend=pitch_trend,
            speech_rate=speech_rate,
            trailing_silence=trailing_silence,
            confidence_score=0.8  # Placeholder
        )
    
    def _should_cutoff(self, features: CutoffFeatures) -> bool:
        """Decide if we should cut off based on features and learned weights"""
        weights = self.model_weights
        
        # Weighted decision
        score = (
            features.pause_duration * weights['pause_weight'] +
            (2.0 - features.energy_trend[-1]) * weights['energy_weight'] +
            features.trailing_silence * weights['rate_weight']
        )
        
        threshold = weights['base_threshold']
        return score > threshold
    
    def _vad_worker(self):
        """Real-time VAD and cutoff detection thread"""
        print("🎤 VAD thread started")
        
        while not self.stop_event.is_set():
            try:
                # Get audio chunk from queue
                audio_chunk = self.vad_queue.get(timeout=0.1)
                
                # Extract features
                features = self._extract_features(audio_chunk)
                
                # Check if user is speaking
                energy = np.sqrt(np.mean(audio_chunk ** 2))
                is_speech = energy > 0.01  # Simple threshold
                
                if is_speech:
                    self.user_speaking = True
                    self.last_speech_time = time.time()
                else:
                    # Check for cutoff
                    silence_duration = time.time() - self.last_speech_time
                    if self.user_speaking and self._should_cutoff(features):
                        print(f"🔇 User done speaking (silence: {silence_duration:.1f}s)")
                        self._trigger_transcription()
                        self.user_speaking = False
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ VAD error: {e}")
    
    def _recording_worker(self):
        """Audio recording thread"""
        print("🎙️ Recording thread started")
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"⚠️ Audio status: {status}")
            
            # Send to VAD queue
            self.vad_queue.put(indata.copy().flatten())
            
            # Buffer for STT
            with self.buffer_lock:
                self.audio_buffer.extend(indata.flatten())
        
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                callback=audio_callback,
                blocksize=int(self.sample_rate * 0.1)  # 100ms chunks
            ):
                print("🎤 Recording started...")
                while not self.stop_event.is_set():
                    time.sleep(0.1)
        except Exception as e:
            print(f"❌ Recording error: {e}")
    
    def _trigger_transcription(self):
        """Trigger STT on buffered audio"""
        with self.buffer_lock:
            if len(self.audio_buffer) < self.sample_rate * 0.5:  # Less than 0.5s
                return
            
            # Save audio to temp file for STT
            audio_data = np.array(self.audio_buffer, dtype=np.float32)
            self.audio_buffer.clear()
        
        # Create temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Save audio (simplified - would use proper WAV format)
            # In real implementation, use soundfile or wave
            print(f"💾 Saving {len(audio_data)/self.sample_rate:.1f}s of audio for STT")
            
            # Trigger callback with temp file path
            if self.on_user_done:
                self.on_user_done(temp_path)
                
        except Exception as e:
            print(f"❌ Transcription trigger error: {e}")
        finally:
            # Cleanup temp file after use
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def start_listening(self):
        """Start the dual-stream turn-taking system"""
        if self.is_recording:
            print("⚠️ Already recording")
            return
        
        print("🚀 Starting smart turn-taking system...")
        self.is_recording = True
        self.stop_event.clear()
        
        # Start threads
        self.vad_thread = threading.Thread(target=self._vad_worker, daemon=True)
        self.recording_thread = threading.Thread(target=self._recording_worker, daemon=True)
        
        self.vad_thread.start()
        self.recording_thread.start()
        
        print("✅ Turn-taking system active")
    
    def stop_listening(self):
        """Stop the turn-taking system"""
        if not self.is_recording:
            return
        
        print("🛑 Stopping turn-taking system...")
        self.stop_event.set()
        self.is_recording = False
        
        # Wait for threads
        if self.vad_thread:
            self.vad_thread.join(timeout=1.0)
        if self.recording_thread:
            self.recording_thread.join(timeout=1.0)
        
        print("✅ Turn-taking system stopped")
    
    def add_feedback(self, feedback_type: str, user_phrase: str = ""):
        """Add user feedback for training"""
        if not hasattr(self, '_last_features'):
            print("⚠️ No recent cutoff to provide feedback on")
            return
        
        sample = FeedbackSample(
            features=self._last_features,
            label=feedback_type,
            timestamp=time.time(),
            user_phrase=user_phrase
        )
        
        self.feedback_samples.append(sample)
        print(f"📝 Added feedback: {feedback_type}")
        
        # Retrain if we have enough samples
        if len(self.feedback_samples) >= 10:
            self._retrain_model()
    
    def _retrain_model(self):
        """Retrain the cutoff model based on feedback"""
        print("🧠 Retraining turn-taking model...")
        
        # Simple weight adjustment based on feedback
        # In real implementation, use proper ML training
        
        good_samples = [s for s in self.feedback_samples if s.label == "good_cutoff"]
        early_samples = [s for s in self.feedback_samples if s.label == "too_early"]
        late_samples = [s for s in self.feedback_samples if s.label == "too_late"]
        
        # Adjust weights based on feedback patterns
        if len(early_samples) > len(late_samples):
            # Too many early cutoffs - increase threshold
            self.model_weights['base_threshold'] += 0.1
            print("📈 Increased cutoff threshold (too many early cutoffs)")
        elif len(late_samples) > len(early_samples):
            # Too many late cutoffs - decrease threshold  
            self.model_weights['base_threshold'] -= 0.1
            print("📉 Decreased cutoff threshold (too many late cutoffs)")
        
        # Save updated weights
        self._save_weights()
        
        # Clear old samples (keep recent ones)
        self.feedback_samples = self.feedback_samples[-20:]
        print("✅ Model retrained")


def test_smart_turn_taking():
    """Test the smart turn-taking system"""
    print("🧪 Testing Smart Turn-Taking System")
    print("=" * 50)
    
    turn_taking = SmartTurnTaking()
    
    def on_user_done(audio_path: str):
        print(f"🎯 User finished speaking - audio saved to: {audio_path}")
        print("   (This would trigger STT API call)")
        
        # Simulate user feedback
        feedback = input("Feedback (good/early/late): ").strip().lower()
        if feedback in ['early', 'late']:
            turn_taking.add_feedback(f"too_{feedback}")
        elif feedback == 'good':
            turn_taking.add_feedback("good_cutoff")
    
    turn_taking.on_user_done = on_user_done
    
    try:
        turn_taking.start_listening()
        
        print("\n🎤 Speak and test the turn-taking system!")
        print("💡 Say 'Hey, I wasn't done talking' to train the system")
        print("Press Ctrl+C to stop")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping test...")
    finally:
        turn_taking.stop_listening()


if __name__ == "__main__":
    test_smart_turn_taking() 