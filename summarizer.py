import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()

@st.cache_data(ttl=86400)  # Cache for 24 hours since summaries don't change
def summarize_text(text):
    """Summarize text using Google's Gemini model."""
    try:
        model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        
        prompt = f"""
        Summarize the following text in 3-5 sentences. Keep it professional and informative.
        
        Text:
        {text}
        
        Instructions:
        1. Focus on the main points and key information
        2. Use clear and concise language
        3. Maintain the original meaning
        4. Include relevant technical terms and their simple explanations
        5. Format the summary in markdown
        """
        
        response = model.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        return f"[Could not summarize content: {str(e)}]"
