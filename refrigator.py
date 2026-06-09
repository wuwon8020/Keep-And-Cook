import streamlit as st

def app():
    st.title("재료 목록")
    
    
    if "food_item" not in st.session_state:
        st.session_state.food_item = []
        st.error("아직 냉장고에 아무 재료도 없습니다.");
        return
    if len(st.session_state.food_item) == 0:
        st.info("저장된 재료가 없습니다.")
        return
    st.session_state.food_item.sort(key=lambda x: x["dDay"])
    for item in st.session_state.food_item:
        st.subheader(item["name"])

        st.write(f"구매일: {item['purchase_date']}")
        st.write(f"유통기한: {item['exday']}일")
        st.write(f"D-Day: {item['dDay']}일")

        if item["dDay"] <= 0:
            st.error("유통기한이 지났습니다.")
        elif item["dDay"] <= 3:
            st.warning("유통기한이 임박했습니다.")
        else:
            st.success("사용 가능")

        st.divider()