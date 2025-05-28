"""
Status and health check API routes
"""
import sys
import time
import psutil
from pathlib import Path
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.models.responses import StatusResponse
from api import __version__

router = APIRouter(prefix="/api/v1", tags=["Status"])

# Track startup time
startup_time = time.time()

@router.get("/status", response_model=StatusResponse)
async def get_system_status():
    """
    Get comprehensive system status
    """
    try:
        # Calculate uptime
        uptime = time.time() - startup_time
        
        # Get memory usage
        memory_info = psutil.virtual_memory()
        memory_usage = {
            "total_gb": round(memory_info.total / (1024**3), 2),
            "available_gb": round(memory_info.available / (1024**3), 2),
            "used_gb": round(memory_info.used / (1024**3), 2),
            "percent": memory_info.percent
        }
        
        # Test provider availability
        providers = await _check_all_providers()
        
        return StatusResponse(
            status="healthy",
            version=__version__,
            providers=providers,
            uptime_seconds=uptime,
            memory_usage=memory_usage
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {e}")

@router.get("/health")
async def health_check():
    """
    Simple health check endpoint
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "uptime_seconds": time.time() - startup_time
    }

@router.get("/providers")
async def get_all_providers():
    """
    Get detailed provider information
    """
    try:
        providers = await _check_all_providers()
        return providers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get providers: {e}")

async def _check_all_providers() -> Dict[str, Dict[str, Any]]:
    """Check availability of all providers"""
    providers = {
        "stt": {},
        "llm": {},
        "tts": {}
    }
    
    # Check STT providers
    try:
        from sonanima.stt.engine import SonanimaStt
        stt_engine = SonanimaStt()
        
        for provider in ["openai_whisper", "whisper_cpp", "vosk", "speech_recognition", "faster_whisper"]:
            try:
                # Test basic availability
                available = hasattr(stt_engine, f'_setup_{provider}')
                providers["stt"][provider] = {
                    "available": available,
                    "type": "stt",
                    "description": f"{provider.replace('_', ' ').title()} STT provider"
                }
            except Exception:
                providers["stt"][provider] = {
                    "available": False,
                    "type": "stt",
                    "description": f"{provider.replace('_', ' ').title()} STT provider"
                }
    except Exception:
        providers["stt"]["error"] = {"available": False, "error": "STT engine not available"}
    
    # Check LLM providers
    try:
        from sonanima.core.companion import SonanimaCompanion
        companion = SonanimaCompanion()
        
        for provider in ["anthropic", "openai", "ollama"]:
            try:
                original_provider = companion.llm_provider
                companion.llm_provider = provider
                companion._setup_llm()
                available = companion.llm_client is not None
                companion.llm_provider = original_provider
                companion._setup_llm()
                
                providers["llm"][provider] = {
                    "available": available,
                    "type": "llm",
                    "description": f"{provider.title()} LLM provider"
                }
            except Exception:
                providers["llm"][provider] = {
                    "available": False,
                    "type": "llm",
                    "description": f"{provider.title()} LLM provider"
                }
    except Exception:
        providers["llm"]["error"] = {"available": False, "error": "LLM engine not available"}
    
    # Check TTS providers
    try:
        from sonanima.tts.engine import SonanimaTts
        tts_engine = SonanimaTts()
        
        for provider in ["elevenlabs", "pyttsx3", "system"]:
            try:
                available = hasattr(tts_engine, f'_setup_{provider}')
                providers["tts"][provider] = {
                    "available": available,
                    "type": "tts",
                    "description": f"{provider.title()} TTS provider"
                }
            except Exception:
                providers["tts"][provider] = {
                    "available": False,
                    "type": "tts",
                    "description": f"{provider.title()} TTS provider"
                }
    except Exception:
        providers["tts"]["error"] = {"available": False, "error": "TTS engine not available"}
    
    return providers

@router.get("/metrics")
async def get_system_metrics():
    """
    Get detailed system metrics
    """
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "percent": round((disk.used / disk.total) * 100, 1)
            },
            "uptime_seconds": time.time() - startup_time
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {e}") 