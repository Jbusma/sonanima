# Sonanima - Voice AI Companion

A voice-first AI companion with memory, emotion detection, and real-time conversation capabilities.

## Features

- **Multi-Provider STT**: OpenAI Whisper, Whisper.cpp, Vosk, SpeechRecognition
- **Multi-Provider LLM**: Claude (Anthropic), GPT (OpenAI), Ollama (local)
- **Multi-Provider TTS**: ElevenLabs, pyttsx3, system voice
- **Memory System**: Vector-based conversation memory with context
- **Emotion Detection**: Real-time emotion analysis and response
- **REST API**: FastAPI-based API for integration with n8n and other tools

## Quick Start

### 1. Setup Environment

```bash
# Clone and setup
git clone <your-repo-url>
cd sonanima
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy environment template
cp .envbase .env

# Edit .env with your API keys:
# ANTHROPIC_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here  
# ELEVENLABS_API_KEY=your_key_here
```

### 3. Run Sonanima

```bash
# Direct voice interaction
python sonanima.py

# Or start the API server
python src/api/main.py
# Visit: http://localhost:8000/docs
```

## Testing

Run the comprehensive test suite:

```bash
# Interactive test runner
python run_tests.py

# Specific test categories:
python run_tests.py  # Choose option:
# 1. Multi-Provider Tests (STT/TTS/LLM)
# 2. Memory System Tests  
# 3. API Integration Tests
# 4. Voice Companion Tests
# 5. All Tests (comprehensive)
```

### Memory System Tests

Test the core memory functionality:

```bash
# Run memory tests directly
python tests/memory/test_memory_system.py

# Test the "Jack" example:
# 1. Add memory: "my name is Jack"
# 2. Query: "what is my name"
# 3. Verify: Response mentions "Jack"
```

## Architecture

### Provider-Based Design
- **STT Providers**: `src/sonanima/stt/`
- **TTS Providers**: `src/sonanima/tts/`  
- **LLM Integration**: `src/sonanima/core/companion.py`
- **Memory System**: `src/sonanima/memory/`
- **API Layer**: `src/api/`

### Memory System
- **Vector Search**: Semantic similarity using sentence transformers
- **SQLite Fallback**: Reliable storage with manual similarity calculation
- **Conversation Context**: Recent message history for context
- **Emotional Tracking**: Emotion-based memory importance scoring

### Performance Targets
- **Real-time STT**: <1s transcription latency
- **TTS Streaming**: <0.6s time-to-first-audio
- **Memory Search**: <100ms semantic search
- **End-to-end**: <2s total conversation latency

## Configuration

### Environment Variables

```bash
# LLM Providers (auto-detection priority)
LLM_PROVIDER=anthropic  # anthropic, openai, ollama
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key

# TTS Providers (priority: elevenlabs > pyttsx3 > system)
TTS_PROVIDER=elevenlabs  # elevenlabs, pyttsx3, system
ELEVENLABS_API_KEY=your_key
ELEVENLABS_VOICE_ID=rachel

# STT Providers (priority: openai_whisper > whisper_cpp > vosk)
STT_PROVIDER=openai_whisper  # openai_whisper, whisper_cpp, vosk, speech_recognition

# Memory Configuration
MEMORY_DIR=memory
USE_VECTOR_DB=true
```

## Development

### Adding New Providers

1. **STT Provider**: Add to `src/sonanima/stt/`
2. **TTS Provider**: Add to `src/sonanima/tts/`
3. **Update Engine**: Register in respective `engine.py`
4. **Add Tests**: Create corresponding test file

### Testing Strategy

- **Unit Tests**: Code quality and API compliance
- **Integration Tests**: Cross-provider functionality  
- **Memory Tests**: Semantic search and context retrieval
- **Performance Tests**: Latency and accuracy benchmarks

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python run_tests.py`
5. Submit a pull request

---

**Note**: This is a voice-first AI system. For best experience, ensure microphone permissions are granted and audio devices are properly configured. 