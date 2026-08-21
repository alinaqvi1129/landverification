# Compatibility shim — all AI logic has moved to the ai/ package
# This file re-exports everything so existing imports continue to work.
from ai.aasia import summarize_page, ask_aasia, summarize_result

__all__ = ["summarize_page", "ask_aasia", "summarize_result"]
