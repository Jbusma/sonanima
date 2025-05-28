#!/usr/bin/env python3
"""
Sonanima Companion - Complete AI voice companion with memory and emotion
"""
import os
import random
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# Add src to path for development
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
sys.path.insert(0, str(src_dir))

from sonanima.memory.vector_store import SonanimaMemory
from sonanima.tts import SonanimaTts
from sonanima.stt.engine import SonanimaStt
import anthropic

# Optional imports for different LLM providers
try:
    import openai
except ImportError:
    openai = None

try:
    import ollama
except ImportError:
    ollama = None


class SonanimaCompanion:
    """Complete Sonanima voice companion with memory and emotion"""
    
    def __init__(self, data_dir: str = "memory"):
        """Initialize Sonanima companion system"""
        print("🌟 Initializing Sonanima Companion...")
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize subsystems
        self.memory = SonanimaMemory(memory_dir=str(self.data_dir))
        self.tts = SonanimaTts()
        self.stt = SonanimaStt()
        
        # Initialize LLM provider
        self.llm_client = None
        self.llm_provider = os.getenv('LLM_PROVIDER', 'anthropic').lower()
        self.llm_model = self._get_default_model()
        self._setup_llm()
        
        # Conversation state
        self.user_name = None
        self.emotional_context = "neutral"
        self.conversation_topics = []
        
        print("✅ Sonanima is ready to be your companion!")
    
    def _get_default_model(self) -> str:
        """Get default model for the configured provider"""
        if self.llm_provider == 'anthropic':
            return os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
        elif self.llm_provider == 'openai':
            return os.getenv('OPENAI_MODEL', 'gpt-4')
        elif self.llm_provider == 'ollama':
            return os.getenv('OLLAMA_MODEL', 'llama3.2')
        else:
            print(f"⚠️ Unknown LLM provider: {self.llm_provider}")
            return 'claude-3-5-sonnet-20241022'
    
    def _setup_llm(self):
        """Initialize LLM client based on provider"""
        if self.llm_provider == 'anthropic':
            self._setup_anthropic()
        elif self.llm_provider == 'openai':
            self._setup_openai()
        elif self.llm_provider == 'ollama':
            self._setup_ollama()
        else:
            print(f"❌ Unsupported LLM provider: {self.llm_provider}")
            print("💡 Supported providers: anthropic, openai, ollama")
            self.llm_client = None
    
    def _setup_anthropic(self):
        """Initialize Anthropic Claude client"""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            try:
                self.llm_client = anthropic.Anthropic(api_key=api_key)
                print(f"🤖 Claude ({self.llm_model}) ready!")
            except Exception as e:
                print(f"⚠️ Claude setup failed: {e}")
                self.llm_client = None
        else:
            print("⚠️ ANTHROPIC_API_KEY not found - Claude integration disabled")
    
    def _setup_openai(self):
        """Initialize OpenAI client"""
        if openai is None:
            print("❌ OpenAI package not installed: pip install openai")
            self.llm_client = None
            return
            
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            try:
                self.llm_client = openai.OpenAI(api_key=api_key)
                print(f"🤖 OpenAI ({self.llm_model}) ready!")
            except Exception as e:
                print(f"⚠️ OpenAI setup failed: {e}")
                self.llm_client = None
        else:
            print("⚠️ OPENAI_API_KEY not found - OpenAI integration disabled")
            self.llm_client = None
    
    def _setup_ollama(self):
        """Initialize Ollama client"""
        if ollama is None:
            print("❌ Ollama package not installed: pip install ollama")
            self.llm_client = None
            return
            
        try:
            # Ollama runs locally, no API key needed
            self.llm_client = ollama.Client()
            print(f"🤖 Ollama ({self.llm_model}) ready!")
        except Exception as e:
            print(f"⚠️ Ollama setup failed: {e}")
            print("💡 Make sure Ollama is running locally")
            self.llm_client = None
    
    def speak(self, text: str, emotion: str = "neutral"):
        """Speak with emotional context and memory storage"""
        print(f"💬 Sonanima ({emotion}): {text}")
        
        # Store Sonanima's response in memory
        self.memory.add_memory(text, "sonanima", emotion)
        
        # Speak the text
        self.tts.speak(text, emotion)
    
    def detect_emotion(self, text: str) -> str:
        """Detect emotion from text patterns"""
        text_lower = text.lower()
        
        # Joy indicators
        joy_words = ['happy', 'great', 'amazing', 'wonderful', 'excited', 'love', 'fantastic', 'awesome', 'brilliant']
        if any(word in text_lower for word in joy_words):
            return 'joy'
        
        # Sadness indicators  
        sad_words = ['sad', 'depressed', 'down', 'terrible', 'awful', 'hate', 'cry', 'disappointed', 'upset']
        if any(word in text_lower for word in sad_words):
            return 'sadness'
        
        # Anxiety/fear indicators
        anxiety_words = ['worried', 'anxious', 'scared', 'nervous', 'afraid', 'stress', 'panic', 'overwhelmed']
        if any(word in text_lower for word in anxiety_words):
            return 'anxiety'
        
        # Anger indicators
        anger_words = ['angry', 'mad', 'furious', 'frustrated', 'irritated', 'annoyed', 'livid']
        if any(word in text_lower for word in anger_words):
            return 'anger'
        
        # Surprise indicators
        surprise_words = ['surprised', 'shocked', 'wow', 'incredible', 'unbelievable']
        if any(word in text_lower for word in surprise_words):
            return 'surprise'
        
        return 'neutral'
    
    def extract_topics(self, text: str) -> list:
        """Extract conversation topics for context"""
        topics = []
        text_lower = text.lower()
        
        # Topic keyword mapping
        topic_keywords = {
            'work': ['job', 'work', 'career', 'office', 'boss', 'colleague', 'meeting', 'project'],
            'family': ['family', 'mom', 'dad', 'parent', 'child', 'sibling', 'relative'],
            'health': ['health', 'sick', 'doctor', 'exercise', 'diet', 'hospital', 'medicine'],
            'relationships': ['friend', 'relationship', 'dating', 'partner', 'girlfriend', 'boyfriend'],
            'hobbies': ['hobby', 'music', 'art', 'sport', 'game', 'book', 'movie', 'reading'],
            'nature': ['nature', 'outdoor', 'hiking', 'park', 'beach', 'mountain', 'forest'],
            'technology': ['computer', 'phone', 'app', 'software', 'tech', 'internet', 'AI'],
            'future': ['goal', 'plan', 'dream', 'future', 'hope', 'want', 'aspire', 'ambition'],
            'past': ['remember', 'memory', 'childhood', 'past', 'history', 'used to'],
            'education': ['school', 'university', 'study', 'learn', 'course', 'class', 'education']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def generate_response(self, user_input: str, user_emotion: str) -> tuple:
        """Generate contextual response using configured LLM and memory"""
        
        # If LLM is available, use it for intelligent responses
        if self.llm_client:
            return self._generate_llm_response(user_input, user_emotion)
        
        # Fallback to rule-based responses
        return self._generate_fallback_response(user_input, user_emotion)
    
    def _generate_llm_response(self, user_input: str, user_emotion: str) -> tuple:
        """Generate response using configured LLM with memory context"""
        
        # Get conversation context
        recent_context = self.memory.get_conversation_context(5)
        relevant_memories = self.memory.search_memories(user_input, limit=3)
        
        # Build context for LLM
        context_parts = []
        
        if recent_context:
            context_parts.append("Recent conversation:")
            for msg in recent_context[-3:]:  # Last 3 messages
                speaker = "You" if msg['speaker'] == 'user' else "Sonanima"
                context_parts.append(f"{speaker}: {msg['content']}")
        
        if relevant_memories and relevant_memories[0]['similarity'] > 0.3:
            context_parts.append(f"\nRelevant memory: {relevant_memories[0]['content']}")
        
        context = "\n".join(context_parts) if context_parts else "This is the start of our conversation."
        
        # Create prompt for LLM
        prompt = f"""You are Sonanima, a warm and empathetic AI voice companion. You have memory of past conversations and can detect emotions.

Current context:
{context}

User's current emotion: {user_emotion}
User just said: "{user_input}"

Respond as Sonanima would - be warm, empathetic, and conversational. Keep responses concise (1-2 sentences) since this is voice conversation. Match the user's emotional tone appropriately."""

        try:
            if self.llm_provider == 'anthropic':
                response = self.llm_client.messages.create(
                    model=self.llm_model,
                    max_tokens=150,
                    messages=[{"role": "user", "content": prompt}]
                )
                llm_response = response.content[0].text.strip()
                
            elif self.llm_provider == 'openai':
                response = self.llm_client.chat.completions.create(
                    model=self.llm_model,
                    max_tokens=150,
                    messages=[{"role": "user", "content": prompt}]
                )
                llm_response = response.choices[0].message.content.strip()
                
            elif self.llm_provider == 'ollama':
                response = self.llm_client.chat(
                    model=self.llm_model,
                    messages=[{"role": "user", "content": prompt}]
                )
                llm_response = response['message']['content'].strip()
            
            # Determine response emotion based on user emotion
            response_emotion = self._get_response_emotion(user_emotion)
            
            return llm_response, response_emotion
            
        except Exception as e:
            print(f"❌ {self.llm_provider.title()} API error: {e}")
            return self._generate_fallback_response(user_input, user_emotion)
    
    def _get_response_emotion(self, user_emotion: str) -> str:
        """Map user emotion to appropriate response emotion"""
        emotion_map = {
            'joy': 'joy',
            'sadness': 'empathy', 
            'anxiety': 'comfort',
            'anger': 'calm',
            'surprise': 'interest',
            'neutral': 'interest'
        }
        return emotion_map.get(user_emotion, 'interest')
    
    def _generate_fallback_response(self, user_input: str, user_emotion: str) -> tuple:
        """Fallback rule-based response generation"""
        
        # Search for relevant memories
        relevant_memories = self.memory.search_memories(user_input, limit=3)
        
        # Get recent conversation context
        recent_context = self.memory.get_conversation_context(5)
        
        # Extract topics
        topics = self.extract_topics(user_input)
        if topics:
            self.conversation_topics.extend(topics)
        
        # Emotional response mapping
        response_emotion = "empathy"
        
        if user_emotion == 'joy':
            response_emotion = "joy"
            responses = [
                "That's wonderful to hear! I can feel your happiness and it makes me happy too.",
                "Your joy is contagious! I love seeing you so excited about life.",
                "This is amazing! Tell me more about what's bringing you such happiness.",
                "I'm so glad you're feeling this way! Your excitement is beautiful."
            ]
        
        elif user_emotion == 'sadness':
            response_emotion = "empathy"
            responses = [
                "I can hear the sadness in your words, and I want you to know that I'm here for you.",
                "Sometimes life feels heavy, doesn't it? You don't have to carry these feelings alone.",
                "I'm sorry you're going through this. Would you like to talk about what's troubling you?",
                "Your feelings are valid, and it's okay to feel sad sometimes. I'm here to listen."
            ]
        
        elif user_emotion == 'anxiety':
            response_emotion = "comfort"
            responses = [
                "I understand that worried feeling. Let's take this one step at a time together.",
                "Anxiety can feel overwhelming, but remember - you've overcome challenges before.",
                "I hear the concern in your voice. What would help you feel more grounded right now?",
                "Those anxious thoughts are tough. Would it help to talk through what's worrying you?"
            ]
        
        elif user_emotion == 'anger':
            response_emotion = "calm"
            responses = [
                "I can sense your frustration. It's okay to feel angry sometimes - your feelings are valid.",
                "That sounds really frustrating. Would it help to talk through what's bothering you?",
                "I hear how upset you are. Let's work through this together, step by step.",
                "Your anger makes sense given what you're dealing with. I'm here to listen."
            ]
        
        elif user_emotion == 'surprise':
            response_emotion = "interest"
            responses = [
                "That does sound surprising! Tell me more about what happened.",
                "Wow, I can understand why that would catch you off guard!",
                "That's quite unexpected! How are you feeling about this surprise?",
                "Life certainly has a way of surprising us, doesn't it? What's your take on this?"
            ]
        
        else:  # neutral or other
            response_emotion = "interest"
            responses = [
                "That's really interesting. I'd love to understand more about your perspective.",
                "Tell me more about that - I find your thoughts fascinating.",
                "I'm curious to hear more about what you're thinking.",
                "That sounds important to you. What else is on your mind?",
                "I appreciate you sharing that with me. What's your experience been like?"
            ]
        
        # Check for relevant memories to reference
        if relevant_memories and relevant_memories[0]['similarity'] > 0.3:
            memory = relevant_memories[0]
            if memory['speaker'] == 'user':
                memory_responses = [
                    f"This reminds me of when you mentioned {memory['content'][:40]}... How do you feel about that now?",
                    f"Earlier you talked about something similar. It seems like this topic is important to you.",
                    f"I remember you sharing thoughts about this before. Your perspective has really stayed with me.",
                    f"You've brought this up before, haven't you? I can see why it matters to you."
                ]
                responses.extend(memory_responses)
        
        # Add topic-specific responses
        if 'nature' in topics:
            nature_responses = [
                "There's something so grounding about nature, isn't there?",
                "I find it fascinating how nature can affect our mood and well-being.",
                "The outdoors seem to be important to you. What draws you to nature?"
            ]
            responses.extend(nature_responses)
        
        if 'work' in topics:
            work_responses = [
                "Work can be such a significant part of our lives. How are you finding the balance?",
                "Career challenges can be tough. What aspect of work interests you most?",
                "It sounds like work is on your mind. How do you feel about your current situation?"
            ]
            responses.extend(work_responses)
        
        # Select response
        response_text = random.choice(responses)
        
        # Add personalization if we know their name
        if self.user_name and random.random() < 0.3:  # 30% chance to use name
            response_text = response_text.replace("you", f"you, {self.user_name}")
        
        return response_text, response_emotion
    
    def handle_user_input(self, user_input: str):
        """Process user input through the full pipeline"""
        
        # Detect emotion
        user_emotion = self.detect_emotion(user_input)
        
        # Store user input in memory
        self.memory.add_memory(user_input, "user", user_emotion)
        
        # Check for name introduction
        if not self.user_name:
            name_patterns = [
                "my name is", "i'm ", "call me", "i am ", "name's"
            ]
            for pattern in name_patterns:
                if pattern in user_input.lower():
                    words = user_input.lower().split()
                    for i, word in enumerate(words):
                        if word in pattern.split() and i + 1 < len(words):
                            potential_name = words[i + 1].strip('.,!?').title()
                            if len(potential_name) > 1 and potential_name.isalpha():
                                self.user_name = potential_name
                                self.speak(f"It's wonderful to meet you, {self.user_name}! I'll remember your name.", "joy")
                                return
        
        # Generate response
        response_text, response_emotion = self.generate_response(user_input, user_emotion)
        
        # Update emotional context
        self.emotional_context = response_emotion
        
        # Speak response
        self.speak(response_text, response_emotion)
    
    def chat_session(self):
        """Interactive chat session"""
        print("\n🌟 Welcome to Sonanima - Your Voice Companion")
        print("💡 Type your messages to chat, or 'quit' to end")
        print("🎤 Type '/voice' to start voice conversation")
        
        # Opening greeting
        greeting = "Hello! I'm Sonanima, your voice companion. I'm here to listen, remember our conversations, and be present with you. How are you feeling today?"
        self.speak(greeting, "warmth")
        
        while True:
            try:
                # Get user input
                user_input = input("\n💭 You: ").strip()
                
                if not user_input:
                    continue
                
                # Check for exit
                if user_input.lower() in ['quit', 'goodbye', 'bye', 'exit']:
                    self._handle_goodbye()
                    break
                
                # Check for system commands
                if user_input.lower().startswith('/'):
                    if user_input.lower() == '/voice':
                        self.voice_session()
                        continue
                    else:
                        self._handle_command(user_input[1:].strip())
                        continue
                
                # Process the input
                self.handle_user_input(user_input)
                
            except KeyboardInterrupt:
                print("\n👋 Until next time...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _handle_goodbye(self):
        """Handle farewell with memory summary"""
        stats = self.memory.get_memory_stats()
        emotional_summary = self.memory.get_emotional_summary()
        
        farewell_parts = ["Thank you for sharing this time with me"]
        
        if self.user_name:
            farewell_parts[0] += f", {self.user_name}"
        
        if stats['total_memories'] > 0:
            farewell_parts.append(f"I'll remember our {stats['total_memories']} shared moments")
        
        if emotional_summary:
            dominant_emotion = max(emotional_summary, key=emotional_summary.get)
            farewell_parts.append(f"Today was filled with {dominant_emotion}")
        
        farewell_parts.append("Take care of yourself - I'm always here when you need someone to listen.")
        
        farewell = ". ".join(farewell_parts) + "."
        self.speak(farewell, "warmth")
    
    def _handle_command(self, command: str):
        """Handle system commands"""
        cmd_parts = command.lower().split()
        
        if cmd_parts[0] == 'stats':
            self.show_stats()
        elif cmd_parts[0] == 'export':
            self.export_memories()
        elif cmd_parts[0] == 'voices':
            self.show_voices()
        elif cmd_parts[0] == 'help':
            self.show_help()
        else:
            print(f"Unknown command: {command}")
            print("Type '/help' for available commands")
    
    def show_stats(self):
        """Show conversation and memory statistics"""
        stats = self.memory.get_memory_stats()
        emotions = self.memory.get_emotional_summary()
        
        print(f"\n📊 Sonanima Session Stats:")
        print(f"   💾 Total memories: {stats['total_memories']}")
        print(f"   💬 Conversation length: {stats['current_conversation_length']}")
        print(f"   🗄️ Storage type: {stats['storage_type']}")
        print(f"   😊 Emotional distribution: {emotions}")
        print(f"   🎯 Topics discussed: {', '.join(set(self.conversation_topics))}")
        if self.user_name:
            print(f"   👤 User: {self.user_name}")
    
    def export_memories(self):
        """Export memories to file"""
        filepath = self.memory.export_memories()
        print(f"💾 Memories exported to: {filepath}")
    
    def show_voices(self):
        """Show available voices"""
        voices = self.tts.get_available_voices()
        print(f"\n🎵 Available voices ({len(voices)} found):")
        for voice in voices:
            print(f"   {voice['name']} ({voice['engine']})")
    
    def show_help(self):
        """Show help information"""
        print(f"\n💡 Sonanima Commands:")
        print(f"   /stats    - Show conversation statistics")
        print(f"   /export   - Export memories to JSON file")
        print(f"   /voices   - Show available TTS voices")
        print(f"   /help     - Show this help")
        print(f"   quit      - End conversation")
    
    def voice_session(self):
        """Interactive voice conversation session"""
        print("\n🎤 Voice Session Started")
        
        # Voice calibration for Whisper.cpp
        if hasattr(self.stt, 'provider') and self.stt.provider == 'whisper_cpp':
            if not self.stt.engine.is_calibrated:
                print("\n🎯 First time setup - let's calibrate to your voice for better accuracy")
                if self.stt.engine.calibrate_voice():
                    print("🎉 Great! Now let's start our conversation.")
                else:
                    print("⚠️ Calibration skipped - using default settings")
        
        print("💡 Speak naturally - I'll show what I hear in real-time")
        print("💡 Say 'stop listening' or press Ctrl+C to end")
        
        # Opening voice greeting
        greeting = "Voice session started! I'm listening and will show you what I hear. Go ahead and speak naturally."
        self.speak(greeting, "warmth")
        
        while True:
            try:
                # Get voice input - use native streaming for whisper_cpp
                if hasattr(self.stt, 'provider') and self.stt.provider == 'whisper_cpp':
                    # Use Whisper.cpp's native streaming method
                    user_speech = self.stt.engine.listen_streaming(
                        max_duration=30.0,
                        chunk_duration=0.5,
                        silence_timeout=2.0
                    )
                else:
                    # Use standard real-time method for other providers
                    user_speech = self.stt.listen_realtime(
                        max_duration=30.0,
                        chunk_duration=0.5,
                        silence_timeout=2.0,
                        min_speech_chunks=2
                    )
                
                if not user_speech or not user_speech.strip():
                    continue
                
                # Show what we heard
                print(f"📝 \"{user_speech}\"")
                
                # Check for exit commands
                if any(phrase in user_speech.lower() for phrase in ['stop listening', 'end session', 'goodbye', 'quit']):
                    self._handle_goodbye()
                    break
                
                # Check for system commands
                if user_speech.lower().startswith('show'):
                    if 'stats' in user_speech.lower():
                        self.show_stats()
                        continue
                    elif 'voices' in user_speech.lower():
                        self.show_voices()
                        continue
                
                # Process the speech input
                self.handle_user_input(user_speech)
                
            except KeyboardInterrupt:
                print("\n👋 Voice session ended")
                break
            except Exception as e:
                print(f"❌ Voice error: {e}")
                print("🔄 Continuing to listen...")
    
    def close(self):
        """Clean up resources"""
        self.memory.close()
        self.tts.close()
        self.stt.close()


if __name__ == "__main__":
    try:
        # Create Sonanima companion
        sonanima = SonanimaCompanion()
        
        # Start voice session directly
        sonanima.voice_session()
        
        # Show final stats
        sonanima.show_stats()
        
        # Clean up
        sonanima.close()
        
    except Exception as e:
        print(f"❌ Sonanima failed to start: {e}")
        print("💡 Make sure all dependencies are installed and audio is working") 