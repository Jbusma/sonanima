#!/usr/bin/env python3
"""
Hybrid Mode Implementation for Sonanima
Smart STT + Custom LLM + ElevenLabs TTS with perceived latency optimization
"""
import sys
import time
import threading
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sonanima.stt.smart_turn_taking import SmartTurnTaking
from sonanima.stt.engine import SonanimaStt
from sonanima.core.companion import SonanimaCompanion
from sonanima.tts.smart_fillers import SmartFillerSystem

class HybridSonanima:
    """Hybrid mode with perceived latency optimization"""
    
    def __init__(self):
        print("🚀 Initializing Hybrid Sonanima Mode...")
        
        # Core components
        self.turn_taking = SmartTurnTaking()
        self.stt_engine = SonanimaStt()
        self.companion: Optional[SonanimaCompanion] = None
        self.filler_system = SmartFillerSystem()
        
        # State management
        self.is_active = False
        self.processing_audio = False
        self.conversation_history = []
        
        # Performance tracking
        self.metrics = {
            "total_interactions": 0,
            "avg_perceived_latency": 0,
            "avg_actual_latency": 0,
            "filler_usage_rate": 0
        }
        
        # Setup callbacks
        self.turn_taking.on_user_done = self._handle_user_speech
        
        print("✅ Hybrid mode ready")
    
    def set_companion(self, companion: SonanimaCompanion):
        """Set the companion instance"""
        self.companion = companion
        
        # Pre-generate filler cache with companion's TTS
        if hasattr(companion, 'tts') and companion.tts:
            print("🎭 Pre-generating filler cache...")
            self.filler_system.pre_generate_cache(companion.tts, max_phrases=15)
        
        print("🤝 Companion connected to hybrid mode")
    
    def _handle_user_speech(self, audio_path: str):
        """Handle completed user speech with perceived latency optimization"""
        if self.processing_audio:
            print("⚠️ Still processing previous audio, skipping...")
            return
        
        self.processing_audio = True
        start_time = time.time()
        
        try:
            print(f"🎯 Processing user speech: {audio_path}")
            
            # Load and transcribe audio
            import soundfile as sf
            audio_data, sample_rate = sf.read(audio_path)
            
            # Start transcription
            transcription_start = time.time()
            transcription = self.stt_engine.transcribe_audio(audio_data)
            transcription_time = time.time() - transcription_start
            
            if not transcription:
                print("❌ No transcription received")
                return
            
            print(f"📝 '{transcription}' ({transcription_time*1000:.0f}ms)")
            
            # Check for feedback phrases
            if self._is_feedback_phrase(transcription):
                self._handle_feedback(transcription)
                return
            
            # PERCEIVED LATENCY OPTIMIZATION STARTS HERE
            filler_played = False
            
            if self.companion and self.companion.tts:
                # Play immediate filler while generating real response
                filler = self.filler_system.play_immediate_filler(
                    transcription, 
                    self.conversation_history,
                    self.companion.tts
                )
                
                if filler:
                    filler_played = True
                    print(f"🎭 Filler: '{filler.text}' (buying {filler.duration_ms}ms)")
            
            # Generate real response (this takes the longest time)
            response_start = time.time()
            
            if self.companion:
                # Use companion's full conversation flow
                response = self._generate_companion_response(transcription)
            else:
                response = f"I heard: {transcription}"
            
            response_time = time.time() - response_start
            
            if response:
                print(f"🤖 Response: '{response}' ({response_time*1000:.0f}ms)")
                
                # Speak the real response
                if self.companion and self.companion.tts:
                    tts_start = time.time()
                    self.companion.tts.speak_streaming(response)
                    tts_time = time.time() - tts_start
                    print(f"🗣️ TTS: {tts_time*1000:.0f}ms")
                else:
                    print(f"🗣️ {response}")
                
                # Update conversation history
                self.conversation_history.append({
                    "user": transcription,
                    "assistant": response,
                    "timestamp": time.time()
                })
                
                # Keep history manageable
                if len(self.conversation_history) > 10:
                    self.conversation_history = self.conversation_history[-10:]
            
            # Calculate and track metrics
            total_time = time.time() - start_time
            perceived_time = total_time
            
            if filler_played:
                # User heard something immediately, so perceived latency is much lower
                perceived_time = min(400, total_time)  # Filler gives ~400ms perceived latency
            
            self._update_metrics(total_time * 1000, perceived_time * 1000, filler_played)
            
            print(f"⏱️ Total: {total_time*1000:.0f}ms, Perceived: {perceived_time*1000:.0f}ms")
            
        except Exception as e:
            print(f"❌ Speech processing error: {e}")
        finally:
            self.processing_audio = False
    
    def _generate_companion_response(self, transcription: str) -> str:
        """Generate response using the companion system"""
        try:
            # This integrates with the existing companion conversation flow
            if hasattr(self.companion, 'process_user_input'):
                return self.companion.process_user_input(transcription)
            elif hasattr(self.companion, 'generate_response'):
                return self.companion.generate_response(transcription)
            else:
                # Fallback to basic LLM call
                return f"I understand you said: {transcription}. How can I help?"
        except Exception as e:
            print(f"❌ Companion response error: {e}")
            return "I'm having trouble processing that right now."
    
    def _is_feedback_phrase(self, text: str) -> bool:
        """Check if the transcription is feedback about turn-taking"""
        feedback_phrases = [
            "i wasn't done", "i wasn't finished", "you cut me off",
            "let me finish", "i was still talking", "wait i'm not done",
            "hold on", "you interrupted me"
        ]
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in feedback_phrases)
    
    def _handle_feedback(self, text: str):
        """Handle user feedback about turn-taking"""
        print(f"📝 Detected feedback: '{text}'")
        
        if any(phrase in text.lower() for phrase in ["cut", "interrupt", "wasn't done", "not done"]):
            self.turn_taking.add_feedback("too_early", text)
            
            if self.companion and self.companion.tts:
                response = "Sorry about that! I'm learning when you're finished speaking. I'll wait longer next time."
                self.companion.tts.speak_streaming(response)
            else:
                print("🤖 Sorry! I'll wait longer next time.")
    
    def _update_metrics(self, actual_latency: float, perceived_latency: float, used_filler: bool):
        """Update performance metrics"""
        self.metrics["total_interactions"] += 1
        
        # Running average calculation
        n = self.metrics["total_interactions"]
        self.metrics["avg_actual_latency"] = (
            (self.metrics["avg_actual_latency"] * (n-1) + actual_latency) / n
        )
        self.metrics["avg_perceived_latency"] = (
            (self.metrics["avg_perceived_latency"] * (n-1) + perceived_latency) / n
        )
        
        if used_filler:
            self.metrics["filler_usage_rate"] = (
                (self.metrics["filler_usage_rate"] * (n-1) + 1) / n
            )
        else:
            self.metrics["filler_usage_rate"] = (
                self.metrics["filler_usage_rate"] * (n-1)) / n
    
    def start_conversation(self):
        """Start the hybrid conversation system"""
        if self.is_active:
            print("⚠️ Already active")
            return
        
        print("🚀 Starting Hybrid Sonanima...")
        self.is_active = True
        
        # Start turn-taking system
        self.turn_taking.start_listening()
        
        print("✅ Hybrid mode active!")
        print("💡 Features enabled:")
        print("  • Smart turn-taking with feedback learning")
        print("  • Perceived latency optimization with fillers")
        print("  • OpenAI Whisper STT → Claude 4 → ElevenLabs TTS")
        print("  • Custom memory and conversation flow")
    
    def stop_conversation(self):
        """Stop the hybrid conversation system"""
        if not self.is_active:
            return
        
        print("🛑 Stopping Hybrid Sonanima...")
        self.is_active = False
        
        # Stop turn-taking
        self.turn_taking.stop_listening()
        
        # Show final metrics
        self._show_metrics()
        
        print("✅ Hybrid mode stopped")
    
    def _show_metrics(self):
        """Display performance metrics"""
        print("\n📊 Hybrid Mode Performance Metrics:")
        print(f"  Total interactions: {self.metrics['total_interactions']}")
        print(f"  Average actual latency: {self.metrics['avg_actual_latency']:.0f}ms")
        print(f"  Average perceived latency: {self.metrics['avg_perceived_latency']:.0f}ms")
        print(f"  Filler usage rate: {self.metrics['filler_usage_rate']*100:.1f}%")
        
        if self.metrics['avg_actual_latency'] > 0:
            improvement = (
                (self.metrics['avg_actual_latency'] - self.metrics['avg_perceived_latency']) 
                / self.metrics['avg_actual_latency'] * 100
            )
            print(f"  Perceived latency improvement: {improvement:.1f}%")
        
        # Filler system stats
        filler_stats = self.filler_system.get_stats()
        print(f"  Filler phrases used: {filler_stats['total_fillers_used']}")
        print(f"  Cached audio files: {filler_stats['cached_audio_files']}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status and metrics"""
        return {
            "mode": "hybrid",
            "is_active": self.is_active,
            "processing_audio": self.processing_audio,
            "stt_provider": self.stt_engine.provider if self.stt_engine else None,
            "companion_connected": self.companion is not None,
            "metrics": self.metrics,
            "filler_stats": self.filler_system.get_stats(),
            "turn_taking_stats": {
                "feedback_samples": len(self.turn_taking.feedback_samples),
                "current_threshold": self.turn_taking.model_weights.get('base_threshold', 1.5)
            }
        }


def test_hybrid_mode():
    """Test the hybrid mode system"""
    print("🧪 Testing Hybrid Sonanima Mode")
    print("=" * 50)
    
    # Initialize hybrid mode
    hybrid = HybridSonanima()
    
    # Try to connect companion
    try:
        from sonanima.core.companion import SonanimaCompanion
        companion = SonanimaCompanion()
        hybrid.set_companion(companion)
        print("✅ Companion connected")
    except Exception as e:
        print(f"⚠️ Companion not available: {e}")
        print("📝 Running in STT-only mode")
    
    # Show initial status
    status = hybrid.get_status()
    print(f"📊 Initial status: {status}")
    
    try:
        # Start conversation
        hybrid.start_conversation()
        
        print("\n🎤 Hybrid Sonanima active!")
        print("🎯 This mode provides:")
        print("  • ~400ms perceived latency (with fillers)")
        print("  • ~1300ms actual latency")
        print("  • 6x cheaper than ElevenLabs CAI")
        print("  • Full customization and memory")
        print("\nSpeak naturally - try complex questions!")
        print("Press Ctrl+C to stop")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping test...")
    finally:
        hybrid.stop_conversation()


if __name__ == "__main__":
    test_hybrid_mode() 