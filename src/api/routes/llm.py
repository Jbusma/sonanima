"""
LLM API routes
"""
import sys
import time
from pathlib import Path
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sonanima.core.companion import SonanimaCompanion
from api.models.requests import LLMRequest
from api.models.responses import LLMResponse

router = APIRouter(prefix="/api/v1/llm", tags=["Large Language Model"])

# Global companion instance for LLM
companion = None

def get_companion():
    """Get or create companion instance for LLM"""
    global companion
    if companion is None:
        companion = SonanimaCompanion()
    return companion

@router.post("/generate", response_model=LLMResponse)
async def generate_response(request: LLMRequest):
    """
    Generate response using specified LLM provider
    """
    start_time = time.time()
    
    try:
        # Get companion
        comp = get_companion()
        
        # Override provider if specified
        if request.provider:
            comp.llm_provider = request.provider
            comp._setup_llm()
        
        # Generate response using companion's LLM
        if comp.llm_client:
            # Use companion's LLM generation
            response_text, _ = comp._generate_llm_response(request.message, "neutral")
            response = response_text
        else:
            raise HTTPException(status_code=500, detail="LLM client not available")
        
        if not response:
            raise HTTPException(status_code=422, detail="No response generated")
        
        processing_time = (time.time() - start_time) * 1000
        
        return LLMResponse(
            response=response,
            provider=comp.llm_provider,
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        raise HTTPException(
            status_code=500, 
            detail=f"LLM processing failed: {str(e)}"
        )

@router.get("/providers")
async def get_llm_providers():
    """Get available LLM providers and their status"""
    try:
        comp = get_companion()
        
        providers = {}
        for provider in ["anthropic", "openai", "ollama"]:
            try:
                # Test if provider is available
                original_provider = comp.llm_provider
                comp.llm_provider = provider
                comp._setup_llm()
                available = comp.llm_client is not None
                comp.llm_provider = original_provider
                comp._setup_llm()
                
                providers[provider] = {
                    "available": available,
                    "description": f"{provider.title()} LLM provider"
                }
            except Exception:
                providers[provider] = {
                    "available": False,
                    "description": f"{provider.title()} LLM provider"
                }
        
        return {
            "current_provider": comp.llm_provider,
            "providers": providers
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get providers: {e}")

@router.post("/chat")
async def chat_completion(request: LLMRequest):
    """
    Chat completion endpoint (alias for generate with chat formatting)
    """
    return await generate_response(request) 