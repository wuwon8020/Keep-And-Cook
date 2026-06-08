import streamlit as st
import openai as OpenAI
import Receipt
import kitchen
import refrigator

st.title("Keep And Cook")
page = st.sidebar.radio(
    "항목 선택",
    (   "main",
        "Receipt",
        "Refrigator",
        "Kitchen"
    )
)