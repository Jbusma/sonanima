#!/usr/bin/env python3
"""
Qualitative STT Test - Non-Streaming Approach
Records complete audio, then transcribes whole WAV file for accuracy/latency testing
"""
import sys
import random
import time
import tempfile
import os
import subprocess
from pathlib import Path
from difflib import SequenceMatcher
import numpy as np
import soundfile as sf

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sonanima.stt.engine import SonanimaStt

# Try to import OpenAI for API testing
try:
    import openai
    from dotenv import load_dotenv
    HAS_OPENAI_API = True
except ImportError:
    openai = None
    load_dotenv = None
    HAS_OPENAI_API = False


class OpenAIWhisperAPI:
    """OpenAI Whisper API for comparison testing"""
    
    def __init__(self):
        """Initialize OpenAI Whisper API client"""
        if not HAS_OPENAI_API:
            raise ImportError("OpenAI package not installed: pip install openai")
        
        # Load environment variables
        project_root = Path(__file__).parent.parent.parent
        env_path = project_root / ".env"
        load_dotenv(env_path)
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key or api_key == 'your_openai_api_key_here':
            raise ValueError("OpenAI API key not configured in .env file")
        
        self.client = openai.OpenAI(api_key=api_key)
        print("✅ OpenAI Whisper API ready")
    
    def transcribe_audio(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio using OpenAI Whisper API"""
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Write audio to file
            sf.write(temp_path, audio_data, sample_rate)
            
            # Transcribe using OpenAI API
            with open(temp_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )
            
            # Clean up temp file
            os.unlink(temp_path)
            
            return transcript.text.strip()
            
        except Exception as e:
            print(f"❌ OpenAI API transcription failed: {e}")
            return ""


class NonStreamingSTTTest:
    """Non-streaming STT accuracy and latency testing"""
    
    def __init__(self):
        """Initialize the STT test system"""
        print("🧪 Non-Streaming STT Test")
        print("=" * 50)
        
        # Test phrases of varying complexity
        self.test_phrases = [
            # Simple phrases
            "Hello world",
            "How are you today",
            "The weather is nice",
            "I like coffee",
            "Good morning",
            
            # Medium complexity
            "The quick brown fox jumps over the lazy dog",
            "I want to test the speech recognition system",
            "Please remember what I say and respond appropriately",
            "This is a test of the emergency broadcast system",
            "Artificial intelligence is changing the world",
            
            # Complex phrases
            "Supercalifragilisticexpialidocious",
            "She sells seashells by the seashore",
            "How much wood would a woodchuck chuck if a woodchuck could chuck wood",
            "The sixth sick sheik's sixth sheep's sick",
            "Red leather yellow leather",
            
            # Technical terms
            "Machine learning algorithms",
            "Natural language processing",
            "Speech to text transcription",
            "Voice activity detection",
            "Real-time audio streaming",
            
            # Numbers and mixed content
            "The year is twenty twenty four",
            "My phone number is five five five one two three four",
            "The temperature is seventy two degrees",
            "I have three cats and two dogs",
            "The meeting is at three thirty PM"
        ]
        
        # Initialize STT engines
        try:
            self.stt = SonanimaStt()
            print(f"✅ Local STT ready with {self.stt.provider} provider")
        except Exception as e:
            print(f"❌ Failed to initialize local STT: {e}")
            self.stt = None
        
        # Try to initialize OpenAI API
        try:
            self.openai_api = OpenAIWhisperAPI()
            print(f"✅ OpenAI API STT ready")
        except Exception as e:
            print(f"⚠️ OpenAI API not available: {e}")
            self.openai_api = None
        
        # Check if sox is available for recording
        try:
            result = subprocess.run(['sox', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ Sox available for recording")
                self.use_sox = True
            else:
                print("⚠️ Sox not available, will try alternative methods")
                self.use_sox = False
        except Exception:
            print("⚠️ Sox not found, will try alternative methods")
            self.use_sox = False
    
    def calculate_similarity(self, expected: str, actual: str) -> float:
        """Calculate similarity between expected and actual text"""
        return SequenceMatcher(None, expected.lower(), actual.lower()).ratio()
    
    def rate_accuracy(self, similarity: float) -> str:
        """Rate the accuracy based on similarity score"""
        if similarity >= 0.95:
            return "🟢 EXCELLENT"
        elif similarity >= 0.85:
            return "🟡 GOOD"
        elif similarity >= 0.70:
            return "🟠 FAIR"
        elif similarity >= 0.50:
            return "🔴 POOR"
        else:
            return "❌ FAILED"
    
    def record_complete_audio_sox(self, max_duration: float = 5.0) -> tuple:
        """Record complete audio using sox (avoids PortAudio issues)"""
        print("🎤 Recording with sox... (speak clearly within 5 seconds)")
        
        # Create temporary file for recording
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            # Simpler sox command - just record for a fixed time
            # User can stop early with Ctrl+C if needed
            cmd = [
                'sox', '-d',  # Default input device
                temp_path,    # Output file
                'rate', '16000',  # Sample rate
                'channels', '1',  # Mono
                'trim', '0', str(max_duration)  # Record for max_duration
            ]
            
            print("🎤 Recording started... speak now!")
            start_time = time.time()
            
            # Run sox recording with timeout
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=max_duration + 2)
                recording_time = time.time() - start_time
                
                if result.returncode != 0:
                    print(f"❌ Sox recording failed: {result.stderr}")
                    return None, 0
                    
            except subprocess.TimeoutExpired:
                # This is expected - sox should timeout after max_duration
                recording_time = max_duration
                print(f"🔇 Recording complete ({recording_time:.1f}s)")
            
            # Load the recorded audio
            try:
                audio_data, sample_rate = sf.read(temp_path)
                if len(audio_data) == 0:
                    print("❌ No audio recorded")
                    return None, 0
                
                # Convert to mono if stereo
                if len(audio_data.shape) > 1:
                    audio_data = audio_data.mean(axis=1)
                
                # Check if we actually got meaningful audio
                avg_level = np.sqrt(np.mean(audio_data ** 2))
                if avg_level < 0.001:  # Very quiet threshold
                    print("❌ Audio level too low - no speech detected")
                    return None, 0
                
                print(f"📊 Recording stats:")
                print(f"   Duration: {recording_time:.1f}s")
                print(f"   Audio length: {len(audio_data)/sample_rate:.1f}s")
                print(f"   Max level: {np.max(np.abs(audio_data)):.3f}")
                print(f"   Avg level: {avg_level:.3f}")
                
                return audio_data, recording_time
                
            except Exception as e:
                print(f"❌ Failed to load recorded audio: {e}")
                return None, 0
                
        except Exception as e:
            print(f"❌ Recording failed: {e}")
            return None, 0
            
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def record_complete_audio_fallback(self, max_duration: float = 5.0) -> tuple:
        """Fallback recording method using ffmpeg"""
        print("🎤 Recording with ffmpeg... (speak for up to 5 seconds)")
        
        # Create temporary file for recording
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            # Use ffmpeg to record from default microphone
            cmd = [
                'ffmpeg', '-y',  # Overwrite output
                '-f', 'avfoundation',  # macOS audio input
                '-i', ':0',  # Default microphone
                '-t', str(max_duration),  # Max duration
                '-ar', '16000',  # Sample rate
                '-ac', '1',  # Mono
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                temp_path
            ]
            
            print("🎤 Recording started... speak now!")
            start_time = time.time()
            
            # Run ffmpeg recording
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=max_duration + 5)
            recording_time = time.time() - start_time
            
            if result.returncode != 0:
                print(f"❌ FFmpeg recording failed: {result.stderr}")
                return None, 0
            
            # Load the recorded audio
            try:
                audio_data, sample_rate = sf.read(temp_path)
                if len(audio_data) == 0:
                    print("❌ No audio recorded")
                    return None, 0
                
                print(f"📊 Recording stats:")
                print(f"   Duration: {recording_time:.1f}s")
                print(f"   Audio length: {len(audio_data)/sample_rate:.1f}s")
                print(f"   Max level: {np.max(np.abs(audio_data)):.3f}")
                print(f"   Avg level: {np.sqrt(np.mean(audio_data ** 2)):.3f}")
                
                return audio_data, recording_time
                
            except Exception as e:
                print(f"❌ Failed to load recorded audio: {e}")
                return None, 0
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Recording timed out after {max_duration}s")
            return None, 0
            
        except Exception as e:
            print(f"❌ Recording failed: {e}")
            return None, 0
            
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
    
    def record_complete_audio(self, max_duration: float = 5.0) -> tuple:
        """Record complete audio with voice activity detection"""
        if self.use_sox:
            return self.record_complete_audio_sox(max_duration)
        else:
            return self.record_complete_audio_fallback(max_duration)
    
    def transcribe_complete_audio(self, audio_data: np.ndarray, use_api: bool = False) -> tuple:
        """Transcribe complete audio file and measure latency"""
        if use_api and self.openai_api:
            print("🔄 Transcribing with OpenAI API...")
            start_time = time.time()
            transcription = self.openai_api.transcribe_audio(audio_data)
            transcription_time = time.time() - start_time
            return transcription, transcription_time
        elif self.stt:
            print("🔄 Transcribing with local model...")
            start_time = time.time()
            transcription = self.stt.transcribe_audio(audio_data)
            transcription_time = time.time() - start_time
            return transcription, transcription_time
        else:
            print("❌ No transcription engine available")
            return "", 0
    
    def run_single_test(self, phrase: str, use_api: bool = False) -> dict:
        """Run a single non-streaming STT test"""
        engine_name = "OpenAI API" if use_api else f"Local ({self.stt.provider if self.stt else 'None'})"
        print(f"📝 Testing with {engine_name}")
        print(f"   Please speak: \"{phrase}\"")
        print("\nPress Enter when ready...")
        input()
        
        # Record complete audio
        audio_data, recording_time = self.record_complete_audio()
        
        if audio_data is None:
            return None
        
        # Transcribe complete audio
        transcription, transcription_time = self.transcribe_complete_audio(audio_data, use_api)
        
        # Calculate metrics
        similarity = self.calculate_similarity(phrase, transcription)
        rating = self.rate_accuracy(similarity)
        total_time = recording_time + transcription_time
        
        # Display results
        print(f"\n📊 Results ({engine_name}):")
        print(f"   Expected:     \"{phrase}\"")
        print(f"   Got:          \"{transcription}\"")
        print(f"   Accuracy:     {similarity:.1%} {rating}")
        print(f"   Recording:    {recording_time:.1f}s")
        print(f"   Transcription: {transcription_time:.1f}s ({transcription_time*1000:.0f}ms)")
        print(f"   Total time:   {total_time:.1f}s")
        print(f"   Engine:       {engine_name}")
        
        return {
            'expected': phrase,
            'actual': transcription,
            'similarity': similarity,
            'rating': rating,
            'recording_time': recording_time,
            'transcription_time': transcription_time,
            'total_time': total_time,
            'engine': engine_name,
            'transcription_ms': transcription_time * 1000
        }
    
    def run_test_session(self, num_tests: int = 5):
        """Run a session of multiple non-streaming STT tests"""
        print(f"🎯 Starting {num_tests} test session (Non-Streaming)")
        print("=" * 50)
        
        results = []
        
        for i in range(num_tests):
            print(f"\n🔄 Test {i+1}/{num_tests}")
            print("-" * 30)
            
            # Select random phrase
            phrase = random.choice(self.test_phrases)
            
            try:
                result = self.run_single_test(phrase)
                if result:
                    results.append(result)
                    print(f"\n✅ Test {i+1} complete")
                else:
                    print(f"\n❌ Test {i+1} failed (no audio)")
                
                if i < num_tests - 1:
                    print("\nPress Enter for next test...")
                    input()
                    
            except KeyboardInterrupt:
                print("\n⏹️ Test interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Test failed: {e}")
                continue
        
        # Show summary
        self.show_summary(results)
        
        return results
    
    def show_summary(self, results: list):
        """Display test session summary"""
        if not results:
            print("\n❌ No results to summarize")
            return
        
        print("\n" + "=" * 50)
        print("📊 NON-STREAMING TEST SESSION SUMMARY")
        print("=" * 50)
        
        # Calculate statistics
        similarities = [r['similarity'] for r in results]
        recording_times = [r['recording_time'] for r in results]
        transcription_times = [r['transcription_time'] for r in results]
        total_times = [r['total_time'] for r in results]
        
        avg_similarity = sum(similarities) / len(similarities)
        avg_recording = sum(recording_times) / len(recording_times)
        avg_transcription = sum(transcription_times) / len(transcription_times)
        avg_total = sum(total_times) / len(total_times)
        
        # Count ratings
        ratings = [r['rating'] for r in results]
        rating_counts = {}
        for rating in ratings:
            rating_counts[rating] = rating_counts.get(rating, 0) + 1
        
        print(f"📈 Overall Statistics:")
        print(f"   Tests completed:      {len(results)}")
        print(f"   Average accuracy:     {avg_similarity:.1%}")
        print(f"   Average recording:    {avg_recording:.1f}s")
        print(f"   Average transcription: {avg_transcription:.1f}s")
        print(f"   Average total time:   {avg_total:.1f}s")
        print(f"   STT Provider:         {results[0]['engine']}")
        
        print(f"\n🎯 Accuracy Distribution:")
        for rating, count in rating_counts.items():
            percentage = count / len(results) * 100
            print(f"   {rating}: {count} tests ({percentage:.0f}%)")
        
        print(f"\n⚡ Latency Analysis:")
        print(f"   Fastest transcription: {min(transcription_times):.1f}s")
        print(f"   Slowest transcription: {max(transcription_times):.1f}s")
        print(f"   Transcription range:   {max(transcription_times) - min(transcription_times):.1f}s")
        
        print(f"\n📝 Individual Results:")
        for i, result in enumerate(results, 1):
            expected_short = result['expected'][:30] + "..." if len(result['expected']) > 30 else result['expected']
            print(f"   {i}. {result['rating']} ({result['similarity']:.1%}) - {result['transcription_time']:.1f}s - \"{expected_short}\"")
    
    def run_custom_test(self):
        """Run a test with user-provided phrase"""
        print("\n🎯 Custom Phrase Test (Non-Streaming)")
        print("-" * 30)
        
        phrase = input("Enter the phrase you want to test: ").strip()
        if not phrase:
            print("❌ No phrase provided")
            return
        
        try:
            result = self.run_single_test(phrase)
            return result
        except Exception as e:
            print(f"❌ Custom test failed: {e}")
            return None
    
    def run_comparison_test(self, phrase: str) -> dict:
        """Run the same phrase on both local and API for direct comparison"""
        print(f"\n🔄 Comparison Test")
        print("-" * 40)
        print(f"📝 Phrase: \"{phrase}\"")
        print("We'll record once and test both engines")
        
        print("\nPress Enter when ready to record...")
        input()
        
        # Record once for both tests
        audio_data, recording_time = self.record_complete_audio()
        
        if audio_data is None:
            print("❌ Recording failed")
            return None
        
        results = {}
        
        # Test local first
        if self.stt:
            print(f"\n🔄 Testing Local ({self.stt.provider})...")
            transcription_local, time_local = self.transcribe_complete_audio(audio_data, use_api=False)
            similarity_local = self.calculate_similarity(phrase, transcription_local)
            rating_local = self.rate_accuracy(similarity_local)
            
            results['local'] = {
                'transcription': transcription_local,
                'time_ms': time_local * 1000,
                'similarity': similarity_local,
                'rating': rating_local,
                'engine': f"Local ({self.stt.provider})"
            }
        
        # Test API
        if self.openai_api:
            print(f"\n🔄 Testing OpenAI API...")
            transcription_api, time_api = self.transcribe_complete_audio(audio_data, use_api=True)
            similarity_api = self.calculate_similarity(phrase, transcription_api)
            rating_api = self.rate_accuracy(similarity_api)
            
            results['api'] = {
                'transcription': transcription_api,
                'time_ms': time_api * 1000,
                'similarity': similarity_api,
                'rating': rating_api,
                'engine': "OpenAI API"
            }
        
        # Display comparison
        print(f"\n📊 COMPARISON RESULTS")
        print("=" * 50)
        print(f"Expected: \"{phrase}\"")
        print()
        
        if 'local' in results:
            local = results['local']
            print(f"🖥️  LOCAL ({self.stt.provider}):")
            print(f"   Got:      \"{local['transcription']}\"")
            print(f"   Accuracy: {local['similarity']:.1%} {local['rating']}")
            print(f"   Time:     {local['time_ms']:.0f}ms")
        
        if 'api' in results:
            api = results['api']
            print(f"☁️  API (OpenAI Whisper):")
            print(f"   Got:      \"{api['transcription']}\"")
            print(f"   Accuracy: {api['similarity']:.1%} {api['rating']}")
            print(f"   Time:     {api['time_ms']:.0f}ms")
        
        # Speed comparison
        if 'local' in results and 'api' in results:
            speed_diff = results['local']['time_ms'] / results['api']['time_ms']
            if speed_diff > 1:
                print(f"\n⚡ API is {speed_diff:.1f}x FASTER than local")
            else:
                print(f"\n⚡ Local is {1/speed_diff:.1f}x FASTER than API")
        
        results['phrase'] = phrase
        results['recording_time'] = recording_time
        return results


def main():
    """Main test interface"""
    test = NonStreamingSTTTest()
    
    while True:
        print("\n" + "=" * 50)
        print("🎤 Non-Streaming STT Test Menu")
        print("=" * 50)
        print("1. Quick test (3 phrases)")
        print("2. Standard test (5 phrases)")
        print("3. Extended test (10 phrases)")
        print("4. Custom phrase test")
        print("5. Single random phrase")
        print("6. Comparison test")
        print("7. Quit")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == '1':
            test.run_test_session(3)
        elif choice == '2':
            test.run_test_session(5)
        elif choice == '3':
            test.run_test_session(10)
        elif choice == '4':
            test.run_custom_test()
        elif choice == '5':
            phrase = random.choice(test.test_phrases)
            test.run_single_test(phrase)
        elif choice == '6':
            phrase = input("Enter the phrase you want to compare: ").strip()
            if phrase:
                test.run_comparison_test(phrase)
        elif choice == '7':
            print("\n👋 Thanks for testing!")
            break
        else:
            print("❌ Invalid choice, please try again")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Test session ended")
    except Exception as e:
        print(f"\n❌ Test failed: {e}") 