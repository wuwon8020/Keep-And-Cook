import streamlit as st
import openai as OpenAI
import api_key
import receipt
import kitchen
import refrigator

st.title("Keep And Cook")
page = st.sidebar.radio(
    "항목 선택",
    (   "api_key",
        "Receipt",
        "Refrigator",
        "Kitchen"
    )
)

if page == "api_key":
    api_key.app()

elif page == "Receipt":
    Receipt.app()

elif page == "Refrigator":
    Refrigator.app()
    
elif page == "kitchen":
    Kitchen.app()