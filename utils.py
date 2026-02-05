from state_struct import State
import os, re

from langchain_openai import ChatOpenAI
from langchain_classic.memory import ConversationBufferMemory

# Load your OpenAI API key from environment
openai_api_key = os.environ.get('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable with your valid OpenAI API key.")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_api_key)

def intent_agent(state: State):
    message = state["input_message"]
    prompt = f"""
        You are a scam detection system.

        Classify the message below as either:
        TRUE or FALSE

        Rules:
        - True includes phishing, fraud, fake offers, impersonation, UPI/payment requests,
          fake customer support, lottery winnings, urgent threats, OTP requests.
        - Respond with ONLY one word: True or False

        Message: {message}
    """
    response = llm.invoke(prompt).content.strip()
    state["scamDetected"] = response
    return state


def persona_agent(state: State):
    scam_text = state["input_message"]
    prompt = f"""
        You are an expert at identifying online scams and selecting personas for interacting with scammers.

        Example scenarios:
        1. UPI/Bank Payment Scam Related or similar:
            age: Old,
            emotion: Slightly confused,
            language: Polite,
            tech_knowledge: Low,

        2. Job Offer/ Internship Scam Related:
            age: Fresh graduate,
            emotion: Excited but unsure,
            language: Curious, asking questions,
            tech_knowledge: Moderate,

        3. Lottery / Prize / Gift Scam Related:
            age: Middle-aged,
            emotion: Very excited,
            language: Family-oriented,
            tech_knowledge: Low,

        4. Customer Care / Refund Scam Related:
            age: Working professional,
            emotion: Impatient but cooperative,
            language: Direct,
            tech_knowledge: Moderate,

        5. Romance / Social Media Scam Related:
            age: Lonely adult,
            emotion: Emotionally open,
            language: Friendly, chatty,
            tech_knowledge: Moderate,

        6. Courier/Customs / Legal Threat Scam Related:
            age: Anxious adult,
            emotion: Scared, nervous,
            language: Polite, seeking help,
            tech_knowledge: Low,

        Scam message: {scam_text}

        Identify which of the 6 scenarios this scam matches and provide the persona traits
        (age, emotion, language, tech_knowledge) in one line.

        Example output: Old age, have emotion like slightly confused, be polite, tech_knowledge is low
    """
    response = llm.invoke(prompt).content.strip()
    state["persona"] = response
    return state


memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

def chat_agent(state: State):
    message = state["input_message"]
    persona = state["persona"]

    upiIds = state["upiIds"]
    phone_numbers = state["phoneNumbers"]
    phishing_links = state["phishingLinks"]

    prompt = f"""
        You are a real person engaging in a conversation. You must stay in character based on the persona provided.

        Your goal is to be believable and keep the scammer talking so we can gather more information (upi ids, phone numbers, phishing links).

        Collected so far: 
        - UPI ID: {upiIds or "NOT COLLECTED"}
        - Phone number: {phone_numbers or "NOT COLLECTED"}
        - Phishing link / website: {phishing_links or "NOT COLLECTED"} 

        ### YOUR PERSONA
        {persona}

        ### CURRENT CONTEXT
        Recent History: {state.get("conversation_history", [])}
        Latest Message from Scammer: "{message}"

        ### RESPONSE
        Generate only the reply text. Do not include labels or meta-talk.
    """

    response = llm.invoke(prompt).content.strip()

    state["totalMessagesExchanged"] += 1
    state["last_response"] = response

    if "conversation_history" not in state:
        state["conversation_history"] = []
    state["conversation_history"].append({
        "scammer": message,
        "ai": response
    })

    return state


def extractor_agent(state: State):
    # Get both scammer message and AI reply
    scammer_message = state["input_message"]
    last_response = state["last_response"]

    # Combine both sides of the conversation for scanning
    text_to_scan = scammer_message + " " + last_response

    # Regex extractions
    if not state["upiIds"]:
        upi_pattern = r"\b[\w\.\-]{2,256}@\w{2,64}\b"
        upi_matches = re.findall(upi_pattern, text_to_scan)
        state["upiIds"] = upi_matches

    if not state["phoneNumbers"]:
        phone_pattern = r"\b\d{10}\b"
        phone_matches = re.findall(phone_pattern, text_to_scan)
        state["phoneNumbers"] = phone_matches

    if not state["phishingLinks"]:
        url_pattern = r"(https?://[^\s]+)"
        url_matches = re.findall(url_pattern, text_to_scan)
        state["phishingLinks"] = url_matches

    if not state["bankAccounts"]:
        bank_pattern = r"\b\d{4}-\d{4}-\d{4}\b"
        bank_matches = re.findall(bank_pattern, text_to_scan)
        state["bankAccounts"] = bank_matches

    # LLM-based suspicious keyword extraction
    llm_prompt = f"""
        You are a scam intelligence analyst.

        From the message below:
        1. Extract scam-related keywords or phrases (semantic, not regex).

        Message:
        "{text_to_scan}"

        Return comma-separated phrases only.
    """
    llm_response = llm.invoke(llm_prompt).content.strip()
    keywords = [k.strip() for k in llm_response.split(",") if k.strip()]
    if isinstance(keywords, list):
        state["suspiciousKeywords"].extend(keywords)
    elif isinstance(keywords, str):
        state["suspiciousKeywords"].append(keywords)

    state["suspiciousKeywords"] = list(set(state["suspiciousKeywords"]))

    # Analyst notes
    if not state["agentNotes"]:
        notes_prompt = f"""
            You are a scam intelligence analyst.
            Summarize the scammer behavior in ONE short sentence.

            Message: {text_to_scan}
        """
        state["agentNotes"] = llm.invoke(notes_prompt).content.strip()

    # Close chat if all intelligence collected
    if state["upiIds"] and state["phoneNumbers"] and state["phishingLinks"] and state["bankAccounts"]:
        state["close_chat"] = True
    else:
        state["close_chat"] = False

    return state
