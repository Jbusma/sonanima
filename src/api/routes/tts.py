"""
Text-to-Speech API routes
"""
import sys
import time
import base64
import tempfile
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sonanima.tts.engine import SonanimaTts
from api.models.requests import TTSRequest
from api.models.responses import TTSResponse

router = APIRouter(prefix="/api/v1/tts", tags=["Text-to-Speech"])

# Global TTS engine instance
tts_engine = None

def get_tts_engine():
    """Get or create TTS engine instance"""
    global tts_engine
    if tts_engine is None:
        tts_engine = SonanimaTts()
    return tts_engine

@router.post("/speak", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    """
    Synthesize speech from text using specified TTS provider
    """
    start_time = time.time()
    
    try:
        # Get TTS engine
        engine = get_tts_engine()
        
        # Override provider if specified
        if request.provider:
            engine.provider = request.provider
        
        # Generate speech
        if request.streaming and hasattr(engine, 'speak_streaming'):
            # Use streaming TTS
            audio_path = engine.speak_streaming(
                request.text,
                emotion=request.emotion,
                voice=request.voice
            )
        else:
            # Use regular TTS
            audio_path = engine.speak(
                request.text,
                emotion=request.emotion,
                voice=request.voice
            )
        
        if not audio_path or not Path(audio_path).exists():
            raise HTTPException(status_code=422, detail="No audio generated")
        
        processing_time = (time.time() - start_time) * 1000
        
        # Read audio file and encode as base64
        with open(audio_path, 'rb') as audio_file:
            audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
        
        return TTSResponse(
            audio_data=audio_data,
            audio_url=f"/api/v1/tts/audio/{Path(audio_path).name}",
            provider=engine.provider,
            voice=request.voice or "default",
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        raise HTTPException(
            status_code=500, 
            detail=f"TTS processing failed: {str(e)}"
        )

@router.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """
    Serve generated audio files
    """
    try:
        # Look for audio file in common output directories
        possible_paths = [
            Path("data/audio") / filename,
            Path("tests/tts/output") / filename,
            Path("/tmp") / filename
        ]
        
        for audio_path in possible_paths:
            if audio_path.exists():
                return FileResponse(
                    path=str(audio_path),
                    media_type="audio/wav",
                    filename=filename
                )
        
        raise HTTPException(status_code=404, detail="Audio file not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serve audio: {e}")

@router.get("/providers")
async def get_tts_providers():
    """Get available TTS providers and their status"""
    try:
        engine = get_tts_engine()
        
        providers = {}
        for provider in ["elevenlabs", "pyttsx3", "system"]:
            try:
                # Test if provider is available
                original_provider = engine.provider
                engine.provider = provider
                available = hasattr(engine, f'_setup_{provider}')
                engine.provider = original_provider
                
                providers[provider] = {
                    "available": available,
                    "description": f"{provider.title()} TTS provider"
                }
            except Exception:
                providers[provider] = {
                    "available": False,
                    "description": f"{provider.title()} TTS provider"
                }
        
        return {
            "current_provider": engine.provider,
            "providers": providers
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get providers: {e}")

@router.get("/voices")
async def get_available_voices():
    """Get available voices for current TTS provider"""
    try:
        engine = get_tts_engine()
        
        # Provider-specific voice lists
        voices = {
            "elevenlabs": [
                {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "description": "Young American female"},
                {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "description": "Young American female"},
                {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "description": "Young American female"}
            ],
            "pyttsx3": [
                {"id": "default", "name": "System Default", "description": "Default system voice"}
            ],
            "system": [
                {"id": "default", "name": "System Default", "description": "Default system voice"}
            ]
        }
        
        return {
            "provider": engine.provider,
            "voices": voices.get(engine.provider, [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get voices: {e}") 