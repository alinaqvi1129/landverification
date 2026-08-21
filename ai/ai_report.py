import os
import json
import base64

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def generate_ai_report(plot_no, fertility_info, water_info, image_path=None):
    """
    Generate an AI property report using Mistral AI (Pixtral for vision).
    If MISTRAL_API_KEY is set and image_path is provided, calls Pixtral vision.
    Otherwise returns a safe mock report (demo fallback).
    """
    api_key = os.getenv("MISTRAL_API_KEY", "")

    # Mock report — always works as a safe fallback (demo / SIH mode)
    fert_level = fertility_info.get("level", "Medium") if isinstance(fertility_info, dict) else "Medium"
    water_note = (
        water_info.get("nearby_water", "Check satellite view")
        if isinstance(water_info, dict)
        else str(water_info)
    )

    mock = {
        "land_use": "Agricultural / Rural plot",
        "fertility_indication": fert_level,
        "water_resources": water_note,
        "structures": "Open land — verify on satellite imagery",
        "summary": (
            f"Plot {plot_no}: Boundary extracted and overlaid on satellite view. "
            f"Fertility indication: {fert_level}. "
            f"Water: {water_note}. "
            "Full Mistral Vision (Pixtral) can refine this when API key + map image are available."
        ),
    }

    if not api_key or image_path is None:
        return mock

    # Real Mistral Pixtral Vision call
    try:
        from mistralai import Mistral

        client = Mistral(api_key=api_key)

        # Read and base64-encode the image
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        b64 = base64.b64encode(image_bytes).decode("utf-8")

        # Detect mime type from file extension
        ext = os.path.splitext(image_path)[-1].lower()
        mime_map = {
            ".png":  "image/png",
            ".jpg":  "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }
        mime_type = mime_map.get(ext, "image/png")

        prompt = """Analyze this cadastral / land plot on satellite imagery.
Reply ONLY in pure JSON (no markdown, no code fences) with exactly these keys:
{
  "land_use": "...",
  "fertility_indication": "...",
  "water_resources": "...",
  "structures": "...",
  "summary": "..."
}"""

        response = client.chat.complete(
            model="pixtral-12b-latest",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{b64}"},
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        )

        raw_text = response.choices[0].message.content.strip()

        # Strip markdown code fences if model wraps in ```json ... ```
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            raw_text = "\n".join(
                lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            ).strip()

        parsed = json.loads(raw_text)
        return parsed

    except json.JSONDecodeError:
        raw = response.choices[0].message.content if "response" in dir() else "No response"
        mock["mistral_raw"] = raw
        mock["error"] = "Pixtral response was not valid JSON — raw text saved above."
        return mock
    except Exception as e:
        mock["error"] = str(e)
        return mock


if __name__ == "__main__":
    from extract import get_plot_coordinates
    from fertility_water import estimate_fertility, detect_water_resources

    coords = get_plot_coordinates("Prayagraj", "Koraon", "Koodar", "30")
    fert   = estimate_fertility(coords)
    water  = detect_water_resources(coords)
    report = generate_ai_report("30", fert, water)
    print("AI Report:")
    for k, v in report.items():
        print(f"  {k}: {v}")