import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

def get_llm(api_key: str):
    if not api_key:
        raise ValueError("Gemini API key is required")
    
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        google_api_key=api_key,
        temperature=0.0
    )
