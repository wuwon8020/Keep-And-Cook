import streamlit as st
import json
from datetime import datetime, timedelta
from PIL import Image
from openai import OpenAI
import base64


def app():
    # 세션 상태 초기화
    if "food_item" not in st.session_state:
        st.session_state.food_item = []

    if "food_exday" not in st.session_state:
        st.session_state.food_exday = []

    if "temp_extracted" not in st.session_state:
        st.session_state.temp_extracted = None

    if "last_saved_items" not in st.session_state:
        st.session_state.last_saved_items = []

    if "api_key" not in st.session_state:
        st.session_state.api_key = ""

    user_openai_api_key = st.session_state.api_key

    def run_ocr_step(image_file, client):
        image_file.seek(0)
        bytes_data = image_file.read()

        base64_image = base64.b64encode(bytes_data).decode("utf-8")
        file_type = image_file.type if hasattr(image_file, "type") else "image/jpeg"

        ocr_prompt = """
당신은 아주 정밀한 OCR(광학 문자 인식) 시스템입니다.
제공된 영수증 이미지에 포함된 모든 텍스트를 위에서부터 아래로, 보이는 그대로 받아적어 주세요.
단어를 임의로 수정하거나, 요약하거나, 추론하지 말고 오직 눈에 보이는 글자만 텍스트로 반환해야 합니다.
"""

        response = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": ocr_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{file_type};base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            max_completion_tokens=1500,
        )

        return response.choices[0].message.content

    def run_inference_step(raw_text, client):
        today_str = datetime.today().strftime("%Y-%m-%d")

        inference_prompt = f"""
당신은 영수증 텍스트 데이터에서 구매일과 식재료를 정밀하게 정제하는 NLP 전문가입니다.

[영수증 텍스트]
{raw_text}

[추출 규칙]
1. 텍스트 중에서 '결제일', '승인일자', '거래일시' 등 구매 날짜를 찾아 "YYYY-MM-DD" 형식으로 추출하세요.
2. 구매 품목 중 공산품이나 비식품, 예를 들어 봉투, 세제 등은 제외하세요.
3. 식재료에 해당하는 품목명만 추출하세요.
4. 글자가 잘리거나 축약된 경우, 사람이 이해할 수 있는 온전한 식재료명으로 정제하세요.
   예: "친환경대파(특" -> "대파"
   예: "깐마늘500g" -> "마늘"
   예: "백오이(3입)" -> "오이"
5. 양념류, 가공식품이라도 식재료로 사용할 수 있으면 포함하세요.
6. 규격, 용량, 수량, 가격 정보는 제외하세요.
7. 개인정보는 절대 포함하지 마세요.
8. 구매일을 찾을 수 없다면 오늘 날짜인 {today_str}을 사용하세요.

[반환 형식]
반드시 마크다운 없이 순수 JSON 객체만 반환하세요.

{{
  "purchase_date": "YYYY-MM-DD",
  "items": ["재료명1", "재료명2"]
}}
"""

        response = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "user", "content": inference_prompt}
            ],
            response_format={"type": "json_object"},
        )

        return json.loads(response.choices[0].message.content)

    def extract_items_from_receipt(image_file, api_key):
        client = OpenAI(api_key=api_key)

        with st.spinner("1단계: 영수증에서 글자를 읽어오는 중 (OCR)..."):
            raw_text = run_ocr_step(image_file, client)

        with st.spinner("2단계: 식재료를 추론하는 중..."):
            result_json = run_inference_step(raw_text, client)

        return result_json

    def find_exday_from_cache(name):
        for item in st.session_state.food_exday:
            if item["name"] == name:
                return item["exday"]

        return None

    def save_exday_to_cache(name, exday):
        st.session_state.food_exday.append({
            "name": name,
            "exday": exday,
        })

    def guess_exday_with_openai(name, api_key):
        client = OpenAI(api_key=api_key)

        prompt = f"""
다음 식재료의 일반적인 냉장 보관 유통기한을 일수로 추정하세요.

식재료명: {name}

조건:
1. 숫자는 일수만 의미합니다.
2. 너무 길게 잡지 말고 일반적인 가정용 냉장 보관 기준으로 추정하세요.
3. 반드시 JSON 객체만 반환하세요.

반환 형식:
{{
  "name": "{name}",
  "exday": 7
}}
"""

        response = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)
        return int(result["exday"])

    def add_items(final_date, final_items_list):
        saved_items = []

        try:
            purchase_date_obj = datetime.strptime(final_date, "%Y-%m-%d").date()
        except ValueError:
            st.error("구매일 형식이 올바르지 않습니다. 예: 2026-06-09")
            return False

        today = datetime.today().date()

        for name in final_items_list:
            name = name.strip()

            if not name:
                continue

            exday = find_exday_from_cache(name)

            if exday is None:
                if not user_openai_api_key:
                    st.error(
                        f"'{name}'의 유통기한 정보가 없습니다.\n"
                        "OpenAI API Key를 먼저 입력해주세요."
                    )
                    return False

                try:
                    exday = guess_exday_with_openai(name, user_openai_api_key)
                except Exception as e:
                    st.error(
                        f"'{name}'의 유통기한 추론에 실패했습니다.\n{e}"
                    )
                    return False

                save_exday_to_cache(name, exday)

            expire_date_obj = purchase_date_obj + timedelta(days=exday)
            dday = (expire_date_obj - today).days

            item_model = {
                "name": name,
                "dDay": dday,
                "purchase_date": purchase_date_obj.strftime("%Y-%m-%d"),
                "exday": exday,
            }

            st.session_state.food_item.append(item_model)
            saved_items.append(item_model)

        st.session_state.last_saved_items = saved_items
        return True

    # UI
    st.title("Keep And Cook 🍳")
    st.subheader("영수증 재료 등록")

    uploaded_file = st.file_uploader(
        "영수증 이미지를 첨부해주세요.",
        type=["jpg", "jpeg", "png"],
    )

    if uploaded_file is not None:
        image = Image.open(uploaded_file)

        st.image(
            image,
            caption="업로드된 영수증",
            width="stretch",
        )

        if st.button("영수증에서 재료 추출하기"):
            if not user_openai_api_key:
                st.warning("OpenAI API Key를 먼저 입력해주세요!")
            else:
                extracted_data = extract_items_from_receipt(
                    uploaded_file,
                    user_openai_api_key,
                )

                if extracted_data:
                    st.session_state.temp_extracted = extracted_data
                    st.rerun()

    if st.session_state.temp_extracted is not None:
        st.markdown("---")
        st.markdown("### ✏️ AI 추출 결과 확인 및 수정")
        st.info("틀린 부분이 있다면 직접 수정한 후 [최종 냉장고에 저장] 버튼을 눌러주세요.")

        temp_date = st.session_state.temp_extracted.get(
            "purchase_date",
            datetime.today().strftime("%Y-%m-%d"),
        )

        edited_date = st.text_input(
            "🗓️ 구매일 (YYYY-MM-DD)",
            value=temp_date,
        )

        temp_items = st.session_state.temp_extracted.get("items", [])

        if not isinstance(temp_items, list):
            temp_items = []

        temp_items_str = ", ".join(temp_items)

        edited_items_str = st.text_area(
            "🛒 추출된 재료",
            value=temp_items_str,
        )

        if st.button("💾 최종 냉장고에 저장"):
            edited_items_list = [
            item.strip()
            for item in edited_items_str.split(",")
            if item.strip()
            ]

            with st.spinner("재료 유통기한을 계산하고 냉장고에 저장하는 중..."):
                success = add_items(
                    edited_date,
                    edited_items_list
                )

            if success:
                st.toast("재료가 냉장고 저장소에 저장되었습니다!")
                st.session_state.temp_extracted = None
                st.rerun()

    st.markdown("---")
    st.subheader("이번 영수증에서 저장한 재료들")

    if st.session_state.last_saved_items:
        table_data = []

        for item in st.session_state.last_saved_items:
            table_data.append({
                "재료명": item["name"],
                "D-Day": item["dDay"],
                "구매일": item["purchase_date"],
                "유통기한(일)": item["exday"],
            })

        st.dataframe(
            table_data,
            use_container_width=True,
        )
    else:
        st.info("아직 이번 영수증에서 저장한 재료가 없습니다.")