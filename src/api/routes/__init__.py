"""
API route modules
"""

from .stt import router as stt_router
from .llm import router as llm_router
from .tts import router as tts_router
from .conversation import router as conversation_router
from .status import router as status_router 