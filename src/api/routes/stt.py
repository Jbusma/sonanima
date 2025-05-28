"""
Speech-to-Text API routes
"""
import sys
import time
import base64
import tempfile
from pathlib import Path
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sonanima.stt.engine import SonanimaStt
from api.models.requests import STTRequest
from api.models.responses import STTResponse, ErrorResponse

router = APIRouter(prefix="/api/v1/stt", tags=["Speech-to-Text"])

# Global STT engine instance
stt_engine = None

def get_stt_engine():
    """Get or create STT engine instance"""
    global stt_engine
    if stt_engine is None:
        stt_engine = SonanimaStt()
    return stt_engine

@router.post("/transcribe", response_model=STTResponse)
async def transcribe_audio(request: STTRequest):
    """
    Transcribe audio to text using specified STT provider
    """
    start_time = time.time()
    
    try:
        # Get STT engine
        engine = get_stt_engine()
        
        # Override provider if specified
        if request.provider:
            engine.provider = request.provider
        
        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(request.audio_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 audio data: {e}")
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name
        
        try:
            # Load audio data
            import soundfile as sf
            audio_data, sample_rate = sf.read(temp_path)
            
            # Transcribe
            transcription = engine.transcribe_audio(audio_data)
            
            if not transcription:
                raise HTTPException(status_code=422, detail="No transcription generated")
            
            processing_time = (time.time() - start_time) * 1000
            
            return STTResponse(
                transcription=transcription,
                provider=engine.provider,
                processing_time_ms=processing_time
            )
            
        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
            
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        raise HTTPException(
            status_code=500, 
            detail=f"STT processing failed: {str(e)}"
        )

@router.get("/providers")
async def get_stt_providers():
    """Get available STT providers and their status"""
    try:
        engine = get_stt_engine()
        
        providers = {}
        for provider in ["openai_whisper", "whisper_cpp", "vosk", "speech_recognition", "faster_whisper"]:
            try:
                # Test if provider is available
                original_provider = engine.provider
                engine.provider = provider
                available = hasattr(engine, f'_setup_{provider}')
                engine.provider = original_provider
                
                providers[provider] = {
                    "available": available,
                    "description": f"{provider.replace('_', ' ').title()} STT provider"
                }
            except Exception:
                providers[provider] = {
                    "available": False,
                    "description": f"{provider.replace('_', ' ').title()} STT provider"
                }
        
        return {
            "current_provider": engine.provider,
            "providers": providers
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get providers: {e}") 