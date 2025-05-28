#!/usr/bin/env python3
"""
Sonanima Deployment Modes
Three deployment strategies with different latency/cost trade-offs
"""
import os
import time
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

class DeploymentMode(Enum):
    """Available deployment modes"""
    ELEVENLABS_CAI = "elevenlabs_cai"      # Ultra-fast, expensive
    HYBRID = "hybrid"                       # Balanced cost/performance  
    LOCAL = "local"                         # Privacy-first, slower

@dataclass
class ModeConfig:
    """Configuration for each deployment mode"""
    name: str
    description: str
    estimated_latency_ms: int
    cost_per_minute: float
    stt_provider: str
    llm_provider: str
    tts_provider: str
    features: list

class SonanimaModeManager:
    """Manages different deployment modes for Sonanima"""
    
    def __init__(self):
        self.current_mode: Optional[DeploymentMode] = None
        self.mode_configs = self._init_mode_configs()
        
    def _init_mode_configs(self) -> Dict[DeploymentMode, ModeConfig]:
        """Initialize configuration for each mode"""
        return {
            DeploymentMode.ELEVENLABS_CAI: ModeConfig(
                name="ElevenLabs Conversational AI",
                description="Ultra-low latency, production-ready voice agent",
                estimated_latency_ms=300,
                cost_per_minute=0.30,
                stt_provider="elevenlabs_cai",
                llm_provider="elevenlabs_cai", 
                tts_provider="elevenlabs_cai",
                features=[
                    "Sub-300ms latency",
                    "Professional turn-taking",
                    "Built-in interruption handling",
                    "Webhook integration ready"
                ]
            ),
            
            DeploymentMode.HYBRID: ModeConfig(
                name="Hybrid (Smart STT + Custom LLM + ElevenLabs TTS)",
                description="Best balance of cost, performance, and customization",
                estimated_latency_ms=1300,
                cost_per_minute=0.05,
                stt_provider="openai_whisper_api",
                llm_provider="claude_4",
                tts_provider="elevenlabs_streaming",
                features=[
                    "Smart turn-taking with feedback learning",
                    "Custom memory system",
                    "LLM choice flexibility",
                    "6x cheaper than CAI",
                    "Tool integration via webhooks"
                ]
            ),
            
            DeploymentMode.LOCAL: ModeConfig(
                name="Fully Local",
                description="Complete privacy and offline capability",
                estimated_latency_ms=2500,
                cost_per_minute=0.00,
                stt_provider="openai_whisper_local",
                llm_provider="ollama_local",
                tts_provider="pyttsx3",
                features=[
                    "Complete data sovereignty", 
                    "Offline capable",
                    "No API costs",
                    "Custom model fine-tuning",
                    "Local tool integration"
                ]
            )
        }
    
    def get_mode_info(self, mode: DeploymentMode) -> ModeConfig:
        """Get configuration info for a specific mode"""
        return self.mode_configs[mode]
    
    def compare_modes(self) -> str:
        """Generate a comparison table of all modes"""
        comparison = "🎯 Sonanima Deployment Mode Comparison\n"
        comparison += "=" * 60 + "\n\n"
        
        for mode, config in self.mode_configs.items():
            comparison += f"**{config.name}**\n"
            comparison += f"  Latency: ~{config.estimated_latency_ms}ms\n"
            comparison += f"  Cost: ${config.cost_per_minute:.2f}/minute\n"
            comparison += f"  Stack: {config.stt_provider} → {config.llm_provider} → {config.tts_provider}\n"
            comparison += f"  Features:\n"
            for feature in config.features:
                comparison += f"    • {feature}\n"
            comparison += "\n"
        
        return comparison
    
    def recommend_mode(self, priority: str = "balanced") -> DeploymentMode:
        """Recommend a mode based on user priorities"""
        recommendations = {
            "speed": DeploymentMode.ELEVENLABS_CAI,
            "cost": DeploymentMode.LOCAL,
            "privacy": DeploymentMode.LOCAL,
            "balanced": DeploymentMode.HYBRID,
            "production": DeploymentMode.ELEVENLABS_CAI,
            "development": DeploymentMode.HYBRID
        }
        
        return recommendations.get(priority, DeploymentMode.HYBRID)
    
    def get_webhook_config(self, mode: DeploymentMode) -> Dict[str, Any]:
        """Get webhook configuration for external tool integration"""
        base_config = {
            "base_url": "http://localhost:8000",
            "endpoints": {
                "chat": "/api/v1/chat",
                "voice": "/api/v1/voice", 
                "memory": "/api/v1/memory",
                "status": "/api/v1/status"
            }
        }
        
        mode_specific = {
            DeploymentMode.ELEVENLABS_CAI: {
                "integration_type": "webhook_proxy",
                "description": "Proxy requests to ElevenLabs CAI with custom memory/tools"
            },
            DeploymentMode.HYBRID: {
                "integration_type": "full_api",
                "description": "Complete API access to all Sonanima features"
            },
            DeploymentMode.LOCAL: {
                "integration_type": "local_api", 
                "description": "Local-only API for privacy-sensitive integrations"
            }
        }
        
        return {**base_config, **mode_specific[mode]}


