#!/usr/bin/env python3
"""
Unified Sonanima TTS Tester - All tests in one place!
No more file spam, comprehensive audio debugging
"""
import asyncio
import sys
import time
import tempfile
import subprocess
import os
from pathlib import Path

# Add the src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sonanima.tts.elevenlabs.streaming import SonanimaStreamingTTS

class UnifiedTTSTester:
    def __init__(self):
        self.tts = SonanimaStreamingTTS()
        # Set up output directory for test files
        self.output_dir = Path(__file__).parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        
    def check_audio_system(self):
        """Quick audio system check"""
        print("🔊 Audio System Check:")
        
        # Test system audio
        try:
            result = subprocess.run(['say', 'Audio test'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("  ✅ System 'say' command works")
                print("  💡 Did you hear 'Audio test'? If not, check volume/output device")
                return True
            else:
                print("  ❌ System 'say' command failed")
                return False
        except Exception as e:
            print(f"  ❌ Audio system error: {e}")
            return False
    
    async def stream_test(self, text: str, realtime: bool = True):
        """Streaming test - tries real-time first, falls back to file-based"""
        print(f"\n🎯 Stream Test: '{text[:50]}...'")
        
        if not self.tts.ready:
            if not self.tts.setup():
                print("❌ TTS setup failed")
                return False
        
        try:
            if realtime:
                # Try sox streaming first (best for MP3 chunks)
                print("🚀 Attempting real-time streaming...")
                ttfb = await self.tts.stream_and_play_sox(text)
            else:
                # Use file-based streaming for debugging
                print("📁 Using file-based streaming...")
                ttfb = await self.tts.stream_and_play(text)
            
            if ttfb > 0:
                print(f"✅ Stream completed: {ttfb:.2f}s time-to-first-byte")
                
                # Rate the performance
                if ttfb < 0.6:
                    print("⚡ Performance: ULTRA-FAST")
                elif ttfb < 1.0:
                    print("🚀 Performance: FAST") 
                elif ttfb < 2.0:
                    print("✅ Performance: GOOD")
                else:
                    print("⏰ Performance: SLOW")
                    
                return ttfb
            else:
                print("❌ Streaming failed")
                return False
                
        except Exception as e:
            print(f"❌ Stream error: {e}")
            return False
    
    async def debug_audio_playback(self, text: str, save_file: bool = False):
        """File-based audio test for debugging API output"""
        print(f"\n🎯 Debug File Test: '{text[:50]}...'")
        
        if not self.tts.ready:
            if not self.tts.setup():
                print("❌ TTS setup failed")
                return False
        
        start_time = time.time()
        
        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        temp_file.close()
        
        try:
            # Generate audio using streaming
            print("🔄 Generating audio file...")
            audio_chunks = []
            first_chunk_time = None
            
            async for chunk in self.tts.stream_speech_websocket(text):
                if first_chunk_time is None:
                    first_chunk_time = time.time()
                audio_chunks.append(chunk)
            
            if not audio_chunks:
                print("❌ No audio chunks received")
                return False
            
            # Write to file
            with open(temp_file.name, 'wb') as f:
                for chunk in audio_chunks:
                    f.write(chunk)
            
            file_size = os.path.getsize(temp_file.name)
            ttfb = first_chunk_time - start_time if first_chunk_time else -1
            
            print(f"✅ Audio file generated: {file_size} bytes in {ttfb:.2f}s")
            
            # Save permanently if requested
            if save_file:
                timestamp = int(time.time())
                permanent_file = self.output_dir / f"test_audio_{timestamp}.mp3"
                os.rename(temp_file.name, str(permanent_file))
                print(f"💾 Saved to: {permanent_file}")
                temp_file.name = str(permanent_file)
            
            # Play the saved file
            print("🔊 Playing saved file...")
            result = subprocess.run(['afplay', temp_file.name], 
                                   capture_output=True, text=True)
            if result.returncode == 0:
                print("  ✅ File playback succeeded")
            else:
                print(f"  ❌ File playback failed: {result.stderr}")
            
            print(f"\n📁 Output directory: {self.output_dir}")
            
            return ttfb
            
        except Exception as e:
            print(f"❌ Audio generation error: {e}")
            return False
        finally:
            # Cleanup unless saved
            if not save_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    async def quick_test(self):
        """Quick 'hello' test"""
        print("\n" + "="*50)
        print("🚀 QUICK TEST")
        print("="*50)
        return await self.stream_test("Hello! This is a quick test. Can you hear me?")
    
    async def medium_test(self):
        """Medium length test"""
        print("\n" + "="*50)
        print("📝 MEDIUM TEST (100 words)")
        print("="*50)
        text = """Good morning! Welcome to Sonanima, your advanced AI voice companion. 
                 Today we're testing our streaming speech synthesis capabilities with medium-length content. 
                 This test helps us evaluate performance across different response sizes, ensuring consistent 
                 quality and speed regardless of content length. The streaming technology allows us to begin 
                 audio playback almost immediately, creating a natural conversational experience."""
        return await self.stream_test(text)
    
    async def long_test(self):
        """500-word test"""
        print("\n" + "="*50)
        print("📚 LONG TEST (500 words)")
        print("="*50)
        text = """Good morning! Welcome to this comprehensive test of our advanced streaming speech synthesis system. 
                 Today we're evaluating the performance characteristics of ElevenLabs WebSocket streaming technology 
                 when processing longer form content that approaches real-world conversational responses.
                 
                 The field of artificial intelligence has revolutionized how we interact with technology, creating 
                 unprecedented opportunities for natural human-computer communication. Modern text-to-speech systems 
                 like the one we're testing represent significant breakthroughs in neural audio synthesis, enabling 
                 real-time generation of highly natural-sounding speech from arbitrary text input.
                 
                 What makes streaming particularly fascinating is the ability to begin audio playback before the 
                 complete text has been processed. This dramatically reduces perceived latency and creates a more 
                 natural conversational experience. Traditional batch processing would require waiting for the 
                 entire text to be analyzed and converted before any audio could begin playing.
                 
                 Performance optimization involves multiple factors including chunk sizing, network latency, 
                 audio buffering strategies, and the computational efficiency of the underlying neural networks. 
                 The goal is to minimize time to first byte while maintaining consistent audio quality throughout 
                 the generation process.
                 
                 This test demonstrates the practical capabilities of modern streaming synthesis and provides 
                 valuable performance metrics for evaluating real-world deployment scenarios."""
        return await self.stream_test(text)
    
    async def interactive_mode(self):
        """Interactive testing mode"""
        print("\n" + "="*50)
        print("🎮 INTERACTIVE MODE")
        print("="*50)
        print("Commands:")
        print("  'quick' - Quick real-time streaming test")
        print("  'medium' - Medium real-time streaming test") 
        print("  'long' - Long real-time streaming test")
        print("  'quickf' - Quick file-based streaming test")
        print("  'file <text>' - File-based test (for debugging)")
        print("  'save' - Save next audio file")
        print("  'audio' - Audio system check")
        print("  'custom <text>' - Custom real-time streaming")
        print("  'customf <text>' - Custom file-based streaming")
        print("  'quit' - Exit")
        print()
        
        save_next = False
        
        while True:
            try:
                cmd = input("🎤 Command: ").strip().lower()
                
                if cmd == 'quit':
                    break
                elif cmd == 'quick':
                    await self.quick_test()
                elif cmd == 'medium':
                    await self.medium_test()
                elif cmd == 'long':
                    await self.long_test()
                elif cmd == 'quickf':
                    await self.stream_test("Hello! This is a quick file-based test.", realtime=False)
                elif cmd == 'save':
                    save_next = True
                    print("💾 Next audio will be saved permanently")
                elif cmd == 'audio':
                    self.check_audio_system()
                elif cmd.startswith('custom '):
                    text = cmd[7:]
                    await self.stream_test(text, realtime=True)
                elif cmd.startswith('customf '):
                    text = cmd[8:]
                    await self.stream_test(text, realtime=False)
                elif cmd.startswith('file '):
                    text = cmd[5:]
                    await self.debug_audio_playback(text, save_file=save_next)
                    save_next = False
                else:
                    print("❓ Unknown command")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break

async def main():
    print("🎯 Unified Sonanima TTS Tester")
    print("=" * 60)
    print("🚀 Primary: True streaming (plays as chunks arrive)")
    print("💾 Secondary: File-based tests (save/debug API output)")
    print()
    
    tester = UnifiedTTSTester()
    
    # Audio system check
    if not tester.check_audio_system():
        print("⚠️  Audio system issues detected, but continuing...")
    
    print("\nChoose test mode:")
    print("1. Quick streaming test")
    print("2. All streaming tests") 
    print("3. Interactive mode")
    
    choice = input("\nChoice (1-3): ").strip()
    
    if choice == '1':
        await tester.quick_test()
    elif choice == '2':
        await tester.quick_test()
        await tester.medium_test()
        await tester.long_test()
    elif choice == '3':
        await tester.interactive_mode()
    else:
        print("Running quick streaming test by default...")
        await tester.quick_test()

if __name__ == "__main__":
    asyncio.run(main()) 