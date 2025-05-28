#!/usr/bin/env python3
"""
Smart Filler System for Sonanima
Plays contextual filler phrases immediately while real response generates
"""
import random
import time
import threading
import tempfile
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class FillerPhrase:
    """A filler phrase with context and audio"""
    text: str
    context: str  # "thinking", "acknowledging", "clarifying", "processing"
    emotion: str  # "neutral", "curious", "understanding", "engaged"
    duration_ms: int
    audio_path: Optional[str] = None
    usage_count: int = 0

class SmartFillerSystem:
    """Intelligent filler phrase system for perceived latency reduction"""
    
    def __init__(self):
        self.filler_phrases = self._init_filler_phrases()
        self.context_history = []
        self.last_filler_time = 0
        self.min_filler_gap = 2.0  # Don't repeat fillers too quickly
        
        # Pre-generated audio cache
        self.audio_cache: Dict[str, str] = {}
        self.cache_dir = Path("data/filler_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Callbacks
        self.on_filler_complete: Optional[Callable] = None
        
    def _init_filler_phrases(self) -> Dict[str, List[FillerPhrase]]:
        """Initialize contextual filler phrases"""
        return {
            "thinking": [
                FillerPhrase("Hmm, let me think about that...", "thinking", "curious", 1200),
                FillerPhrase("That's an interesting question...", "thinking", "engaged", 1100),
                FillerPhrase("Let me consider that for a moment...", "thinking", "neutral", 1300),
                FillerPhrase("Oh, that's a good point...", "thinking", "understanding", 900),
                FillerPhrase("I see what you're getting at...", "thinking", "engaged", 1000),
            ],
            
            "acknowledging": [
                FillerPhrase("I understand...", "acknowledging", "understanding", 800),
                FillerPhrase("Right, okay...", "acknowledging", "neutral", 600),
                FillerPhrase("Yes, I see...", "acknowledging", "understanding", 700),
                FillerPhrase("Mm-hmm, got it...", "acknowledging", "neutral", 650),
                FillerPhrase("That makes sense...", "acknowledging", "understanding", 850),
            ],
            
            "clarifying": [
                FillerPhrase("Just to make sure I understand...", "clarifying", "curious", 1200),
                FillerPhrase("So you're saying...", "clarifying", "curious", 800),
                FillerPhrase("Let me clarify...", "clarifying", "neutral", 750),
                FillerPhrase("To be clear...", "clarifying", "neutral", 650),
                FillerPhrase("If I'm understanding correctly...", "clarifying", "curious", 1100),
            ],
            
            "processing": [
                FillerPhrase("Give me just a second...", "processing", "neutral", 900),
                FillerPhrase("Let me process that...", "processing", "neutral", 850),
                FillerPhrase("One moment...", "processing", "neutral", 600),
                FillerPhrase("Bear with me...", "processing", "neutral", 700),
                FillerPhrase("Just processing that...", "processing", "neutral", 800),
            ]
        }
    
    def analyze_context(self, user_input: str, conversation_history: List[str]) -> str:
        """Analyze what type of filler would be most appropriate"""
        user_lower = user_input.lower()
        
        # Question indicators
        question_words = ["what", "how", "why", "when", "where", "who", "which", "can", "could", "would", "should"]
        if any(word in user_lower for word in question_words) or "?" in user_input:
            return "thinking"
        
        # Complex/long statements
        if len(user_input.split()) > 15:
            return "processing"
        
        # Clarification needed
        clarification_indicators = ["explain", "clarify", "elaborate", "detail", "specific"]
        if any(word in user_lower for word in clarification_indicators):
            return "clarifying"
        
        # Default to acknowledging
        return "acknowledging"
    
    def select_filler(self, context: str, avoid_recent: bool = True) -> FillerPhrase:
        """Select the best filler phrase for the context"""
        available_fillers = self.filler_phrases.get(context, self.filler_phrases["acknowledging"])
        
        if avoid_recent and len(self.context_history) > 0:
            # Avoid recently used phrases
            recent_texts = [item["text"] for item in self.context_history[-3:]]
            available_fillers = [f for f in available_fillers if f.text not in recent_texts]
            
            if not available_fillers:
                # If all are recent, use least recently used
                available_fillers = self.filler_phrases[context]
        
        # Prefer less-used fillers
        available_fillers.sort(key=lambda x: x.usage_count)
        
        # Add some randomness to top 3 least used
        top_choices = available_fillers[:3]
        selected = random.choice(top_choices)
        
        # Update usage
        selected.usage_count += 1
        
        # Track history
        self.context_history.append({
            "text": selected.text,
            "context": context,
            "timestamp": time.time()
        })
        
        # Keep history manageable
        if len(self.context_history) > 10:
            self.context_history = self.context_history[-10:]
        
        return selected
    
    def should_use_filler(self, user_input: str) -> bool:
        """Determine if a filler should be used"""
        # Don't use fillers too frequently
        if time.time() - self.last_filler_time < self.min_filler_gap:
            return False
        
        # Don't use fillers for very short inputs
        if len(user_input.split()) < 3:
            return False
        
        # Don't use fillers for simple greetings
        simple_greetings = ["hi", "hello", "hey", "thanks", "thank you", "bye", "goodbye"]
        if user_input.lower().strip() in simple_greetings:
            return False
        
        return True
    
    async def generate_filler_audio(self, filler: FillerPhrase, tts_engine) -> str:
        """Generate audio for a filler phrase using the TTS engine"""
        cache_key = f"{filler.context}_{hash(filler.text)}"
        cache_path = self.cache_dir / f"{cache_key}.wav"
        
        if cache_path.exists():
            return str(cache_path)
        
        try:
            # Generate audio with appropriate emotion/voice
            audio_path = await tts_engine.speak_streaming(
                filler.text,
                emotion=filler.emotion,
                save_path=str(cache_path)
            )
            
            self.audio_cache[cache_key] = str(cache_path)
            return str(cache_path)
            
        except Exception as e:
            print(f"❌ Failed to generate filler audio: {e}")
            return None
    
    def play_immediate_filler(self, user_input: str, conversation_history: List[str], tts_engine) -> Optional[FillerPhrase]:
        """Play an immediate filler while real response generates"""
        if not self.should_use_filler(user_input):
            return None
        
        # Analyze context and select filler
        context = self.analyze_context(user_input, conversation_history)
        filler = self.select_filler(context)
        
        print(f"🎭 Playing filler: '{filler.text}' ({context})")
        
        # Start filler generation/playback in background
        threading.Thread(
            target=self._play_filler_async,
            args=(filler, tts_engine),
            daemon=True
        ).start()
        
        self.last_filler_time = time.time()
        return filler
    
    def _play_filler_async(self, filler: FillerPhrase, tts_engine):
        """Play filler audio asynchronously"""
        try:
            # Generate or get cached audio
            if filler.text not in self.audio_cache:
                # Quick generation for immediate playback
                audio_path = tts_engine.speak_streaming(
                    filler.text,
                    emotion=filler.emotion
                )
            else:
                audio_path = self.audio_cache[filler.text]
            
            # Play the audio
            if audio_path:
                import subprocess
                subprocess.run(["afplay", audio_path], check=False)
            
            # Notify completion
            if self.on_filler_complete:
                self.on_filler_complete()
                
        except Exception as e:
            print(f"❌ Filler playback error: {e}")
    
    def pre_generate_cache(self, tts_engine, max_phrases: int = 20):
        """Pre-generate audio for most common filler phrases"""
        print("🎭 Pre-generating filler phrase cache...")
        
        # Get most important phrases from each category
        important_phrases = []
        for context, phrases in self.filler_phrases.items():
            important_phrases.extend(phrases[:3])  # Top 3 from each category
        
        # Sort by estimated usage frequency (shorter = more frequent)
        important_phrases.sort(key=lambda x: len(x.text))
        important_phrases = important_phrases[:max_phrases]
        
        generated = 0
        for filler in important_phrases:
            try:
                cache_key = f"{filler.context}_{hash(filler.text)}"
                cache_path = self.cache_dir / f"{cache_key}.wav"
                
                if not cache_path.exists():
                    print(f"  Generating: '{filler.text}'")
                    audio_path = tts_engine.speak_streaming(
                        filler.text,
                        emotion=filler.emotion,
                        save_path=str(cache_path)
                    )
                    if audio_path:
                        self.audio_cache[cache_key] = str(cache_path)
                        generated += 1
                else:
                    self.audio_cache[cache_key] = str(cache_path)
                    
            except Exception as e:
                print(f"  ❌ Failed to generate '{filler.text}': {e}")
        
        print(f"✅ Generated {generated} new filler phrases, {len(self.audio_cache)} total cached")
    
    def get_stats(self) -> Dict:
        """Get statistics about filler usage"""
        total_usage = sum(
            phrase.usage_count 
            for phrases in self.filler_phrases.values() 
            for phrase in phrases
        )
        
        context_usage = {}
        for context, phrases in self.filler_phrases.items():
            context_usage[context] = sum(p.usage_count for p in phrases)
        
        return {
            "total_fillers_used": total_usage,
            "context_breakdown": context_usage,
            "cached_audio_files": len(self.audio_cache),
            "recent_history": len(self.context_history)
        }


def test_filler_system():
    """Test the smart filler system"""
    print("🎭 Testing Smart Filler System")
    print("=" * 50)
    
    filler_system = SmartFillerSystem()
    
    # Test context analysis
    test_inputs = [
        "What's the weather like today?",
        "Can you explain quantum physics to me in detail?",
        "Hello there!",
        "I need you to help me understand this complex problem I'm having with my code",
        "Thanks for your help"
    ]
    
    print("🧠 Context Analysis Test:")
    for input_text in test_inputs:
        context = filler_system.analyze_context(input_text, [])
        should_use = filler_system.should_use_filler(input_text)
        print(f"  '{input_text}' → {context} (use: {should_use})")
    
    print("\n🎭 Filler Selection Test:")
    for context in ["thinking", "acknowledging", "clarifying", "processing"]:
        filler = filler_system.select_filler(context)
        print(f"  {context}: '{filler.text}' ({filler.duration_ms}ms)")
    
    # Show stats
    stats = filler_system.get_stats()
    print(f"\n📊 Stats: {stats}")


if __name__ == "__main__":
    test_filler_system() 