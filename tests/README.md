# Sonanima Tests

This directory contains all tests and experimental code for the Sonanima project, organized by provider and functionality.

## Directory Structure

```
tests/
├── tts/                        # Text-to-Speech tests
│   ├── unified_tts_tester.py   # 🎯 Main testing interface (START HERE)
│   ├── elevenlabs/             # ElevenLabs WebSocket streaming tests
│   │   ├── cost_performance_analysis.py
│   │   ├── bidirectional_streaming*.py
│   │   └── *_demo.py, *_test.py
│   ├── local/                  # Local TTS implementations
│   │   ├── fast_local_options.py
│   │   ├── sesame_integration.py
│   │   └── models/
│   └── output/                 # 📁 Generated audio files
│       ├── *.mp3, *.wav        
│       └── utilities/
└── stt/                        # Speech-to-Text tests (placeholder)
```

## Quick Start

### Run Main TTS Tester
```bash
cd tests/tts
python unified_tts_tester.py
```

### Test ElevenLabs Streaming
```bash
cd tests/tts/elevenlabs
python quick_stream_test.py
```

### Test Local TTS Options
```bash
cd tests/tts/local
python fast_local_options.py
```

## Key Features

- **Organized by Provider**: ElevenLabs, local TTS, etc.
- **Output Management**: All test files go to `output/` directory
- **Unified Testing**: Single interface for all TTS testing
- **Performance Analysis**: Latency and cost analysis tools

## Provider-Specific Tests

### ElevenLabs (`elevenlabs/`)
- WebSocket streaming tests
- Real-time latency analysis
- Cost per character metrics
- Bidirectional LLM+TTS streaming
- Requires: `ELEVENLABS_API_KEY` in `.env`

### Local TTS (`local/`)
- pyttsx3, macOS say, Coqui TTS
- Sesame CSM-1B neural model
- Local Llama integrations
- Requires: Various local dependencies

## File Organization

- 🧪 **Tests**: Organized by TTS provider
- 📁 **Output**: All generated audio files in one place  
- 📚 **Documentation**: README in each directory
- 🧹 **Clean**: No test files cluttering source code

## Notes

- All tests include proper path setup to import from `src/`
- Tests are isolated from production code in `src/sonanima/`
- Audio files are automatically organized in `output/`
- Each provider directory has specific setup instructions 