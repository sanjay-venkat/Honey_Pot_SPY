import os, requests
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from state_struct import State
from utils import intent_agent, persona_agent, chat_agent, extractor_agent

API_KEY = os.getenv("API_KEY")  # set in Render environment

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

global_state = State()

@app.before_request
def check_api_key():
    if request.endpoint == 'invocation':
        key = request.headers.get("x-api-key")
        if key != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401

@app.route('/')
def health_check():
    return jsonify({'status': 'Flask is running'}), 200

@app.route('/invocation', methods=['POST'])
@cross_origin()
def invocation():
    global global_state

    data = request.get_json()
    session_id = data.get("sessionId")
    message_text = data["message"]["text"]

    # Update state
    global_state["sessionId"] = session_id
    global_state["input_message"] = message_text

    # Run agents
    global_state = intent_agent(global_state)
    global_state = persona_agent(global_state)
    global_state = chat_agent(global_state)
    global_state = extractor_agent(global_state)

    # If chat closed, send final result to GUVI
    if global_state["close_chat"]:
        payload = {
            "sessionId": global_state["sessionId"],
            "scamDetected": global_state["scamDetected"] == "True",
            "totalMessagesExchanged": global_state["totalMessagesExchanged"],
            "extractedIntelligence": {
                "bankAccounts": global_state["bankAccounts"],
                "upiIds": global_state["upiIds"],
                "phishingLinks": global_state["phishingLinks"],
                "phoneNumbers": global_state["phoneNumbers"],
                "suspiciousKeywords": global_state["suspiciousKeywords"]
            },
            "agentNotes": global_state["agentNotes"]
        }
        try:
            requests.post(
                "https://hackathon.guvi.in/api/updateHoneyPotFinalResult",
                json=payload,
                timeout=5
            )
        except Exception as e:
            print("Callback failed:", e)

    # Return hackathon‑expected format
    return jsonify({
        "status": "success",
        "reply": global_state["last_response"]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8004, use_reloader=False)
