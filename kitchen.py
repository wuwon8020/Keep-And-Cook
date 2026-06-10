import streamlit as st
import json
from openai import OpenAI
from tavily import TavilyClient

def app():
    st.title("요리 추천")

    if "food_item" not in st.session_state or len(st.session_state.food_item) == 0:
        st.error("냉장고에 재료가 없습니다. 먼저 재료를 추가해주세요.")
        return

    if "api_key" not in st.session_state or st.session_state.api_key == "":
        st.error("OpenAI API Key가 없습니다. API Key를 입력해주세요.")
        return

    if "tavily_key" not in st.session_state or st.session_state.tavily_key == "":
        st.error("Tavily API Key가 없습니다. API Key를 입력해주세요.")
        return

    items = st.session_state.food_item
    openai_key = st.session_state.api_key
    tavily_key = st.session_state.tavily_key

    valid_items = [
        item for item in items
        if isinstance(item.get("dDay"), int) and item["dDay"] >= 0
    ]

    if not valid_items:
        st.warning("유통기한이 남은 재료가 없습니다.")
        return

    sorted_items = sorted(valid_items, key=lambda x: x["dDay"])

    ingredient_info = [
        f"{item['name']}(D-{item['dDay']})"
        for item in sorted_items
    ]

    ingredient_names = [
        item["name"]
        for item in sorted_items
    ]

    st.subheader("사용 가능한 재료")
    st.write(", ".join(ingredient_names))

    if "recipes" not in st.session_state:
        st.session_state.recipes = []

    if st.button("요리 찾기"):
        with st.spinner("냉장고 재료를 분석해서 요리를 찾는 중입니다..."):
            recipes = find_recipes(
                ingredient_info,
                openai_key,
                tavily_key
            )

            st.session_state.recipes = recipes

    if len(st.session_state.recipes) == 0:
        st.info("요리 찾기 버튼을 눌러 추천 레시피를 받아보세요.")
        return

    st.subheader("추천 레시피")

    for i, recipe in enumerate(st.session_state.recipes, start=1):
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


def find_recipes(ingredient_info, openai_key, tavily_key):
    client = OpenAI(api_key=openai_key)

    prompt = f"""
    냉장고에 있는 전체 재료 목록과 남은 유통기한: {', '.join(ingredient_info)}

    위 재료들을 스캔하여, 유통기한이 임박한(D-Day가 적은) 재료를 우선적으로 소비할 수 있는 자취생 맞춤형 요리 레시피를 2~3개 추천해줘.
    ingredients 필드에서는 무조건 전체 재료 목록에 있는 이름 그대로를 사용해야해.

    반드시 아래 JSON 형식에 맞게 답변해줘:
    {{
        "recipes": [
            {{
                "title": "요리 이름",
                "ingredients": ["재료1", "재료2"],
                "content": "1. 단계별 조리법...\\n2. ...",
                "search_keyword": "유튜브와 블로그에서 이 요리를 찾기 위해 검색할 명확한 요리 이름 키워드"
            }}
        ]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        recipes = result.get("recipes", [])

    except Exception as e:
        st.error(f"레시피 생성 중 오류 발생: {str(e)}")
        return []

    tavily = TavilyClient(api_key=tavily_key)

    for recipe in recipes:
        recipe["youtube_url"] = None
        recipe["blog_url"] = None

        keyword = recipe.get("search_keyword", recipe.get("title", ""))

        try:
            yt_search = tavily.search(
                query=f"{keyword} 레시피 site:youtube.com",
                search_depth="basic",
                max_results=1
            )

            if yt_search.get("results"):
                recipe["youtube_url"] = yt_search["results"][0]["url"]

            web_search = tavily.search(
                query=f"{keyword} 간단 레시피",
                search_depth="basic",
                max_results=1
            )

            if web_search.get("results"):
                recipe["blog_url"] = web_search["results"][0]["url"]

        except Exception:
            pass

    return recipes