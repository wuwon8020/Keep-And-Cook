import streamlit as st

def app():
    st.title("재료 목록")
    
    st.session_state.food_items.sort(key=lambda x: x["dDay"])

    if len(st.session_state.food_items) == 0:
        st.info("저장된 재료가 없습니다.")
        return

    for item in st.session_state.food_items:
        st.subheader(item["name"])

        st.write(f"구매일: {item['purchase_date']}")
        st.write(f"유통기한: {item['expire_date']}")
        st.write(f"D-Day: {item['dDay']}일")

        if item["dDay"] <= 0:
            st.error("유통기한이 지났습니다.")
        elif item["dDay"] <= 3:
            st.warning("유통기한이 임박했습니다.")
        else:
            st.success("사용 가능")

        st.divider()