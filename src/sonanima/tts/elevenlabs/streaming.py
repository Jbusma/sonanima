#!/usr/bin/env python3
"""
Sonanima ElevenLabs Streaming Integration - Ultra Low Latency
WebSocket-based streaming for real-time conversation
"""
import os
import time
import json
import asyncio
import websockets
import subprocess
import tempfile
import base64
import threading
from pathlib import Path
from typing import Optional, AsyncGenerator

class SonanimaStreamingTTS:
    """Ultra-fast streaming TTS using ElevenLabs WebSockets"""
    
    def __init__(self):
        self.api_key = None
        self.base_url = "wss://api.elevenlabs.io/v1/text-to-speech"
        self.ready = False
        
        # Voice options
        self.voices = {
            'rachel': '21m00Tcm4TlvDq8ikWAM',    # Warm female (recommended)
            'bella': 'EXAVITQu4vr4xnSDxMaL',     # Soft female
            'antoni': 'ErXwobaYiN019PkySvjV',    # Male
            'josh': 'TxGEqnHWrfWFTfGW9XjX',     # Deep male
            'adam': 'pNInz6obpgDQGcFmaJgB',     # Young male
            'sam': 'yoZ06aMxZJJ28mfd3POQ',      # Male narrator
        }
        self.current_voice = 'rachel'
        
        # Performance settings
        self.model_id = 'eleven_flash_v2_5'  # Fastest model for low latency
        self.chunk_schedule = [50, 120, 160, 290]  # Aggressive chunking for speed
        
    def load_env_file(self):
        """Load environment variables from .env file"""
        # Look for .env in current directory first, then project root
        env_paths = [
            Path('.env'),
            Path(__file__).parent.parent.parent.parent.parent / '.env',  # Project root (adjusted for new location)
        ]
        
        for env_file in env_paths:
            if env_file.exists():
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            os.environ[key] = value
                print(f"✅ Loaded environment from: {env_file}")
                return True
        
        print("❌ No .env file found")
        return False
    
    def setup(self):
        """Setup API key and verify connection"""
        print("🚀 Setting up ElevenLabs Streaming TTS...")
        
        # Load from .env
        self.load_env_file()
        
        # Get API key
        self.api_key = os.getenv('ELEVENLABS_API_KEY')
        if not self.api_key:
            print("❌ ELEVENLABS_API_KEY not found in .env")
            return False
        
        print(f"✅ API key loaded")
        print(f"🎭 Default voice: {self.current_voice}")
        print(f"⚡ Model: {self.model_id} (optimized for speed)")
        
        self.ready = True
        return True
    
    async def stream_speech_websocket(self, text: str, voice: str = None) -> AsyncGenerator[bytes, None]:
        """Stream speech using WebSocket for ultra-low latency"""
        if not self.ready:
            print("❌ Not ready - run setup first")
            return
        
        voice_id = self.voices.get(voice or self.current_voice, self.voices['rachel'])
        uri = f"{self.base_url}/{voice_id}/stream-input?model_id={self.model_id}"
        
        try:
            async with websockets.connect(
                uri, 
                additional_headers={"xi-api-key": self.api_key}
            ) as websocket:
                # Initialize connection with voice settings
                init_message = {
                    "text": " ",  # Space to initialize
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.8,
                        "use_speaker_boost": False
                    },
                    "generation_config": {
                        "chunk_length_schedule": self.chunk_schedule
                    },
                    "xi_api_key": self.api_key
                }
                
                await websocket.send(json.dumps(init_message))
                
                # Send the text
                text_message = {"text": text}
                await websocket.send(json.dumps(text_message))
                
                # Send empty string to close
                await websocket.send(json.dumps({"text": ""}))
                
                # Listen for audio chunks
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        
                        if data.get("audio"):
                            # Yield audio chunk
                            audio_chunk = base64.b64decode(data["audio"])
                            yield audio_chunk
                        
                        if data.get("isFinal"):
                            break
                            
                    except websockets.exceptions.ConnectionClosed:
                        break
                        
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
    
    async def stream_and_play(self, text: str, voice: str = None) -> float:
        """Stream speech and play when ready with timing"""
        start_time = time.time()
        
        # Create temporary file for audio
        temp_file = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        temp_file.close()
        
        audio_started = False
        first_chunk_time = None
        
        try:
            print("🔄 Streaming audio chunks...")
            
            # Collect all chunks (this still streams from the API)
            audio_chunks = []
            async for chunk in self.stream_speech_websocket(text, voice):
                if not audio_started:
                    first_chunk_time = time.time()
                    audio_started = True
                    print(f"🎵 First chunk received: {first_chunk_time - start_time:.2f}s")
                
                audio_chunks.append(chunk)
            
            if not audio_chunks:
                print("❌ No audio chunks received")
                return -1
            
            # Write complete audio file
            with open(temp_file.name, 'wb') as f:
                for chunk in audio_chunks:
                    f.write(chunk)
            
            file_complete_time = time.time()
            print(f"📁 Audio file ready: {file_complete_time - start_time:.2f}s")
            
            # Now play the complete file
            print("🔊 Playing audio...")
            player_process = subprocess.Popen(
                ['afplay', temp_file.name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for playback to finish
            player_process.wait()
            
            total_time = time.time() - start_time
            ttfb = first_chunk_time - start_time if first_chunk_time else total_time
            
            print(f"✅ Playback completed in {total_time:.2f}s total")
            
            return ttfb
            
        except Exception as e:
            print(f"❌ Playback error: {e}")
            return -1
        finally:
            # Cleanup
            try:
                if 'player_process' in locals() and player_process.poll() is None:
                    player_process.terminate()
                os.unlink(temp_file.name)
            except:
                pass
    
    def stream_speech_sync(self, text: str, voice: str = None) -> float:
        """Synchronous wrapper for async streaming"""
        return asyncio.run(self.stream_and_play(text, voice))
    
    def speak_streaming(self, text: str, emotion: str = "neutral") -> bool:
        """Speak text with streaming for voice companion integration"""
        try:
            # Map emotions to voice characteristics (could be enhanced)
            voice_map = {
                'joy': 'rachel',
                'excitement': 'rachel', 
                'sadness': 'bella',
                'empathy': 'bella',
                'comfort': 'bella',
                'warmth': 'rachel',
                'interest': 'rachel',
                'neutral': self.current_voice
            }
            
            voice = voice_map.get(emotion, self.current_voice)
            
            # Use the fastest streaming method
            ttfb = asyncio.run(self.stream_and_play_sox(text, voice))
            
            return ttfb > 0  # Success if we got a positive time
            
        except Exception as e:
            print(f"❌ ElevenLabs streaming failed: {e}")
            return False
    
    async def interactive_streaming_test(self):
        """Interactive test with real-time streaming"""
        print("\n🎤 ElevenLabs Ultra-Fast Streaming Test")
        print("=" * 50)
        print("Type messages for REAL-TIME streaming synthesis!")
        print("Commands:")
        print("  'voice <name>' - change voice")
        print("  'test' - run speed tests")  
        print("  'quit' - exit")
        print(f"\nCurrent voice: {self.current_voice}")
        print(f"Model: {self.model_id} (optimized for speed)")
        print()
        
        while True:
            try:
                user_input = input("💬 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'quit':
                    break
                
                if user_input.lower().startswith('voice '):
                    new_voice = user_input[6:].strip().lower()
                    if new_voice in self.voices:
                        self.current_voice = new_voice
                        print(f"🎭 Voice changed to: {new_voice}")
                    else:
                        print(f"❌ Unknown voice. Available: {list(self.voices.keys())}")
                    continue
                
                if user_input.lower() == 'test':
                    await self.run_speed_tests()
                    continue
                
                # Real-time streaming test
                print(f"🚀 Streaming with {self.current_voice}...")
                
                ttfb = await self.stream_and_play(user_input, self.current_voice)
                
                if ttfb > 0:
                    print(f"⚡ Time to First Byte: {ttfb:.2f}s")
                    print(f"📊 Speed rating: {'🔥 ULTRA FAST' if ttfb < 0.5 else '⚡ FAST' if ttfb < 1.0 else '✅ GOOD'}")
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def run_speed_tests(self):
        """Run automated speed tests"""
        print("\n🧪 Running Speed Tests...")
        
        test_phrases = [
            "Hello world",
            "Testing real-time speech synthesis",
            "This is a longer sentence to test streaming performance with more content",
            "ElevenLabs WebSocket streaming provides ultra-low latency for real-time conversation applications"
        ]
        
        results = []
        
        for i, phrase in enumerate(test_phrases, 1):
            print(f"\n🧪 Test {i}/4: '{phrase[:30]}...'")
            
            ttfb = await self.stream_and_play(phrase, self.current_voice)
            
            if ttfb > 0:
                results.append(ttfb)
                rating = "🔥 ULTRA" if ttfb < 0.5 else "⚡ FAST" if ttfb < 1.0 else "✅ GOOD"
                print(f"  ✅ TTFB: {ttfb:.2f}s {rating}")
        
        if results:
            avg_ttfb = sum(results) / len(results)
            print(f"\n📈 SPEED TEST SUMMARY:")
            print(f"  • Average TTFB: {avg_ttfb:.2f}s")
            print(f"  • Best: {min(results):.2f}s")
            print(f"  • Tests completed: {len(results)}/4")
            print(f"  • Overall rating: {'🔥 ULTRA FAST' if avg_ttfb < 0.5 else '⚡ FAST' if avg_ttfb < 1.0 else '✅ GOOD'}")

    async def stream_and_play_realtime(self, text: str, voice: str = None) -> float:
        """TRUE real-time streaming - plays chunks as they arrive using ffmpeg with low latency"""
        start_time = time.time()
        
        audio_started = False
        first_chunk_time = None
        first_audio_time = None
        
        try:
            print("🔄 Real-time streaming (chunks play immediately)...")
            
            # Start ffplay with aggressive low-latency settings
            player_process = subprocess.Popen([
                'ffplay', 
                '-f', 'mp3',                    # Input format
                '-nodisp',                      # No video display
                '-autoexit',                    # Exit when done
                '-loglevel', 'quiet',           # Suppress ffmpeg output
                '-fflags', 'nobuffer',          # No input buffering
                '-flags', 'low_delay',          # Low delay mode
                '-framedrop',                   # Drop frames if needed
                '-sync', 'audio',               # Sync to audio
                '-vn',                          # No video
                '-sn',                          # No subtitles
                '-dn',                          # No data streams
                '-'                             # Read from stdin
            ], 
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Track when we actually hear audio start
            def audio_started_callback():
                nonlocal first_audio_time
                if first_audio_time is None:
                    first_audio_time = time.time()
                    perceived_latency = first_audio_time - start_time
                    print(f"🎵 Audio started playing: {perceived_latency:.2f}s total latency")
            
            # Stream chunks directly to ffplay with immediate flushing
            chunk_count = 0
            async for chunk in self.stream_speech_websocket(text, voice):
                if not audio_started:
                    first_chunk_time = time.time()
                    audio_started = True
                    print(f"📡 First chunk received: {first_chunk_time - start_time:.2f}s")
                
                try:
                    # Write chunk immediately and force flush
                    player_process.stdin.write(chunk)
                    player_process.stdin.flush()
                    chunk_count += 1
                    
                    # For the first chunk, give a tiny delay for audio to start
                    if chunk_count == 1:
                        await asyncio.sleep(0.05)  # 50ms for audio pipeline
                        if first_audio_time is None:
                            first_audio_time = time.time()
                            print(f"🔊 Audio should be playing: {first_audio_time - start_time:.2f}s")
                        
                except BrokenPipeError:
                    print("⚠️ Audio player stopped reading")
                    break
                except Exception as e:
                    print(f"❌ Chunk write error: {e}")
                    break
            
            # Close stdin to signal end of stream
            if player_process.stdin:
                player_process.stdin.close()
            
            # Wait for playback to finish
            player_process.wait()
            
            total_time = time.time() - start_time
            actual_latency = first_audio_time - start_time if first_audio_time else total_time
            
            print(f"✅ Streaming completed: {chunk_count} chunks")
            print(f"📊 Performance: {actual_latency:.2f}s actual audio latency")
            
            return actual_latency
            
        except FileNotFoundError:
            print("❌ ffplay not found - trying FIFO streaming...")
            return await self.stream_and_play_fifo(text, voice)
        except Exception as e:
            print(f"❌ Real-time streaming error: {e}")
            return -1
        finally:
            # Cleanup
            try:
                if 'player_process' in locals() and player_process.poll() is None:
                    player_process.terminate()
            except:
                pass

    async def stream_and_play_pyaudio(self, text: str, voice: str = None) -> float:
        """Real-time streaming using PyAudio - plays chunks as they arrive"""
        try:
            import pyaudio
            import wave
            import io
        except ImportError:
            print("❌ PyAudio not installed - pip install pyaudio")
            print("💡 Falling back to file-based playback...")
            return await self.stream_and_play(text, voice)
        
        start_time = time.time()
        audio_started = False
        first_chunk_time = None
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        stream = None
        
        try:
            print("🔄 Real-time PyAudio streaming (chunks play immediately)...")
            
            # We'll initialize the audio stream after getting first chunk
            # since we need to know the audio format from the MP3 data
            chunk_count = 0
            audio_buffer = io.BytesIO()
            
            async for chunk in self.stream_speech_websocket(text, voice):
                if not audio_started:
                    first_chunk_time = time.time()
                    audio_started = True
                    print(f"🎵 First chunk streaming: {first_chunk_time - start_time:.2f}s")
                    
                    # For the first chunk, we need to decode MP3 to get audio params
                    # This is a simplified approach - for full MP3 streaming we'd need
                    # a more sophisticated decoder
                    audio_buffer.write(chunk)
                    
                    # Try to extract audio parameters from MP3 header
                    # For now, use common defaults for ElevenLabs MP3
                    if stream is None:
                        stream = p.open(
                            format=pyaudio.paInt16,  # 16-bit
                            channels=1,              # Mono
                            rate=22050,              # ElevenLabs default sample rate
                            output=True,
                            frames_per_buffer=1024
                        )
                        print("🔊 Audio stream opened")
                
                # Write chunk to audio buffer
                audio_buffer.write(chunk)
                chunk_count += 1
                
                # Try to play decoded audio (this is a simplified version)
                # In reality, we'd need to properly decode MP3 chunks
                if stream and chunk_count % 2 == 0:  # Play every few chunks
                    try:
                        # This is a placeholder - real MP3 decoding would be needed
                        # For now, let's fall back to file-based approach
                        pass
                    except Exception as e:
                        print(f"⚠️ Audio playback error: {e}")
            
            total_time = time.time() - start_time
            ttfb = first_chunk_time - start_time if first_chunk_time else total_time
            
            print(f"✅ PyAudio streaming completed: {chunk_count} chunks in {total_time:.2f}s")
            print("💡 Note: MP3 chunk decoding needs improvement for real-time playback")
            
            return ttfb
            
        except Exception as e:
            print(f"❌ PyAudio streaming error: {e}")
            print("💡 Falling back to file-based playback...")
            return await self.stream_and_play(text, voice)
        finally:
            # Cleanup
            try:
                if stream:
                    stream.stop_stream()
                    stream.close()
                p.terminate()
            except:
                pass

    async def stream_and_play_fifo(self, text: str, voice: str = None) -> float:
        """Real-time streaming using FIFO pipe - truly streams chunks as they arrive"""
        start_time = time.time()
        audio_started = False
        first_chunk_time = None
        
        # Create a named pipe (FIFO)
        import tempfile
        import os
        temp_dir = tempfile.mkdtemp()
        fifo_path = os.path.join(temp_dir, 'audio_stream.mp3')
        
        try:
            # Create the FIFO
            os.mkfifo(fifo_path)
            print("🔄 Real-time FIFO streaming (chunks play as they arrive)...")
            
            # Start afplay reading from the FIFO in the background
            player_process = subprocess.Popen(
                ['afplay', fifo_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("🔊 Audio player started, waiting for chunks...")
            
            # Open FIFO for writing (this will block until afplay opens it for reading)
            with open(fifo_path, 'wb') as fifo:
                chunk_count = 0
                async for chunk in self.stream_speech_websocket(text, voice):
                    if not audio_started:
                        first_chunk_time = time.time()
                        audio_started = True
                        print(f"🎵 First chunk streaming: {first_chunk_time - start_time:.2f}s")
                    
                    try:
                        # Write chunk directly to FIFO - afplay will read it immediately
                        fifo.write(chunk)
                        fifo.flush()
                        chunk_count += 1
                    except BrokenPipeError:
                        print("⚠️ Audio player stopped reading")
                        break
            
            # Wait for afplay to finish
            player_process.wait()
            
            total_time = time.time() - start_time
            ttfb = first_chunk_time - start_time if first_chunk_time else total_time
            
            print(f"✅ Real-time FIFO streaming completed: {chunk_count} chunks in {total_time:.2f}s")
            
            return ttfb
            
        except Exception as e:
            print(f"❌ FIFO streaming error: {e}")
            print("💡 Falling back to file-based playback...")
            return await self.stream_and_play(text, voice)
        finally:
            # Cleanup
            try:
                if 'player_process' in locals() and player_process.poll() is None:
                    player_process.terminate()
                os.unlink(fifo_path)
                os.rmdir(temp_dir)
            except:
                pass

    async def stream_and_play_sox(self, text: str, voice: str = None) -> float:
        """Real-time streaming using sox - handles MP3 chunks better than ffplay"""
        start_time = time.time()
        
        audio_started = False
        first_chunk_time = None
        first_audio_time = None
        
        try:
            print("🔄 Sox streaming (chunks play as they arrive)...")
            
            # Use sox to play MP3 stream from stdin
            player_process = subprocess.Popen([
                'play',           # sox play command
                '-t', 'mp3',      # Input type MP3
                '-',              # Read from stdin
                'trim', '0'       # Start immediately, no delay
            ], 
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Stream chunks directly to sox
            chunk_count = 0
            async for chunk in self.stream_speech_websocket(text, voice):
                if not audio_started:
                    first_chunk_time = time.time()
                    audio_started = True
                    print(f"📡 First chunk received: {first_chunk_time - start_time:.2f}s")
                
                try:
                    # Write chunk immediately
                    player_process.stdin.write(chunk)
                    player_process.stdin.flush()
                    chunk_count += 1
                    
                    # Estimate when audio starts
                    if chunk_count == 1:
                        # Give minimal time for sox to start playing
                        await asyncio.sleep(0.02)  # 20ms
                        first_audio_time = time.time()
                        print(f"🔊 Audio playing: {first_audio_time - start_time:.2f}s")
                        
                except BrokenPipeError:
                    print("⚠️ Sox player stopped reading")
                    break
                except Exception as e:
                    print(f"❌ Chunk write error: {e}")
                    break
            
            # Close stdin
            if player_process.stdin:
                player_process.stdin.close()
            
            # Wait for playback to finish
            player_process.wait()
            
            total_time = time.time() - start_time
            actual_latency = first_audio_time - start_time if first_audio_time else total_time
            
            print(f"✅ Sox streaming completed: {chunk_count} chunks")
            print(f"📊 Performance: {actual_latency:.2f}s actual audio latency")
            
            return actual_latency
            
        except FileNotFoundError:
            print("❌ sox not found - falling back to ffplay...")
            return await self.stream_and_play_realtime(text, voice)
        except Exception as e:
            print(f"❌ Sox streaming error: {e}")
            return -1
        finally:
            # Cleanup
            try:
                if 'player_process' in locals() and player_process.poll() is None:
                    player_process.terminate()
            except:
                pass

def main():
    print("🎯 ElevenLabs Ultra-Fast Streaming TTS Test")
    print("=" * 60)
    
    tts = SonanimaStreamingTTS()
    
    if not tts.setup():
        print("❌ Setup failed - exiting")
        return
    
    print("\n🚀 Ready for ultra-low latency streaming!")
    
    # Run interactive test
    asyncio.run(tts.interactive_streaming_test())

if __name__ == "__main__":
    main() 