#!/usr/bin/env python3
"""
Smart STT Integration for Sonanima
Combines smart turn-taking with existing STT engine and companion system
"""
import sys
import time
import threading
from pathlib import Path
from typing import Optional, Callable

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sonanima.stt.smart_turn_taking import SmartTurnTaking
from sonanima.stt.engine import SonanimaStt
from sonanima.core.companion import SonanimaCompanion

class SmartSonanimaSTT:
    """Smart STT integration with turn-taking and feedback learning"""
    
    def __init__(self):
        print("🧠 Initializing Smart Sonanima STT...")
        
        # Initialize components
        self.turn_taking = SmartTurnTaking()
        self.stt_engine = SonanimaStt()
        self.companion: Optional[SonanimaCompanion] = None
        
        # State
        self.is_active = False
        self.processing_audio = False
        
        # Setup callbacks
        self.turn_taking.on_user_done = self._handle_user_speech
        
        print("✅ Smart STT system ready")
    
    def set_companion(self, companion: SonanimaCompanion):
        """Set the companion instance for full integration"""
        self.companion = companion
        print("🤝 Companion connected to smart STT")
    
    def _handle_user_speech(self, audio_path: str):
        """Handle completed user speech"""
        if self.processing_audio:
            print("⚠️ Still processing previous audio, skipping...")
            return
        
        self.processing_audio = True
        
        try:
            print(f"🎯 Processing user speech from: {audio_path}")
            
            # Load and transcribe audio
            import soundfile as sf
            audio_data, sample_rate = sf.read(audio_path)
            
            print("🔄 Transcribing...")
            start_time = time.time()
            transcription = self.stt_engine.transcribe_audio(audio_data)
            transcription_time = time.time() - start_time
            
            if transcription:
                print(f"📝 '{transcription}' ({transcription_time*1000:.0f}ms)")
                
                # Check for feedback phrases
                if self._is_feedback_phrase(transcription):
                    self._handle_feedback(transcription)
                elif self.companion:
                    # Send to companion for response
                    self._send_to_companion(transcription)
                else:
                    print("💭 No companion connected - transcription only")
            else:
                print("❌ No transcription received")
                
        except Exception as e:
            print(f"❌ Speech processing error: {e}")
        finally:
            self.processing_audio = False
    
    def _is_feedback_phrase(self, text: str) -> bool:
        """Check if the transcription is feedback about turn-taking"""
        feedback_phrases = [
            "i wasn't done",
            "i wasn't finished",
            "you cut me off",
            "let me finish",
            "i was still talking",
            "wait i'm not done",
            "hold on",
            "you interrupted me"
        ]
        
        text_lower = text.lower()
        return any(phrase in text_lower for phrase in feedback_phrases)
    
    def _handle_feedback(self, text: str):
        """Handle user feedback about turn-taking"""
        print(f"📝 Detected feedback: '{text}'")
        
        # Determine feedback type
        if any(phrase in text.lower() for phrase in ["cut", "interrupt", "wasn't done", "not done"]):
            self.turn_taking.add_feedback("too_early", text)
            
            # Acknowledge the feedback
            if self.companion:
                response = "Sorry about that! I'm learning when you're finished speaking. I'll wait longer next time."
                self.companion.speak_response(response)
            else:
                print("🤖 Sorry! I'll wait longer next time.")
        else:
            # Generic feedback
            self.turn_taking.add_feedback("too_early", text)
    
    def _send_to_companion(self, transcription: str):
        """Send transcription to companion for processing"""
        try:
            # This would integrate with the companion's conversation flow
            print(f"🤖 Sending to companion: '{transcription}'")
            
            # For now, just call the companion's process method
            # In full integration, this would be part of the conversation loop
            if hasattr(self.companion, 'process_user_input'):
                response = self.companion.process_user_input(transcription)
                if response:
                    print(f"🗣️ Companion response: '{response}'")
            else:
                print("⚠️ Companion doesn't have process_user_input method")
                
        except Exception as e:
            print(f"❌ Companion integration error: {e}")
    
    def start_conversation(self):
        """Start the smart conversation system"""
        if self.is_active:
            print("⚠️ Already active")
            return
        
        print("🚀 Starting smart conversation system...")
        self.is_active = True
        
        # Start turn-taking
        self.turn_taking.start_listening()
        
        print("✅ Smart conversation active - speak naturally!")
        print("💡 Say 'I wasn't done talking' to train the system")
    
    def stop_conversation(self):
        """Stop the smart conversation system"""
        if not self.is_active:
            return
        
        print("🛑 Stopping smart conversation...")
        self.is_active = False
        
        # Stop turn-taking
        self.turn_taking.stop_listening()
        
        print("✅ Smart conversation stopped")
    
    def get_stats(self) -> dict:
        """Get statistics about the smart STT system"""
        return {
            'feedback_samples': len(self.turn_taking.feedback_samples),
            'current_threshold': self.turn_taking.model_weights.get('base_threshold', 1.5),
            'stt_provider': self.stt_engine.provider if self.stt_engine else 'None',
            'is_active': self.is_active
        }


def test_smart_integration():
    """Test the smart STT integration"""
    print("🧪 Testing Smart STT Integration")
    print("=" * 50)
    
    # Initialize smart STT
    smart_stt = SmartSonanimaSTT()
    
    # Show stats
    stats = smart_stt.get_stats()
    print(f"📊 Initial stats: {stats}")
    
    try:
        # Start conversation
        smart_stt.start_conversation()
        
        print("\n🎤 Smart conversation active!")
        print("Try saying:")
        print("  • 'Hello Sonanima, how are you?'")
        print("  • 'I wasn't done talking' (to train)")
        print("  • Any natural speech")
        print("\nPress Ctrl+C to stop")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping test...")
    finally:
        smart_stt.stop_conversation()
        
        # Show final stats
        final_stats = smart_stt.get_stats()
        print(f"📊 Final stats: {final_stats}")


def integrate_with_companion():
    """Example of full integration with Sonanima companion"""
    print("🤝 Full Sonanima Integration Example")
    print("=" * 50)
    
    try:
        # Initialize components
        smart_stt = SmartSonanimaSTT()
        
        # Try to initialize companion
        try:
            companion = SonanimaCompanion()
            smart_stt.set_companion(companion)
            print("✅ Companion integrated")
        except Exception as e:
            print(f"⚠️ Companion not available: {e}")
            print("📝 Running in STT-only mode")
        
        # Start the integrated system
        smart_stt.start_conversation()
        
        print("\n🎤 Full Sonanima system active!")
        print("Speak naturally - Sonanima will respond with voice!")
        print("Press Ctrl+C to stop")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping integration...")
    finally:
        smart_stt.stop_conversation()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "full":
        integrate_with_companion()
    else:
        test_smart_integration() 