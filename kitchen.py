import streamlit as st
import json
from openai import OpenAI
from tavily import TavilyClient

def app():
    if "food_item" not in st.session_state or len(st.session_state.food_item) == 0:
        st.error("냉장고에 재료가 없습니다. 먼저 재료를 추가해주세요.")
        return 
    items = st.session_state.food_item
    if "api_key" not in st.session_state or st.session_state.api_key == "":
        st.error("OpenAI API Key가 없습니다. API Key를 입력해주세요.")
        return 
    openai_key = st.session_state.api_key

    if "tavily_key" not in st.session_state or st.session_state.tavily_key == "":
        st.error("Tavily API Key가 없습니다. API Key를 입력해주세요.")
        return 
    
    tavily_key = st.session_state.tavily_key
    # 1. 유통기한 남은 재료 전체 필터링 및 임박순 정렬
    valid_items = [item for item in items if isinstance(item.get('dDay'), int) and item['dDay'] >= 0]
    
    if not valid_items:
        return "유통기한이 남은 재료가 없습니다.", None
    
    sorted_items = sorted(valid_items, key=lambda x: x['dDay'])
    
    # 전체 재료 스캔 (AI가 우선순위를 알 수 있도록 D-Day 정보 포함)
    ingredient_info = [f"{item['name']}(D-{item['dDay']})" for item in sorted_items]
    ingredient_names = [item['name'] for item in sorted_items]

    # 2. OpenAI를 통해 전체 재료를 활용한 2~3개 레시피 아이디어 추출 (JSON 형식)
    client = OpenAI(api_key=openai_key)
    
    prompt = f"""
    냉장고에 있는 전체 재료 목록과 남은 유통기한: {', '.join(ingredient_info)}
    
    위 재료들을 스캔하여, 유통기한이 임박한(D-Day가 적은) 재료를 우선적으로 소비할 수 있는 자취생 맞춤형 요리 레시피를 2~3개 추천해줘.
    ingredients 필드에서는 무조건 전체 재료 목록에 있는 이름 그대로를 사용해야해
    반드시 아래 JSON 형식에 맞게 답변해줘:
    {{
        "recipes": [
            {{
                "title": "요리 이름",
                "ingredients": ["재료1", "재료2", "..."],
                "content": "1. 단계별 조리법...\n2. ...",
                "search_keyword": "유튜브와 블로그에서 이 요리를 찾기 위해 검색할 명확한 요리 이름 키워드"
            }}
        ]
    }}
    """
    
    try:
        # JSON 형태로 응답을 강제하여 데이터 파싱을 쉽게 만듦
        response = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        
        result = json.loads(response.choices[0].message.content)
        recipes = result.get("recipes", [])
        
    except Exception as e:
        return f"레시피 생성 중 오류 발생: {str(e)}", None

    # 3. 추출된 각 레시피의 검색 키워드로 Tavily 검색 수행 (영상 및 링크 확보)
    tavily = TavilyClient(api_key=tavily_key)
    
    for recipe in recipes:
        recipe['youtube_url'] = None
        recipe['blog_url'] = None
        keyword = recipe.get('search_keyword', recipe['title'])
        
        try:
            # 유튜브 검색
            yt_search = tavily.search(query=f"{keyword} 레시피 site:youtube.com", search_depth="basic", max_results=1)
            if yt_search['results']:
                recipe['youtube_url'] = yt_search['results'][0]['url']
                
            # 블로그/웹 검색
            web_search = tavily.search(query=f"{keyword} 간단 레시피", search_depth="basic", max_results=1)
            if web_search['results']:
                recipe['blog_url'] = web_search['results'][0]['url']
        except Exception:
            pass # 검색 실패 시 해당 레시피의 링크만 None으로 유지하고 계속 진행
            
    # 4. Streamlit 화면 출력
    st.subheader("사용 가능한 재료")
    st.write(", ".join(ingredient_names))

    st.subheader("추천 레시피")

    if len(recipes) == 0:
        st.info("추천된 레시피가 없습니다.")
        return recipes, ingredient_names

    for i, recipe in enumerate(recipes, start=1):
        st.markdown(f"### {i}. {recipe.get('title', '이름 없음')}")

        st.write("사용 재료")
        st.write(", ".join(recipe.get("ingredients", [])))

        st.write("조리법")
        st.write(recipe.get("content", ""))

        youtube_url = recipe.get("youtube_url")
        blog_url = recipe.get("blog_url")

        col1, col2 = st.columns(2)

        with col1:
            if youtube_url:
                st.link_button("유튜브 레시피 보기", youtube_url)
            else:
                st.caption("유튜브 링크 없음")

        with col2:
            if blog_url:
                st.link_button("블로그 레시피 보기", blog_url)
            else:
                st.caption("블로그 링크 없음")

        st.divider()

