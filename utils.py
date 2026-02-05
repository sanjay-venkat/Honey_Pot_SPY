from state_struct import State
import os, re, json

# openai_api_key = os.environ.get('OPENAI_API_KEY')
# if not openai_api_key:
#     raise ValueError("Please set the OPENAI_API_KEY environment variable with your valid OpenAI API key. You can get one from https://platform.openai.com/account/api-keys.")

# os.environ['OPENAI_API_KEY'] = openai_api_key

from langchain_openai import ChatOpenAI
from langchain_classic.memory import ConversationBufferMemory

# llm = ChatOpenAI(model_name = "gpt-4o", verbose = False)

import os
from langchain_openai import ChatOpenAI

# Load your OpenAI API key from environment
openai_api_key = os.environ.get('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError("Please set the OPENAI_API_KEY environment variable with your valid OpenAI API key.")

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=openai_api_key)
# from langchain_google_genai import ChatGoogleGenerativeAI
# llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

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

        Message:{message}
    """
    response = llm.invoke(prompt).content.strip()
    state["scamDetected"] = response
    return state


def persona_agent(state: State):

    scam_text = state["input_message"]
    prompt = f"""
        You are an expert at identifying online scams and selecting personas for interacting with scammers.
        Example scenarios:
        1. UPI/Bank Payment Scam Related or similar scenario:
            age: Old,
            emotion: Slightly confused,
            language: Polite,
            tech_knowledge: Low,

        2. Job Offer/ Internship Scam Related or similar scenario: 
            age: Fresh graduate,
            emotion: Excited but unsure,
            language: Curious, asking questions,
            tech_knowledge: Moderate,
            why: Scammer sends links, payment pages, fake offer letters
        
        3. Lottery / Prize / Gift Scam Related or similar scenario: 
            age: Middle-aged,
            emotion: Very excited,
            language: Family-oriented,
            tech_knowledge: Low,
            why: Scammer shares more documents and bank details
        
        4. Customer Care / Refund Scam Related or similar scenario: 
            age: Working professional,
            emotion: Impatient but cooperative,
            language: Direct,
            tech_knowledge: Moderate,
            why: Scammer sends phishing links and APKs fast
        
        5. Romance / Social Media Scam Related or similar scenario: 
            age: Lonely adult,
            emotion: Emotionally open,
            language: Friendly, chatty,
            tech_knowledge: Moderate,
            why: Long conversations → rich intelligence gathering
        
        6. Courier/Customs / Legal Threat Scam Related or similar scenario: 
            age: Anxious adult,
            emotion: Scared, nervous,
            language: Polite, seeking help,
            tech_knowledge: Low,
        
        Scam message:{scam_text}

        Identify which of the 6 scenarios this scam matches and provide the persona traits (age, emotion, language, tech_knowledge) in string format in one line.

        Example output: Old age, have emotion like slightly confused, be polite, tech_knowledge is low
        """
    response = llm.invoke(prompt).content.strip()
    state["persona"]= response
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
        Generate only the reply text. Do not include labels or meta-talk
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

