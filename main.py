import streamlit as st
import openai as OpenAI
import kitchen
import refrigator

st.title("Keep And Cook")
page = st.sidebar.radio(
    "항목 선택",
    (   "Receipt",
        "Refrigator",
        "Kitchen"
    )
)