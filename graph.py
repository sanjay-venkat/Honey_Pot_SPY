# graph.py

from langgraph.graph import StateGraph, END
from state_struct import State
from utils import intent_agent, persona_agent, chat_agent, extractor_agent
import json

def build_honey_pot():
    builder = StateGraph(State)

    # Add nodes
    builder.add_node("Intent_Agent", intent_agent)
    builder.add_node("Persona_Agent", persona_agent)
    builder.add_node("Chat_Agent", chat_agent)
    builder.add_node("Extractor_Agent", extractor_agent)

    # Routing logic
    def route_from_intent(state: State):
        if state["scamDetected"]:
            return "scam"
        return "not_scam"

    def route_from_extractor(state: State):
        if state["close_chat"]:
            return "close"
        return "continue"

    # Graph structure
    builder.set_entry_point("Intent_Agent")
    builder.add_conditional_edges(
        "Intent_Agent",
        route_from_intent,
        {"scam": "Persona_Agent", "not_scam": END}
    )
    builder.add_edge("Persona_Agent", "Chat_Agent")
    builder.add_edge("Chat_Agent", "Extractor_Agent")
    builder.add_conditional_edges(
        "Extractor_Agent",
        route_from_extractor,
        {"continue": "Chat_Agent", "close": END}
    )

    graph = builder.compile()

    # Initialize state with correct types
    state: State = {
        "sessionId": "",
        "input_message": "",
        "scamDetected": False,
        "persona": "",
        "totalMessagesExchanged": 0,
        "upiIds": [],
        "phishingLinks": [],
        "phoneNumbers": [],
        "bankAccounts": [],
        "suspiciousKeywords": [],
        "agentNotes": "",
        "last_response": "",
        "conversation_history": [],
        "close_chat": False,
        "final_payload": {}
    }

    return graph, state

if __name__ == "__main__":
    input_message = input("Message: ")
    if input_message:
        graph, state = build_honey_pot()
        state["sessionId"] = "wertyu-dfghj-ertyui"
        state["input_message"] = input_message
        result = graph.invoke(state)

        payload = {
            "sessionId": result["sessionId"],
            "scamDetected": result["scamDetected"],
            "totalMessagesExchanged": result["totalMessagesExchanged"],
            "extractedIntelligence": {
                "bankAccounts": result["bankAccounts"],
                "upiIds": result["upiIds"],
                "phishingLinks": result["phishingLinks"],
                "phoneNumbers": result["phoneNumbers"],
                "suspiciousKeywords": result["suspiciousKeywords"]
            },
            "agentNotes": result["agentNotes"]
        }

        result["final_payload"] = payload
        print(json.dumps(payload, indent=2))
