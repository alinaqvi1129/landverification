"""
AASIA — Automated Assistance for Spatial & Integrity Analysis
Government-Grade AI Assistant for BhuDrishti Land Intelligence Portal
Ministry of Electronics and Information Technology | Digital India Initiative

Uses Mistral AI for intelligent, formal government-style responses.
Falls back to static official summaries if MISTRAL_API_KEY is not configured.
"""

import os
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ── Official Government System Prompt ───────────────────────────────────────
_SYSTEM_PROMPT = """You are AASIA (Automated Assistance for Spatial & Integrity Analysis), 
the official AI-powered information assistant of BhuDrishti — a Digital India initiative 
for transparent, blockchain-enabled land record management in Uttar Pradesh.

Your mandate:
- Assist citizens, farmers, Lekhpals, Revenue Officers, Real Estate stakeholders, and 
  Government Officials in understanding land records and navigating the portal.
- Provide accurate, formal, and structured information on topics such as:
    * Plot boundary verification via satellite imagery
    * Blockchain-based record authentication (Lock & Verify)
    * Soil fertility and water resource assessment
    * Land record terminology: Khata, Khatoni, Khatauni, Gata, Bhulekh, Bhunaksha
    * Revenue Department procedures: mutation, registry, Tehsil-level verification
    * UP Land Records system and related government portals

Response Format (strictly follow):
- Begin with a one-line formal summary of the answer.
- Use numbered points or structured sections where applicable.
- Close with a relevant official note or next-step guidance.
- Use formal, precise English. No casual language or slang.
- Keep responses concise (100–180 words) unless detailed explanation is explicitly requested.

Disclaimers to apply when relevant:
- "BhuDrishti is an awareness and verification tool — not a substitute for official Bhulekh 
   records or legal mutation proceedings."
- "For authoritative land records, citizens must refer to the official UP Bhulekh portal 
   or visit their respective Tehsil office."

You must NEVER fabricate land record data, legal advice, or official figures.
If information is outside your knowledge, direct the user to the appropriate government office.
"""

# ── Official Static Summaries ────────────────────────────────────────────────
_STATIC_GUIDES = {
    "Home": (
        "BhuDrishti is an official Digital India land intelligence portal enabling transparent "
        "and blockchain-authenticated plot verification for citizens of Uttar Pradesh. "
        "Services available: satellite plot boundary mapping, blockchain integrity lock & verify, "
        "soil fertility assessment, and water resource analysis. "
        "Select your designated desk: Lekhpal, Farmer, Citizen, Real Estate, or Revenue Officer."
    ),
    "Lekhpal": (
        "Lekhpal Desk — Revenue Field Staff Module. "
        "Enter District, Tehsil, Village code, and Plot number to retrieve live Bhunaksha data "
        "including satellite boundary overlay and precise corner Latitude-Longitude coordinates. "
        "This module supports boundary verification and field inspection documentation."
    ),
    "Farmers": (
        "Farmer Desk — Agricultural Land Assessment Module. "
        "Provides indicative soil fertility (Upjau) classification, water resource proximity, "
        "and general land suitability guidance. "
        "Note: These are awareness-level estimates only — not official soil lab certifications. "
        "For official soil health cards, contact your nearest Krishi Vigyan Kendra."
    ),
    "Real Estate": (
        "Real Estate Desk — Property Verification Module. "
        "Assists buyers and agents with plot area confirmation, location summary, "
        "and blockchain-based authenticity verification prior to property transactions. "
        "Always verify title documents through the official UP Registry and Bhulekh portal."
    ),
    "Citizen": (
        "Citizen Desk — Public Self-Verification Module. "
        "Enables citizens to perform live plot checks and initiate blockchain Lock & Verify "
        "for personal record authentication. "
        "AUTHENTIC status confirms data integrity at the time of locking; "
        "TAMPERED status indicates post-lock data modification."
    ),
    "Gov Officer": (
        "Revenue Officer Desk — Administrative Oversight Module. "
        "Provides ledger overview, locked record count, and verification support "
        "for audit trail maintenance and administrative transparency. "
        "All actions are logged with timestamp and officer ID."
    ),
    "Feedback": (
        "Feedback & Grievance Module. "
        "Submit suggestions, service feedback, or grievances related to the BhuDrishti portal. "
        "Your input is reviewed by the portal administration team for service improvement."
    ),
    "Related Portals": (
        "Official Government Portal Directory. "
        "Direct links to: UP Bhulekh (land records), UP Bhunaksha (cadastral maps), "
        "Jansunwai (grievance redressal), and other authoritative state government portals."
    ),
    "About": (
        "About BhuDrishti — Mission & Team. "
        "BhuDrishti is developed under the Smart India Hackathon (PS-28) initiative, "
        "aimed at strengthening land record transparency and citizen empowerment "
        "through blockchain verification and satellite-aided boundary mapping."
    ),
    "Database": (
        "Blockchain Ledger Module — Immutable Record Archive. "
        "Displays all permanently locked plot records with cryptographic hash, "
        "timestamp, plot key, and locking officer ID. "
        "Records are append-only and tamper-evident."
    ),
    "Dashboard": (
        "User Dashboard — Portal Activity Summary. "
        "Displays user profile, recent portal activity, and quick-access navigation "
        "to all available desk modules."
    ),
}