class WebhookIntegration:
    """Webhook endpoints for external tool integration (n8n, Zapier, etc.)"""
    
    def __init__(self, mode_manager: SonanimaModeManager):
        self.mode_manager = mode_manager
        self.active_sessions = {}
    
    def create_chat_endpoint(self):
        """Create REST endpoint for chat integration"""
        # This would be implemented with FastAPI or Flask
        endpoint_spec = {
            "path": "/api/v1/chat",
            "method": "POST",
            "request_schema": {
                "message": "string",
                "session_id": "string (optional)",
                "voice_response": "boolean (default: false)"
            },
            "response_schema": {
                "response": "string",
                "session_id": "string",
                "audio_url": "string (if voice_response=true)",
                "latency_ms": "number",
                "mode": "string"
            }
        }
        return endpoint_spec
    
    def create_voice_endpoint(self):
        """Create endpoint for voice file processing"""
        endpoint_spec = {
            "path": "/api/v1/voice",
            "method": "POST", 
            "request_schema": {
                "audio_file": "multipart/form-data",
                "session_id": "string (optional)",
                "return_audio": "boolean (default: true)"
            },
            "response_schema": {
                "transcription": "string",
                "response": "string", 
                "audio_url": "string",
                "session_id": "string",
                "processing_time_ms": "number"
            }
        }
        return endpoint_spec


def demo_mode_selection():
    """Demo the mode selection and comparison system"""
    print("🎯 Sonanima Deployment Mode Demo")
    print("=" * 50)
    
    manager = SonanimaModeManager()
    
    # Show comparison
    print(manager.compare_modes())
    
    # Show recommendations
    priorities = ["speed", "cost", "privacy", "balanced"]
    print("🎯 Mode Recommendations:")
    for priority in priorities:
        recommended = manager.recommend_mode(priority)
        config = manager.get_mode_info(recommended)
        print(f"  {priority.title()}: {config.name}")
    
    print("\n🔗 Webhook Integration Examples:")
    for mode in DeploymentMode:
        webhook_config = manager.get_webhook_config(mode)
        print(f"\n{mode.value.upper()}:")
        print(f"  Type: {webhook_config['integration_type']}")
        print(f"  Description: {webhook_config['description']}")
        print(f"  Chat endpoint: {webhook_config['base_url']}{webhook_config['endpoints']['chat']}")


def generate_n8n_integration_guide():
    """Generate integration guide for n8n"""
    guide = """
# 🔗 Sonanima + n8n Integration Guide

## Architecture
```
n8n Workflow → HTTP Request → Sonanima API → Response → n8n Actions
```

## Setup Steps

### 1. Start Sonanima API Server
```bash
# Choose your mode
python -m sonanima.api --mode hybrid --port 8000
```

### 2. n8n HTTP Request Node Configuration
- **URL**: `http://localhost:8000/api/v1/chat`
- **Method**: POST
- **Headers**: `Content-Type: application/json`
- **Body**:
```json
{
  "message": "{{ $json.user_input }}",
  "session_id": "{{ $json.session_id }}",
  "voice_response": true
}
```

### 3. Example n8n Workflows

#### Voice Assistant with Email Integration
1. **Webhook Trigger** (user voice input)
2. **Sonanima Chat** (process voice → response)
3. **Conditional** (if response contains "send email")
4. **Gmail Node** (send the email)
5. **Sonanima Voice** (confirm action)

#### Smart Home Control
1. **Sonanima Voice** (listen for commands)
2. **Switch Node** (route by intent)
3. **Home Assistant** / **Philips Hue** / etc.
4. **Sonanima Response** (confirm action)

## Cost Comparison
- **ElevenLabs CAI + n8n**: $0.30/min + n8n costs
- **Sonanima Hybrid + n8n**: $0.05/min + n8n costs  
- **Sonanima Local + n8n**: $0.00/min + n8n costs

## Benefits
✅ **Clean separation**: Sonanima handles voice, n8n handles tools
✅ **Scalable**: Add unlimited integrations without touching voice code
✅ **Maintainable**: Each system does what it's best at
✅ **Cost effective**: Choose the right mode for your use case
"""
    return guide


if __name__ == "__main__":
    demo_mode_selection()
    
    print("\n" + "=" * 60)
    print(generate_n8n_integration_guide()) 