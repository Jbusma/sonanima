#!/usr/bin/env python3
"""
Sonanima - Voice AI Companion
Main entry point for direct voice interaction
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Main entry point for Sonanima voice companion"""
    try:
        print("🌟 Starting Sonanima Voice AI Companion...")
        
        from sonanima.core.companion import SonanimaCompanion
        
        # Create and start companion
        companion = SonanimaCompanion()
        
        # Start voice session directly
        companion.voice_session()
        
        # Show final stats
        companion.show_stats()
        
        # Clean up
        companion.close()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Sonanima failed to start: {e}")
        print("💡 Check your configuration and audio setup")
        sys.exit(1)

if __name__ == "__main__":
    main() 