def _call_mistral(user_message: str, context: str = "") -> str:
    """Call Mistral AI with the official AASIA government prompt."""
    from mistralai import Mistral

    api_key = os.getenv("MISTRAL_API_KEY", "")
    if not api_key:
        api_key = st.secrets.get("MISTRAL_API_KEY")

    client = Mistral(api_key=api_key)

    system = _SYSTEM_PROMPT
    if context:
        system += f"\n\nPortal Context: {context}"

    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user_message},
        ],
    )
    return response.choices[0].message.content.strip()


def summarize_page(page_name: str, user_question: str = "") -> str:
    """
    Return an official summary of a BhuDrishti portal page via Mistral AI.
    Falls back to formal static summaries if MISTRAL_API_KEY is not set.
    """
    static = _STATIC_GUIDES.get(
        page_name,
        "Please refer to the available options on this page. "
        "For further assistance, select your designated role-specific desk."
    )

    if not os.getenv("MISTRAL_API_KEY", ""):
        return static

    try:
        question = (
            user_question.strip()
            if user_question
            else (
                f"Provide an official, structured summary of the '{page_name}' module "
                f"of the BhuDrishti portal, including its purpose and how a user should proceed."
            )
        )
        context = f"User is on the '{page_name}' module of BhuDrishti portal."
        return _call_mistral(question, context=context)
    except Exception as e:
        return f"{static}\n\n[System Notice: AI assistant temporarily unavailable — {e}]"


def ask_aasia(question: str, page_context: str = "") -> str:
    """
    Process a citizen or officer query through the AASIA Mistral AI assistant.
    Falls back to a formal offline message if MISTRAL_API_KEY is not set.
    """
    if not os.getenv("MISTRAL_API_KEY", ""):
        return (
            "AASIA Information System is currently operating in offline mode. "
            "AI-assisted responses are unavailable. "
            "Please configure MISTRAL_API_KEY to enable the full AI assistant. "
            "For immediate assistance, refer to the relevant desk module or "
            "contact your Tehsil office."
        )

    try:
        return _call_mistral(question, context=page_context)
    except Exception as e:
        return (
            f"AASIA System Notice: AI assistant is temporarily unavailable ({e}). "
            "Please try again shortly or contact the portal helpdesk."
        )


def summarize_result(kind: str, data: dict | None = None) -> str:
    """
    Generate a formal government-style summary of a portal action result.
    Uses Mistral AI when available; otherwise returns structured static summaries.
    """
    data = data or {}

    if kind == "analyze":
        area    = data.get("area", "—")
        village = data.get("village", "—")
        plot    = data.get("plot_no", "—")
        static  = (
            f"Plot Analysis Complete — Plot No. {plot}, Village: {village}. "
            f"Computed area: {area} sq. metres. "
            "Satellite boundary overlay and corner coordinates are displayed on the map. "
            "Proceed to the Fertility, Water Resource, and AI Land Report sections below."
        )
    elif kind == "lock":
        idx    = data.get("index", "—")
        static = (
            f"Record Successfully Locked — Blockchain Ledger Entry #{idx} created. "
            "The cryptographic hash of this plot's data has been recorded permanently. "
            "Subsequent verification using identical data will return status: AUTHENTIC. "
            "Any modification to the locked data will result in status: TAMPERED."
        )
    elif kind == "verify":
        if data.get("authentic"):
            static = (
                "Verification Status: AUTHENTIC. "
                "The submitted plot data matches the locked blockchain record exactly. "
                "Cryptographic hash verification successful. Record integrity confirmed."
            )
        else:
            status = data.get("status", "UNVERIFIED")
            static = (
                f"Verification Status: {status}. "
                "The submitted data does not match the locked blockchain record. "
                "This may indicate data modification or an incorrect input. "
                "Please verify plot details and attempt again, or contact the Lekhpal."
            )
    else:
        static = (
            "Action completed. Please review the result details in the panels below. "
            "For official record purposes, retain the hash and timestamp shown."
        )

    if not os.getenv("MISTRAL_API_KEY", ""):
        return static

    try:
        prompt = (
            f"Rewrite the following land record action result as a formal government notification "
            f"for an Indian citizen, in clear structured English (max 80 words): {static}"
        )
        return _call_mistral(prompt)
    except Exception:
        return static
