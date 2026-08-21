# AI module package for BhuDrishti Portal
# Contains: aasia.py (AASIA Assistant), ai_report.py (Land Report Generator)
from .aasia import summarize_page, ask_aasia, summarize_result
from .ai_report import generate_ai_report

__all__ = ["summarize_page", "ask_aasia", "summarize_result", "generate_ai_report"]
