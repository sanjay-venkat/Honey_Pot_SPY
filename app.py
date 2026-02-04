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

    # Extract according to hackathon spec
    session_id = data.get("sessionId")
    message = data.get("message")
    conversation_history = data.get("conversationHistory", [])
    metadata = data.get("metadata", {})

    if not message or "text" not in message:
        return jsonify({"error": "INVALID_REQUEST_BODY"}), 400

    # Update state
    global_state["sessionId"] = session_id
    global_state["message"] = message
    global_state["conversationHistory"] = conversation_history
    global_state["metadata"] = metadata

    # Run agents sequentially
    global_state = intent_agent(global_state)
    global_state = persona_agent(global_state)
    global_state = chat_agent(global_state)
    global_state = extractor_agent(global_state)

    # Return hackathon-compliant response
    return jsonify({
        "status": "success",
        "reply": global_state["last_response"]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8004, use_reloader=False)
