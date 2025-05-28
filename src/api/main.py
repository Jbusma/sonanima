#!/usr/bin/env python3
"""
Sonanima API Server
FastAPI-based REST API for Sonanima voice AI system
"""
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api import __version__
from api.routes import (
    stt_router,
    llm_router, 
    tts_router,
    conversation_router,
    status_router
)

# Create FastAPI app
app = FastAPI(
    title="Sonanima API",
    description="REST API for Sonanima voice AI companion system",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for n8n integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify n8n's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routers
app.include_router(status_router)
app.include_router(stt_router)
app.include_router(llm_router)
app.include_router(tts_router)
app.include_router(conversation_router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if app.debug else "An unexpected error occurred"
        }
    )

# Root endpoint
@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Sonanima API",
        "version": __version__,
        "description": "Voice AI companion system",
        "docs": "/docs",
        "health": "/api/v1/health",
        "status": "/api/v1/status"
    }

# API info endpoint
@app.get("/api")
async def api_info():
    """API information"""
    return {
        "version": __version__,
        "endpoints": {
            "conversation": "/api/v1/conversation/",
            "stt": "/api/v1/stt/transcribe",
            "llm": "/api/v1/llm/generate", 
            "tts": "/api/v1/tts/speak",
            "status": "/api/v1/status",
            "health": "/api/v1/health"
        },
        "features": [
            "Multi-provider STT (OpenAI Whisper, Whisper.cpp, etc.)",
            "Multi-provider LLM (Claude, GPT, Ollama)",
            "Multi-provider TTS (ElevenLabs, pyttsx3, system)",
            "Full conversation pipeline",
            "Memory and context management",
            "Real-time audio processing"
        ]
    }

def main():
    """Run the API server"""
    print("🚀 Starting Sonanima API Server...")
    print(f"📖 API Documentation: http://localhost:8000/docs")
    print(f"🔍 Health Check: http://localhost:8000/api/v1/health")
    print(f"📊 Status: http://localhost:8000/api/v1/status")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main() 