#!/usr/bin/env python3
"""
Test Local Sesame CSM Integration for Sonanima
"""
import os
import sys
import torch
import torchaudio
from pathlib import Path
import traceback
import subprocess

# Add the models directory to path
MODELS_DIR = Path(__file__).parent / "models"
sys.path.insert(0, str(MODELS_DIR))

# Local Llama model paths
LLAMA_BASE_PATH = "/Users/mac/.llama/checkpoints/Llama3.2-1B"
LLAMA_INSTRUCT_PATH = "/Users/mac/.llama/checkpoints/Llama3.2-1B-Instruct"

class LocalSesameTest:
    """Test Sesame CSM with local Llama models"""
    
    def __init__(self):
        print("🎤 Initializing Local Sesame CSM Test")
        print("=" * 50)
        
        # Device setup
        if torch.backends.mps.is_available():
            self.device = "mps"
            print("🍎 Using Apple Silicon (MPS)")
        elif torch.cuda.is_available():
            self.device = "cuda"
            print("🟢 Using NVIDIA GPU")
        else:
            self.device = "cpu"
            print("💻 Using CPU")
        
        self.sample_rate = 24000
        self.generator = None
        
    def check_prerequisites(self):
        """Check if all required components are available"""
        print("\n🔍 Checking Prerequisites...")
        
        # Check Llama models
        llama_base = Path(LLAMA_BASE_PATH)
        llama_instruct = Path(LLAMA_INSTRUCT_PATH)
        
        if llama_base.exists():
            print(f"✅ Llama3.2-1B found: {llama_base}")
        else:
            print(f"❌ Llama3.2-1B not found: {llama_base}")
            return False
            
        if llama_instruct.exists():
            print(f"✅ Llama3.2-1B-Instruct found: {llama_instruct}")
        else:
            print(f"⚠️  Llama3.2-1B-Instruct not found: {llama_instruct}")
        
        # Check CSM components
        required_files = ['models.py', 'generator.py', 'watermarking.py']
        for file in required_files:
            if (MODELS_DIR / file).exists():
                print(f"✅ CSM component found: {file}")
            else:
                print(f"❌ CSM component missing: {file}")
                return False
        
        return True
    
    def setup_environment(self):
        """Set up environment for local model usage"""
        print("\n🔧 Setting up Environment...")
        
        # Set environment variables for local Llama
        os.environ['LLAMA_LOCAL_PATH'] = LLAMA_BASE_PATH
        os.environ['HF_HOME'] = str(Path.home() / '.cache' / 'huggingface')
        
        # Disable HF transfer for now
        os.environ.pop('HF_HUB_ENABLE_HF_TRANSFER', None)
        
        print("✅ Environment configured")
    
    def test_imports(self):
        """Test importing CSM components"""
        print("\n📦 Testing CSM Imports...")
        
        try:
            from models import Model, ModelArgs, FLAVORS
            print("✅ Models imported successfully")
            
            from generator import Generator, Segment, load_llama3_tokenizer
            print("✅ Generator imported successfully")
            
            from watermarking import load_watermarker
            print("✅ Watermarking imported successfully")
            
            return True
            
        except Exception as e:
            print(f"❌ Import failed: {e}")
            traceback.print_exc()
            return False
    
    def test_tokenizer(self):
        """Test Llama tokenizer setup"""
        print("\n📝 Testing Tokenizer...")
        
        try:
            from generator import load_llama3_tokenizer
            
            # Try to load with local model path
            tokenizer = load_llama3_tokenizer()
            print("✅ Tokenizer loaded successfully")
            
            # Test tokenization
            test_text = "Hello, I'm Sonanima!"
            tokens = tokenizer.encode(test_text)
            print(f"✅ Test tokenization: '{test_text}' -> {len(tokens)} tokens")
            
            return True
            
        except Exception as e:
            print(f"❌ Tokenizer test failed: {e}")
            return False
    
    def test_model_loading(self):
        """Test loading CSM model"""
        print("\n🤖 Testing CSM Model Loading...")
        
        try:
            from models import Model
            from generator import Generator
            
            # Load CSM-1B model
            print("📥 Loading CSM-1B from HuggingFace...")
            model = Model.from_pretrained("sesame/csm-1b")
            model.to(device=self.device, dtype=torch.bfloat16)
            print("✅ CSM-1B loaded successfully")
            
            # Create generator
            self.generator = Generator(model)
            print("✅ Generator created successfully")
            
            return True
            
        except Exception as e:
            print(f"❌ Model loading failed: {e}")
            traceback.print_exc()
            return False
    
    def test_speech_generation(self):
        """Test speech generation"""
        print("\n🎵 Testing Speech Generation...")
        
        if not self.generator:
            print("❌ No generator available")
            return False
        
        try:
            test_text = "Hello! I'm Sonanima, your voice companion. This is a test of local Sesame CSM with your downloaded Llama models."
            
            print(f"Generating: '{test_text[:50]}...'")
            
            # Generate audio
            audio = self.generator.generate(
                text=test_text,
                speaker=0,
                context=[],
                max_audio_length_ms=15_000,  # 15 seconds max
                temperature=0.9,
                topk=50
            )
            
            # Save audio
            output_file = "test_local_sesame.wav"
            torchaudio.save(output_file, audio.unsqueeze(0).cpu(), self.generator.sample_rate)
            print(f"💾 Audio saved: {output_file}")
            
            # Audio info
            duration = len(audio) / self.generator.sample_rate
            print(f"📊 Generated {duration:.2f}s of audio at {self.generator.sample_rate}Hz")
            
            return output_file
            
        except Exception as e:
            print(f"❌ Speech generation failed: {e}")
            traceback.print_exc()
            return None
    
    def play_audio(self, audio_file):
        """Play generated audio"""
        print(f"\n🔊 Playing Audio: {audio_file}")
        
        try:
            # Use macOS afplay
            subprocess.run(['afplay', audio_file], check=True)
            print("✅ Playback completed")
        except Exception as e:
            print(f"⚠️  Playback failed: {e}")
            print(f"💡 Play manually: afplay {audio_file}")
    
    def run_full_test(self):
        """Run complete test suite"""
        print("🚀 Starting Local Sesame CSM Test Suite")
        print("=" * 60)
        
        success_count = 0
        
        # Prerequisites
        if self.check_prerequisites():
            success_count += 1
        else:
            print("❌ Prerequisites failed - cannot continue")
            return False
        
        # Environment setup
        self.setup_environment()
        success_count += 1
        
        # Imports
        if self.test_imports():
            success_count += 1
        else:
            print("❌ Import test failed - cannot continue")
            return False
        
        # Tokenizer
        if self.test_tokenizer():
            success_count += 1
        
        # Model loading
        if self.test_model_loading():
            success_count += 1
        else:
            print("❌ Model loading failed - cannot continue")
            return False
        
        # Speech generation
        audio_file = self.test_speech_generation()
        if audio_file:
            success_count += 1
            
            # Play audio
            self.play_audio(audio_file)
        
        # Results
        print("\n" + "=" * 60)
        print(f"🎯 Test Results: {success_count}/6 tests passed")
        
        if success_count >= 5:
            print("🎉 Local Sesame CSM is working!")
            print("✅ You can now use high-quality conversational speech in Sonanima")
        elif success_count >= 3:
            print("⚠️  Partial success - some features may be limited")
        else:
            print("❌ Multiple failures - check dependencies and setup")
        
        return success_count >= 5

def main():
    """Main test function"""
    try:
        tester = LocalSesameTest()
        success = tester.run_full_test()
        
        if success:
            print("\n🚀 Next Steps:")
            print("1. Integrate CSM into main Sonanima companion")
            print("2. Add conversation context for better speech quality")
            print("3. Experiment with different speakers and temperatures")
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main() 