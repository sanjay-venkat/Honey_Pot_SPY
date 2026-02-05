import os, requests
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from state_struct import State
from utils import intent_agent, persona_agent, chat_agent, extractor_agent

API_KEY = os.getenv("API_KEY")  # must match the key you gave GUVI

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

global_state = State()


@app.before_request
def check_api_key():
    # Secure both honeypot endpoints
    if request.endpoint in ("invocation", "root_invocation"):
        key = request.headers.get("x-api-key")
        if key != API_KEY:
            return jsonify({
                "status": "error",
                "message": "Invalid API key or malformed request"
            }), 401


@app.route('/', methods=['GET'])
def health_check():
    return jsonify({'status': 'Flask is running'}), 200


# POST on root – this is what the tester will call
@app.route('/', methods=['POST'])
@cross_origin()
def root_invocation():
    return handle_invocation()


# Explicit /invocation endpoint – for your curl tests
@app.route('/invocation', methods=['POST'])
@cross_origin()
def invocation():
    return handle_invocation()


def handle_invocation():
    global global_state

    # Safely parse JSON
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({
            "status": "error",
            "message": "INVALID_REQUEST_BODY"
        }), 400

    # Extract required fields
    session_id = data.get("sessionId")
    message = data.get("message")
    conversation_history = data.get("conversationHistory", [])
    metadata = data.get("metadata", {})

    # Validate sessionId
    if not isinstance(session_id, str) or not session_id.strip():
        return jsonify({
            "status": "error",
            "message": "INVALID_REQUEST_BODY"
        }), 400

    # Validate message structure
    if not isinstance(message, dict):
        return jsonify({
            "status": "error",
            "message": "INVALID_REQUEST_BODY"
        }), 400

    message_text = message.get("text")
    if not isinstance(message_text, str) or not message_text.strip():
        return jsonify({
            "status": "error",
            "message": "INVALID_REQUEST_BODY"
        }), 400

    # Update state
    global_state["sessionId"] = session_id
    global_state["input_message"] = message_text
    global_state["conversation_history"] = conversation_history
    global_state["metadata"] = metadata

    # Run agents
    global_state = intent_agent(global_state)
    global_state = persona_agent(global_state)
    global_state = chat_agent(global_state)
    global_state = extractor_agent(global_state)

    # Final callback if chat closed
    if global_state.get("close_chat"):
        payload = {
            "sessionId": global_state.get("sessionId"),
            "scamDetected": bool(global_state.get("scamDetected")),
            "totalMessagesExchanged": len(global_state.get("conversation_history", [])) + 1,
            "extractedIntelligence": {
                "bankAccounts": global_state.get("bankAccounts", []),
                "upiIds": global_state.get("upiIds", []),
                "phishingLinks": global_state.get("phishingLinks", []),
                "phoneNumbers": global_state.get("phoneNumbers", []),
                "suspiciousKeywords": global_state.get("suspiciousKeywords", [])
            },
            "agentNotes": global_state.get("agentNotes", "")
        }
        try:
            requests.post(
                "https://hackathon.guvi.in/api/updateHoneyPotFinalResult",
                json=payload,
                timeout=5
            )
        except Exception as e:
            print("Callback failed:", e)

    # Response in expected format
    return jsonify({
        "status": "success",
        "reply": global_state.get("last_response", "")
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8004, use_reloader=False)
