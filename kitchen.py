import streamlit as st
from openai import OpenAI
from datetime import datetime

def get_recipe(items):
    # 1. 유통기한 지난 재료 제외 및 정렬
    # dDay가 양수(남은 날짜)인 것만 필터링
    valid_items = [item for item in items if isinstance(item.get('dDay'), int) and item['dDay'] >= 0]
    
    if not valid_items:
        return "유통기한이 남은 재료가 없습니다.", None
    
    # dDay 기준 오름차순 정렬 (임박순)
    sorted_items = sorted(valid_items, key=lambda x: x['dDay'])
    urgent_items = sorted_items[:3]  # 상위 3개 재료만 활용
    ingredient_names = [item['name'] for item in urgent_items]

    # 2. OpenAI 프롬프트 구성
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    prompt = f"""
    냉장고에 유통기한이 임박한 재료들: {', '.join(ingredient_names)}
    이 재료들을 우선적으로 활용하여 만들 수 있는 자취생 맞춤형 요리 레시피를 추천해줘.

    요청 사항:
    1. 요리 이름
    2. 단계별 조리법 (1. ~, 2. ~ 형식으로 요약)
    3. 유튜브나 블로그에서 검색하기 좋은 추천 검색어 2개

    정중하고 친절한 어조로 작성해줘.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content, ingredient_names
    except Exception as e:
        return f"레시피 생성 중 오류 발생: {str(e)}", None
