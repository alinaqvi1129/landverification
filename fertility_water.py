"""
fertility_water.py — AI-powered Fertility & Water Resource Analysis
Uses Mistral AI to generate real insights from plot location data.
Falls back to structured prototype estimates if API key is not set.
"""

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _call_mistral_text(prompt: str) -> str:
    """Call Mistral AI for text analysis."""
    from mistralai import Mistral
    api_key = os.getenv("MISTRAL_API_KEY", "")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not set")
    client = Mistral(api_key=api_key)
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an agricultural and land assessment expert for Indian farmland. "
                    "Provide formal, structured analysis for government land portals. "
                    "Always reply in English with short, precise statements."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()


def estimate_fertility(coords, ai_text=None):
    """
    Estimate soil fertility (Upjau) for a plot using Mistral AI.
    Falls back to structured prototype estimate if API unavailable.

    Args:
        coords: List of [lon, lat] coordinate pairs for the plot polygon.
        ai_text: Optional pre-computed AI text (overrides API call if provided).
    """
    if ai_text and "fertility" in str(ai_text).lower():
        return str(ai_text)

    # Default structured fallback
    fallback = {
        "level": "Medium",
        "reason": (
            "Based on the plot location in the Indo-Gangetic Plain region, "
            "soil fertility is estimated as moderate — typical for Uttar Pradesh agricultural land. "
            "Alluvial soil composition suggests moderate nitrogen and phosphorus levels."
        ),
        "ndvi_note": (
            "Real-time NDVI score from Sentinel-2 (Red + NIR bands) can provide "
            "an accurate fertility index. Connect Copernicus API for live data."
        ),
        "crop_suitability": "Wheat, Mustard, Sugarcane, Paddy (seasonal rotation recommended)",
        "source": "Prototype estimate — Mistral AI offline",
    }

    if not os.getenv("MISTRAL_API_KEY", ""):
        return fallback

    try:
        # Use centroid coordinates for context
        if coords and len(coords) > 0:
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            centroid_lat = sum(lats) / len(lats)
            centroid_lon = sum(lons) / len(lons)
        else:
            centroid_lat, centroid_lon = 25.45, 81.84  # Prayagraj default

        prompt = (
            f"Analyze agricultural soil fertility for a plot located at approximately "
            f"Latitude {centroid_lat:.4f}, Longitude {centroid_lon:.4f} in Uttar Pradesh, India.\n\n"
            "Provide a JSON-style structured assessment with these exact keys:\n"
            "- level: (High / Medium / Low)\n"
            "- reason: (2-sentence explanation based on geography)\n"
            "- ndvi_note: (one sentence about NDVI refinement)\n"
            "- crop_suitability: (2-3 suitable crops for this region)\n\n"
            "Reply ONLY with a Python dict literal. No markdown. No code fences."
        )

        raw = _call_mistral_text(prompt)

        # Try to parse as dict
        import ast
        # Strip code fences if present
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:-1]).strip()
        result = ast.literal_eval(raw)
        result["source"] = "Mistral AI Analysis"
        return result

    except Exception as e:
        fallback["source"] = f"Prototype fallback (AI error: {e})"
        return fallback


def detect_water_resources(coords, ai_text=None):
    """
    Detect nearby water resources for a plot using Mistral AI geographic knowledge.
    Falls back to structured prototype if API unavailable.

    Args:
        coords: List of [lon, lat] coordinate pairs for the plot polygon.
        ai_text: Optional pre-computed AI text (overrides API call if provided).
    """
    if ai_text and "water" in str(ai_text).lower():
        return str(ai_text)

    # Default structured fallback
    fallback = {
        "nearby_water": "Canal / river system likely within 1–5 km (UP Gangetic region)",
        "note": (
            "Uttar Pradesh has an extensive canal irrigation network (Ganga, Yamuna, Ghaghra basins). "
            "Check the satellite map for visible water bodies near the plot."
        ),
        "irrigation_hint": (
            "Tube-well irrigation is common in this region. "
            "Check with local Irrigation Department for canal connection eligibility."
        ),
        "water_table_depth": "Estimated 5–15 metres (varies by sub-district)",
        "source": "Prototype estimate — Mistral AI offline",
    }

    if not os.getenv("MISTRAL_API_KEY", ""):
        return fallback

    try:
        if coords and len(coords) > 0:
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            centroid_lat = sum(lats) / len(lats)
            centroid_lon = sum(lons) / len(lons)
        else:
            centroid_lat, centroid_lon = 25.45, 81.84

        prompt = (
            f"Analyze water resources for agricultural land at approximately "
            f"Latitude {centroid_lat:.4f}, Longitude {centroid_lon:.4f} in Uttar Pradesh, India.\n\n"
            "Provide a Python dict with these exact keys:\n"
            "- nearby_water: (nearest river/canal name and estimated distance)\n"
            "- note: (2-sentence description of the water situation)\n"
            "- irrigation_hint: (practical irrigation advice for this region)\n"
            "- water_table_depth: (estimated groundwater depth in metres)\n\n"
            "Reply ONLY with a Python dict literal. No markdown. No code fences."
        )

        raw = _call_mistral_text(prompt)

        import ast
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:-1]).strip()
        result = ast.literal_eval(raw)
        result["source"] = "Mistral AI Analysis"
        return result

    except Exception as e:
        fallback["source"] = f"Prototype fallback (AI error: {e})"
        return fallback


if __name__ == "__main__":
    # Quick test
    test_coords = [[82.068, 25.007], [82.069, 25.007], [82.069, 25.009], [82.068, 25.009]]
    print("Fertility:", estimate_fertility(test_coords))
    print("Water:", detect_water_resources(test_coords))