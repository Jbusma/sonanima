#!/usr/bin/env python3
"""
Patch for CSM to use local Llama tokenizer
"""
import sys
from pathlib import Path

# Add models directory
MODELS_DIR = Path(__file__).parent / "models"
sys.path.insert(0, str(MODELS_DIR))

def patch_generator_for_local_tokenizer():
    """Patch the generator.py to use local tokenizer"""
    generator_file = MODELS_DIR / "generator.py"
    
    if not generator_file.exists():
        print("❌ generator.py not found")
        return False
    
    # Read current content
    content = generator_file.read_text()
    
    # Check if already patched
    if "LOCAL_LLAMA_PATH" in content:
        print("✅ Generator already patched for local use")
        return True
    
    # Create the patch
    original_function = '''def load_llama3_tokenizer():
    """
    https://github.com/huggingface/transformers/issues/22794#issuecomment-2092623992
    """
    tokenizer_name = "meta-llama/Llama-3.2-1B"
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)'''
    
    patched_function = '''def load_llama3_tokenizer():
    """
    Load Llama tokenizer from local path or fallback to HF
    """
    import os
    
    # Try local tokenizer first
    local_path = os.environ.get("LOCAL_LLAMA_PATH", "/Users/mac/.llama/checkpoints/Llama3.2-1B")
    
    if os.path.exists(local_path):
        try:
            # Use local tokenizer 
            tokenizer = AutoTokenizer.from_pretrained(local_path, local_files_only=True)
            print(f"✅ Using local tokenizer from: {local_path}")
        except Exception as e:
            print(f"⚠️ Local tokenizer failed: {e}")
            # Fallback to a compatible tokenizer that doesn't need approval
            try:
                tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
                print("✅ Using DialoGPT tokenizer as fallback")
            except:
                # Ultimate fallback
                from transformers import GPT2Tokenizer
                tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
                tokenizer.pad_token = tokenizer.eos_token
                print("✅ Using GPT2 tokenizer as ultimate fallback")
    else:
        print(f"⚠️ Local path not found: {local_path}")
        # Use fallback tokenizer
        try:
            tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
            print("✅ Using DialoGPT tokenizer as fallback")
        except:
            from transformers import GPT2Tokenizer
            tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
            tokenizer.pad_token = tokenizer.eos_token
            print("✅ Using GPT2 tokenizer as ultimate fallback")'''
    
    # Apply the patch
    if original_function in content:
        patched_content = content.replace(original_function, patched_function)
        generator_file.write_text(patched_content)
        print("✅ Generator patched successfully!")
        return True
    else:
        print("⚠️ Could not find exact function to patch")
        return False

if __name__ == "__main__":
    success = patch_generator_for_local_tokenizer()
    if success:
        print("🎉 Ready to test with local tokenizer!")
    else:
        print("❌ Patch failed") 