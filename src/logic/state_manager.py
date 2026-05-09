from agents.Supervisor import classify
from agents.Negotiator import respond

#CONVERSATION STATE
#This dictionary holds everything about
#the current conversation sesion.
#it resets when a new session starts

def create_session():
    """
    Creates a fresh conversation session.
    Call this once when the user opens the app.
    """
    return{
        "history": [],     #list of {user, Fin} turns dicts
        "last_state": {},  #last classification from Agent B
        "ptp_log": [],     #all ptp attempts captured so far
        "turn_count": 0    #how many turns have happened
    }

#MAIN ORCHESTRATION FUNCTION
#This is the only funtion app.py needs.
#Everything else is handled internally

def chat(user_manager: str, session: dict) -> dict:
    """
    Orchestrates one full conversation turn.

    Flow:
    1. Agent B classifies the user message
    2. Agent A responds using that classification
    3. History is updated
    4. PTP is logged if detected
    5. Full result returned to app.py

    Takes:
    - user_message: what the user typed
    - session: the current session dict

    Returns:
    - dict with reply, state, ptp, turn_count
    """

    #STEP 1 - Agent B classifies first
    print(f"\n[Turn {session['turn_count']+1}]")
    print(f"[Agent B] Classifying: '{user_message}'")

    state= classify(user_message)
    session["last_state"]=state

    print(f"[Agent B] State: {state}")

    #STEP - 2: Agent A responds using state
    print(f"[Agent A] Generating response...")

    result= respond(
        user_message=user_message,
        state=state,
        history=session["history"]

    )

    print(f"[Agent A] Reply: {result['reply'][:60]}...")

    #STEP - 3: Update conversation history
    session["history"].append({
        "user": user_message,
        "Fin": result["reply"]
    })

    #STEP - 4: Lpg PTP if detected
    if result["ptp"].get("detected"):
        session["ptp_log"].append({
            "turn": session["turn_count"] + 1,
            "ptp": result["ptp"]
        })
        print(f"[PTP Detected]{result['ptp']}")

    #STEP - 5: Increment turn counter
    session["tuen_count"] += 1

    #STEP - 6: Return everything to app.py
    return{
        "reply": result["reply"]
        "state": state,
        "ptp": result["ptp"],
        "next_action": result["next_action"],
        "turn_count": session["turn_count"],
        "ptp_log": session["ptp_log"]
    }