"""
Sonanima - Voice Companion with Memory and Emotion
"""

__version__ = "0.1.0"
__author__ = "Sonanima Project"

from .core.companion import SonanimaCompanion
from .memory.vector_store import SonanimaMemory
from .tts import SonanimaTts
from .stt import SonanimaStt

__all__ = ['SonanimaCompanion', 'SonanimaMemory', 'SonanimaTts', 'SonanimaStt'] 