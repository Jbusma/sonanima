# Local TTS Tests

This directory contains tests and experiments for local text-to-speech solutions.

## Files

- **`fast_local_options.py`** - Fast local TTS engine comparisons (pyttsx3, system say, etc.)
- **`sesame_integration.py`** - Sesame CSM-1B model integration
- **`local_tokenizer_patch.py`** - Local tokenizer patches for Llama models  
- **`test_local_sesame.py`** - Tests for local Sesame CSM implementation
- **`test_csm.py`** - Basic CSM model tests
- **`models/`** - Experimental model implementations and requirements

## Local TTS Options Tested

1. **pyttsx3** - Cross-platform TTS library (fastest)
2. **macOS say** - System TTS command (fast, macOS only)
3. **Sesame CSM-1B** - Local neural TTS model (high quality, slow)
4. **Coqui TTS** - Open source neural TTS

## Running Tests

```bash
cd tests/tts/local
python fast_local_options.py
python sesame_integration.py
```

## Requirements

- Local models may require additional setup in `models/`
- Some tests require local Llama checkpoints in `~/.llama/checkpoints/`
- pyttsx3: `pip install pyttsx3` 