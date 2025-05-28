"""
Conversation API routes - Full voice pipeline
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

from sonanima.core.companion import SonanimaCompanion
from api.models.requests import ConversationRequest
from api.models.responses import ConversationResponse

router = APIRouter(prefix="/api/v1/conversation", tags=["Conversation"])

# Global companion instance
companion = None

def get_companion():
    """Get or create companion instance"""
    global companion
    if companion is None:
        companion = SonanimaCompanion()
    return companion

@router.post("/", response_model=ConversationResponse)
async def process_conversation(request: ConversationRequest):
    """
    Process full conversation: audio/text input → STT → LLM → TTS → audio output
    """
    start_time = time.time()
    processing_times = {}
    
    try:
        # Get companion
        comp = get_companion()
        
        # Override providers if specified
        if request.stt_provider and comp.stt:
            comp.stt.provider = request.stt_provider
        if request.llm_provider and comp.llm:
            comp.llm.provider = request.llm_provider
        if request.tts_provider and comp.tts:
            comp.tts.provider = request.tts_provider
        
        transcription = None
        
        # Handle input (audio or text)
        if request.audio_data:
            # Process audio input
            stt_start = time.time()
            
            try:
                # Decode base64 audio data
                audio_bytes = base64.b64decode(request.audio_data)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid base64 audio data: {e}")
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name
            
            try:
                # Load and transcribe audio
                import soundfile as sf
                audio_data, sample_rate = sf.read(temp_path)
                
                if comp.stt:
                    transcription = comp.stt.transcribe_audio(audio_data)
                else:
                    raise HTTPException(status_code=500, detail="STT engine not available")
                
                processing_times["stt_ms"] = (time.time() - stt_start) * 1000
                
            finally:
                # Clean up temp file
                Path(temp_path).unlink(missing_ok=True)
                
        elif request.text_input:
            # Use text input directly
            transcription = request.text_input
            processing_times["stt_ms"] = 0
        else:
            raise HTTPException(status_code=400, detail="Either audio_data or text_input must be provided")
        
        if not transcription:
            raise HTTPException(status_code=422, detail="No transcription generated")
        
        # Generate LLM response
        llm_start = time.time()
        
        if comp.llm:
            # Use companion's conversation flow for context and memory
            if hasattr(comp, 'process_user_input'):
                response_text = comp.process_user_input(transcription)
            else:
                # Fallback to direct LLM call
                response_text = comp.llm.generate_response([
                    {"role": "user", "content": transcription}
                ])
        else:
            raise HTTPException(status_code=500, detail="LLM engine not available")
        
        processing_times["llm_ms"] = (time.time() - llm_start) * 1000
        
        if not response_text:
            raise HTTPException(status_code=422, detail="No response generated")
        
        # Generate TTS audio (if requested)
        audio_data = None
        audio_url = None
        
        if request.include_audio and comp.tts:
            tts_start = time.time()
            
            try:
                # Generate speech
                if hasattr(comp.tts, 'speak_streaming'):
                    audio_path = comp.tts.speak_streaming(
                        response_text,
                        voice=request.voice
                    )
                else:
                    audio_path = comp.tts.speak(
                        response_text,
                        voice=request.voice
                    )
                
                if audio_path and Path(audio_path).exists():
                    # Read audio file and encode as base64
                    with open(audio_path, 'rb') as audio_file:
                        audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
                    
                    audio_url = f"/api/v1/tts/audio/{Path(audio_path).name}"
                
                processing_times["tts_ms"] = (time.time() - tts_start) * 1000
                
            except Exception as e:
                # TTS failure shouldn't break the whole conversation
                processing_times["tts_ms"] = (time.time() - tts_start) * 1000
                print(f"TTS failed: {e}")
        
        # Calculate total time
        total_time = (time.time() - start_time) * 1000
        
        # Get providers used
        providers_used = {
            "stt": comp.stt.provider if comp.stt else None,
            "llm": comp.llm.provider if comp.llm else None,
            "tts": comp.tts.provider if comp.tts else None
        }
        
        return ConversationResponse(
            transcription=transcription,
            response_text=response_text,
            audio_data=audio_data,
            audio_url=audio_url,
            providers_used=providers_used,
            processing_times=processing_times,
            total_time_ms=total_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        total_time = (time.time() - start_time) * 1000
        raise HTTPException(
            status_code=500, 
            detail=f"Conversation processing failed: {str(e)}"
        )

@router.post("/text", response_model=ConversationResponse)
async def text_conversation(request: ConversationRequest):
    """
    Text-only conversation (no audio processing)
    """
    if not request.text_input:
        raise HTTPException(status_code=400, detail="text_input is required for text conversation")
    
    # Force no audio output for text-only mode
    request.include_audio = False
    request.audio_data = None
    
    return await process_conversation(request)

@router.get("/status")
async def get_conversation_status():
    """Get conversation system status"""
    try:
        comp = get_companion()
        
        return {
            "status": "ready",
            "components": {
                "stt": {
                    "available": comp.stt is not None,
                    "provider": comp.stt.provider if comp.stt else None
                },
                "llm": {
                    "available": comp.llm is not None,
                    "provider": comp.llm.provider if comp.llm else None
                },
                "tts": {
                    "available": comp.tts is not None,
                    "provider": comp.tts.provider if comp.tts else None
                },
                "memory": {
                    "available": comp.memory is not None
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {e}") 