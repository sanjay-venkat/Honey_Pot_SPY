from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from state_struct import State
from utils import intent_agent, persona_agent, chat_agent, extractor_agent

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Persistent state across requests
global_state = State()

@app.route('/')
def health_check():
    return jsonify({'status': 'Flask is running'}), 200

@app.route('/invocation', methods=['POST'])
@cross_origin()
def invocation():
    global global_state   # <-- important fix

    data = request.get_json()
    input_message = data.get('input_message')

    if not input_message:
        return jsonify({'error': 'Try again'}), 404

    # Update state with new scammer message
    global_state["input_message"] = input_message

    # Run agents sequentially
    global_state = intent_agent(global_state)
    global_state = persona_agent(global_state)
    global_state = chat_agent(global_state)
    global_state = extractor_agent(global_state)

    # Return full state (conversation + intelligence)
    return jsonify(global_state)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8004, use_reloader=False)