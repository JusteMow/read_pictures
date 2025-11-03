"""
Processors OCR et export pour l'application ReadPicture.

Architecture :
- BaseProcessor : Classe abstraite définissant l'interface commune
- TesseractProcessor : OCR local avec Tesseract
- GoogleCloudProcessor : OCR via Google Cloud Vision API
- DocumentAIProcessor : OCR via Google Document AI (spécialisé documents structurés)
- ChatGPTProcessor : OCR via ChatGPT Vision (GPT-4o-mini, performant pour tableaux complexes)
- ExportProcessor : Logique d'export CSV (utilisée par tous les processors)
"""

from .base_processor import BaseProcessor
from .tesseract_processor import TesseractProcessor
from .google_cloud_processor import GoogleCloudProcessor
from .document_ai_processor import DocumentAIProcessor
from .chatgpt_processor import ChatGPTProcessor

__all__ = ["BaseProcessor", "TesseractProcessor", "GoogleCloudProcessor", "DocumentAIProcessor", "ChatGPTProcessor"]


