import streamlit as st
import openai as OpenAI
import Receipt
import Kitchen
import Refrigator

st.title("Keep And Cook")
page = st.sidebar.radio(
    "항목 선택",
    (   "main",
        "Receipt",
        "Refrigator",
        "Kitchen"
    )
)
if page == "api_key 입력":
    Lab21_api.app()

elif page == "api_key":
    api_key.app()

elif page == "Receipt":
    Receipt.app()

elif page == "Refrigator":
    Refrigator.app()
    
elif page == "kitchen":
    Kitchen.app()