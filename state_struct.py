class State(dict):
    def __init__(self):
        super().__init__({
            "input_message": "",
            "scamDetected": None,
            "persona": [],
            "last_response": [],
            "conversation_history": [],
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