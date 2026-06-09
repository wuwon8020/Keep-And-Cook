import streamlit as st
from openai import OpenAI

def app():
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""
    if "tavily_key" not in st.session_state:
        st.session_state.tavily_key = ""
    # API Key 입력
    st.session_state.api_key = st.text_input(
        "OpenAI API Key 입력",
        type="password",
        value=st.session_state.api_key
    )
    st.session_state.tavily_key = st.text_input(
        "Tavily API Key 입력",
        type="password",
        value=st.session_state.tavily_key 
    )   