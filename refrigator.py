import streamlit as st
import pandas as pd

def app():
    st.title("재료 목록")

    # 다크 배경
    st.markdown("""
    <style>
    .stApp {
        background-color: #181818;
    }
    </style>
    """, unsafe_allow_html=True)

    if "food_item" not in st.session_state:
        st.session_state.food_item = []
        st.error("아직 냉장고에 아무 재료도 없습니다.")
        return

    if len(st.session_state.food_item) == 0:
        st.info("저장된 재료가 없습니다.")
        return

    # D-Day 오름차순 정렬
    sorted_items = sorted(
        st.session_state.food_item,
        key=lambda x: x["dDay"]
    )

    table_data = []

    for item in sorted_items:

        if item["dDay"] <= 0:
            status = "🔴 만료"
        elif item["dDay"] <= 3:
            status = "🟡 임박"
        else:
            status = "🟢 사용 가능"

        table_data.append({
            "재료명": item["name"],
            "구매일": item["purchase_date"],
            "유통기한(일)": item["exday"],
            "D-Day": item["dDay"],
            "상태": status
        })

    df = pd.DataFrame(table_data)

    # 상태 열만 색칠
    def color_status(val):
        if "만료" in val:
            return (
                "background-color: #8B0000;"
                "color: white;"
                "font-weight: bold;"
            )

        elif "임박" in val:
            return (
                "background-color: #B8860B;"
                "color: white;"
                "font-weight: bold;"
            )

        elif "사용 가능" in val:
            return (
                "background-color: #006400;"
                "color: white;"
                "font-weight: bold;"
            )

        return ""

    styled_df = df.style.map(
        color_status,
        subset=["상태"]
    )

    st.dataframe(
        styled_df,
        width='stretch',
        hide_index=True
    )