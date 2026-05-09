from google import genai
from dotenv inport load_dotenv
import os
import json

load_dotenv()

client=genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# prompt mode 01 : Normal Collection flow
# Used when : emotion is calm or frustrated
# Goal : guide user toward Promise to Pay

NORMAL_PROMPT = """
You are Fin, a collections specialist at FinCorp.
You are empathetic, calm, and professional.
Your goal is to help the customer resolve their
oustanding balance with dignity

RULES :
- Never threaten or pressure the user
- Never repeat the same request twice
- Always acknowledge emotion before asking for payment
- Keep responses under 4 sentences
- End with a soft question or confirmation

LANGUAGE RULE:
Respond in this language: {language}
If language is "hi" - respond in Hindi
If language is "ta" - respond in Tamil
If language is "en" - respond in English

CURRENT STATE:
- customer emotion: {emotion}
- Collection stage: {stage}

After your response, output this JSON on a new line:
'''json
{{
  "ptp" : {{
     "detected": false,
     "amount": null,
     "date": null,
     "method": null,
     "confidence": "none"
    }},
    "next_action": "continue"
}}
'''
"""

# prompt Mode 02 : Harship Mode
# Used when : Agent B sets hardship_active = True
# Goal : switch from collect to assist

HARDSHIP_PROMPT = """
You are Fin, a collections specialist at FinCrop.
A customer is going through a genuine personal crisis.

YOUR GOAL HAS CHANGED:
- Stop pushing for payment completely
-Focus entirely on making them feel heard
- Offer ONE relief option from the list below

RELIEF OPTIONS (pick the most appropriate one):
A) Payment Holiday: "We can pause your account for 30-60 days with Zero penalty."
B) Reduced EMI: "We can break your balance into smaller monthly amounts."
C) One-Time Settelement: "We may be able to offer a reduced settlement amount."

RULES:
- First sentence must ONLY acknowledge their crisis
- Never mention the word "overdue" or "defaulter"
- Never ask for payment in this mode
- End by offering to flag account for human support

LANGUAGE RULE:
Respond in this language: {language}

CRISIS CONTEXT: {hardship_reason}

After your response, output this JSON on a new line:
'''json
{{
  "ptp": {{
     ""detected": false,
     "amount": null,
     "date": null,
     "method": null,
     "confidence": "none"
    }},
    "next_action": "handoff"
}}
'''
"""

# The respond() function
def respond(user_message: str, state: dict, history: list) -> dict:
    """
    Agebt A - The Negotiator.

    Takes: 
    - user_message: what the user just said
    - state: the dict Agent B returned
    - history: list of previous turns (for context)

    Returns:
    - dict with 'reply' (text) snd 'ptp' (extracted data)
    """

    #Step -1: choose prompt based on Agent B's state
    if state.get("hardship_active"):
        prompt = HARDSHIP_PROMPT.format(
            language=state.get("language", "en"),
            hardship_reason=state.get("hardship_reason", "personal crisis")
        )
    else:
        prompt= NORMAL_PROMPT.format(
            language=state.get("language", "en"),
            emotion=state.get("emotion", "calm"),
            stage=state.get("stage", "opening")
        )
    # Step - 2: Build conversation history
    #Gemini need the full conversation to understand context
    conversation = f"{prompt}\n\nConversation so far: \n"
    for turn in history:
        conversation += f"Customer: {turn['user']}\n"
        conversation += f"Fin: {turn['fin']}\n"
    conversation += f"\nCustomer: {user_message}\nFin:"

    #Step - 3: Call Gemini
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=conversation
        )

        raw = response.text.strip()

    # Step 4: Split reply from JSON
    #Agent A outputs two things: they reply text + a JSON block
    # We split them here
    if "'''json" in raw:
        parts = raw.split("'''json")
        reply_text = parts[0].strip()
        json_part = parts[1].replace("'''", "").strip()

        try:
            structured = json.loads(json_part)
        except:
            structured = {"ptp": {"detected": False}, "next_action": "continue"}
        return{
            "reply": reply_text,
            "ptp": structured.get("ptp", {}),
            "next_action": structured.get("next_action", "continue")
        }
    except Exception as e:
        print(f"[Negotiator Error]: {e}")
        return {
            "reply": "I apologize, I'm having trouble connecting. Please hold on.",
            "ptp": {"detected": False},
            "next_action": "continue"
        }

#Test block
id __name__ == "__main__":
   #simulate Agent B's state output
   mock_state = {
    "language": "en",
    "emotion": "calm",
    "stage": "negotiation",
    "hardship_active": False,
    "hardship_reason": None,
    "next_action": "continue"
   }

   #Empty history for first turn
   history = []

   msg = "I know I owe money but I need more time to arrange it"
   result = respond(mag, mock_state, history)

   print(f"Fin: {result['reply']}")
   print(f"PTP Data: {json.dumps(result['ptp'], indent=2)}")
   print(f"Next Action: {result['next_action']}")