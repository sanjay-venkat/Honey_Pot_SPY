class State(dict):
    def __init__(self):
        super().__init__({
            "sessionId": "",
            "input_message": "",
            "scamDetected": None,
            "persona": "",
            "last_response": "",
            "conversation_history": [],   # used everywhere
            "upiIds": [],
            "phoneNumbers": [],
            "phishingLinks": [],
            "bankAccounts": [],
            "suspiciousKeywords": [],
            "agentNotes": None,
            "totalMessagesExchanged": 0,
            "close_chat": False,
            "final_payload": {}
        })
