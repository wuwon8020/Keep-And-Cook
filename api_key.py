import streamlit as st
from openai import OpenAI
def app():
    st.title("202313522 최우원 Lab21과제")
    if "api_key" not in st.session_state:
        st.session_state.api_key = ""

    # API Key 입력
    st.session_state.api_key = st.text_input(
        "OpenAI API Key 입력",
        type="password",
        value=st.session_state.api_key
    )