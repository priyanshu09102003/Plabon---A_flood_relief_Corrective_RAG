"""
Plabon — Flood Relief assistant.
"""

import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI

from config import settings

st.set_page_config(page_title="Plabon — setup check", page_icon="🌊")
st.title("Plabon")
st.caption("Corrective RAG flood relief assistant — environment setup check")

st.markdown(
    "This page confirms Phase 1 is working. Once Phases 2-9 are built, "
    "this file becomes the real chat interface."
)

if st.button("Test Gemini connection"):
    if not settings.google_api_key or settings.google_api_key == "your_gemini_api_key_here":
        st.error("GOOGLE_API_KEY is missing. Copy .env.example to .env and add your key.")
    else:
        try:
            llm = ChatGoogleGenerativeAI(
                model=settings.grader_model,
                google_api_key=settings.google_api_key,
            )
            response = llm.invoke("Reply with one short sentence confirming you're connected.")
            st.success("Connected to Gemini successfully.")
            st.write(response.content)
        except Exception as e:
            st.error(f"Connection failed: {e}")

with st.expander("Environment summary"):
    st.write(f"Embedding model: `{settings.embedding_model}`")
    st.write(f"Grader model: `{settings.grader_model}`")
    st.write(f"Generation model: `{settings.generation_model}`")
    st.write(f"Chroma persist dir: `{settings.chroma_persist_dir}`")
