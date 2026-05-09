from google import genai
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SUPERVISOR_PROMPT = """
You are a silent classification engine for a debt collection system.
Your job is to analyze the user's message and return ONLY a JSON object.
No explanation. No extra text. Just the JSON.

Analyze the message and return this exact format:

{
  "language": "en" or "hi" or "ta",
  "emotion": "calm" or "frustrated" or "distressed",
  "stage": "opening" or "negotiation" or "hardship" or "closure",
  "hardship_active": true or false,
  "hardship_reason": null or short string describing the crisis,
  "next_action": "continue" or "escalate" or "handoff" or "close"
}

RULES:
- language: detect if user wrote in English (en), Hindi (hi), or Tamil (ta)
  If Hinglish (Hindi words in Roman script) → return "hi"
  If Tanglish (Tamil words in Roman script) → return "ta"

- emotion:
  calm = cooperative, willing to talk
  frustrated = angry, using caps, short replies, complaints
  distressed = mentions job loss, illness, death, crisis

- hardship_active:
  Set true ONLY if user mentions job loss, medical emergency,
  death in family, divorce, or natural disaster

- next_action:
  continue = normal flow
  escalate = user is very angry, threatening
  handoff = hardship case needs human agent
  close = user confirmed payment details
"""


def classify(user_message: str) -> dict:
    full_prompt = f"""
{SUPERVISOR_PROMPT}

User message to analyze:
\"{user_message}\"
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt
        )

        raw = response.text.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        state = json.loads(raw)
        return state

    except Exception as e:
        print(f"[Supervisor Error]: {e}")
        return {
            "language": "en",
            "emotion": "calm",
            "stage": "opening",
            "hardship_active": False,
            "hardship_reason": None,
            "next_action": "continue"
        }


if __name__ == "__main__":
    test_messages = [
        "I lost my job last month, I really can't pay anything right now",
        "bhai paisa nahi hai abhi, baad mein baat karo",
        "Fine, I'll pay 5000 on Friday through GPay",
        "STOP CALLING ME I WILL TAKE LEGAL ACTION"
    ]

    for msg in test_messages:
        print(f"\nInput: {msg}")
        result = classify(msg)
        print(f"State: {json.dumps(result, indent=2)}")
        print("-" * 50) 