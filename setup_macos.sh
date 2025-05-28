#!/bin/bash
# Sonanima macOS Setup Script
# Installs all system dependencies for optimal TTS streaming

echo "🎯 Sonanima macOS Setup"
echo "======================"
echo "Installing system dependencies for real-time TTS streaming..."
echo

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Please install it first:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

echo "✅ Homebrew found"

# Update brew
echo "🔄 Updating Homebrew..."
brew update

# Core audio/video processing
echo "🎵 Installing FFmpeg (for real-time streaming)..."
brew install ffmpeg

echo "🔊 Installing PortAudio (for PyAudio)..."
brew install portaudio

# Optional: Better audio tools
echo "🎧 Installing additional audio tools..."
brew install sox               # Swiss Army knife of audio
brew install opus              # High-quality audio codec
brew install lame              # MP3 encoder/decoder

# Python build tools (needed for some audio packages)
echo "🐍 Installing Python build tools..."
brew install python-tk        # For GUI audio controls if needed

echo
echo "✅ System dependencies installed!"
echo
echo "📦 Next steps:"
echo "1. Activate your Python venv: source venv/bin/activate"
echo "2. Install Python packages: pip install -r requirements.txt"
echo "3. Test real-time streaming: cd tests/tts && python unified_tts_tester.py"
echo
echo "🚀 Real-time streaming capabilities:"
echo "  • FFmpeg streaming (ffplay)"
echo "  • FIFO pipe streaming (afplay)"
echo "  • PyAudio direct playback"
echo "  • File-based fallback"
echo 