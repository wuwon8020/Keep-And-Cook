import streamlit as st
import json
import re
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
            st.session_state.recipes = find_recipes(
                ingredient_info,
                openai_key,
                tavily_key
            )

    if len(st.session_state.recipes) == 0:
        st.info("요리 찾기 버튼을 눌러 추천 레시피를 받아보세요.")
        return

    st.subheader("추천 레시피")

    for i, recipe in enumerate(st.session_state.recipes, start=1):
        with st.container(border=True):
            st.markdown(f"## {i}. {recipe.get('title', '이름 없음')}")

            st.write("사용 재료")
            st.write(", ".join(recipe.get("ingredients", [])))

            st.write("조리법")
            st.write(recipe.get("content", ""))

            st.markdown("### 참고 레시피")

            preview_cols = st.columns(2)

            with preview_cols[0]:
                show_preview_card(
                    recipe.get("youtube_preview"),
                    default_label="유튜브 레시피"
                )

            with preview_cols[1]:
                show_preview_card(
                    recipe.get("blog_preview"),
                    default_label="블로그 레시피"
                )


def show_preview_card(preview, default_label):
    if not preview or not preview.get("url"):
        st.caption(f"{default_label} 링크 없음")
        return

    title = preview.get("title") or default_label
    url = preview.get("url")
    description = preview.get("description") or ""
    thumbnail = preview.get("thumbnail")

    with st.container(border=True):
        if thumbnail:
            st.image(thumbnail, width='stretch')

        st.markdown(f"**{title}**")

        if description:
            st.caption(description[:120] + "..." if len(description) > 120 else description)

        st.link_button("바로가기", url, width='stretch')


def find_recipes(ingredient_info, openai_key, tavily_key):
    client = OpenAI(api_key=openai_key)

    prompt = f"""
    냉장고에 있는 전체 재료 목록과 남은 유통기한: {', '.join(ingredient_info)}

    위 재료들을 스캔하여, 유통기한이 임박한 재료를 우선적으로 소비할 수 있는
    자취생 맞춤형 요리 레시피를 2~3개 추천해줘.

    ingredients 필드에서는 반드시 전체 재료 목록에 있는 이름 그대로를 사용해야 해.

    반드시 아래 JSON 형식에 맞게 답변해줘:
    {{
        "recipes": [
            {{
                "title": "요리 이름",
                "ingredients": ["재료1", "재료2"],
                "content": "1. 단계별 조리법...\\n2. ...",
                "search_keyword": "검색에 사용할 명확한 요리 이름"
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
        keyword = recipe.get("search_keyword", recipe.get("title", ""))

        recipe["youtube_preview"] = get_youtube_preview(tavily, keyword)
        recipe["blog_preview"] = get_blog_preview(tavily, keyword)

    return recipes


def get_youtube_preview(tavily, keyword):
    try:
        result = tavily.search(
            query=f"{keyword} 레시피 site:youtube.com",
            search_depth="basic",
            max_results=1
        )

        results = result.get("results", [])

        if not results:
            return None

        item = results[0]
        url = item.get("url")
        video_id = extract_youtube_id(url)

        thumbnail = None
        if video_id:
            thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

        return {
            "title": item.get("title", "유튜브 레시피"),
            "url": url,
            "description": item.get("content", ""),
            "thumbnail": thumbnail
        }

    except Exception:
        return None


def get_blog_preview(tavily, keyword):
    try:
        result = tavily.search(
            query=f"{keyword} 간단 레시피 블로그",
            search_depth="basic",
            max_results=1
        )

        results = result.get("results", [])

        if not results:
            return None

        item = results[0]

        return {
            "title": item.get("title", "블로그 레시피"),
            "url": item.get("url"),
            "description": item.get("content", ""),
            "thumbnail": item.get("image_url")
        }

    except Exception:
        return None


def extract_youtube_id(url):
    if not url:
        return None

    patterns = [
        r"youtu\.be/([^?&]+)",
        r"youtube\.com/watch\?v=([^?&]+)",
        r"youtube\.com/shorts/([^?&]+)",
        r"youtube\.com/embed/([^?&]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None