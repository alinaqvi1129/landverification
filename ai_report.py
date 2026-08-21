# Compatibility shim — all AI logic has moved to the ai/ package
# This file re-exports everything so existing imports continue to work.
from ai.ai_report import generate_ai_report

__all__ = ["generate_ai_report"]