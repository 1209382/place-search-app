
import os
import asyncio
import httpx
import streamlit as st
import pandas as pd

############################################################
# CONFIG                                                   #
############################################################
+KAKAO_REST_API_KEY = (
+    st.secrets.get("kakao", {}).get("rest_api_key")
+    or os.getenv("KAKAO_REST_API_KEY", "")
+)
)

HEADERS = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
BASE_URL = "https://dapi.kakao.com/v2/local"

if not KAKAO_REST_API_KEY:
    st.warning("⚠️ Kakao REST API 키가 없습니다. 좌측 사이드바 ▸ Settings ▸ Secrets 에서 등록하세요.")

############################################################
# ASYNC HTTP HELPERS                                       #
############################################################
async def _get_json_async(client: httpx.AsyncClient, url: str, params: dict):
    r = await client.get(url, params=params, headers=HEADERS)
    r.raise_for_status()
    return r.json()

@st.cache_data(show_spinner=False)
def geocode(address: str):
    """동기 Wrapper: 주소 → (lat, lon)"""
    url = f"{BASE_URL}/search/address.json"
    r = httpx.get(url, params={"query": address}, headers=HEADERS, timeout=5)
    r.raise_for_status()
    docs = r.json().get("documents")
    if not docs:
        return None, None
    return float(docs[0]["y"]), float(docs[0]["x"])

async def search_keyword_pages(keyword: str, lat: float, lon: float, radius_m: int, pages: list[int]):
    url = f"{BASE_URL}/search/keyword.json"
    async with httpx.AsyncClient(http2=True, timeout=5) as client:
        tasks = []
        for p in pages:
            params = {
                "y": lat,
                "x": lon,
                "radius": radius_m,
                "size": 15,
                "page": p,
                "query": keyword,
                "sort": "distance",
            }
            tasks.append(_get_json_async(client, url, params))
        return await asyncio.gather(*tasks)

############################################################
# STREAMLIT PAGE                                           #
############################################################
st.set_page_config(
    page_title="Place Search · Ratatouille Clone (Async)",
    page_icon="🍽️",
    layout="wide",
)

st.title("🍽️ Place Search — Async Edition")

with st.sidebar:
    st.header("🔍 검색 옵션")
    keyword = st.text_input("검색 키워드", placeholder="ex) 고깃집, 카페, 포차…")
    address = st.text_input("중심 주소", value="경주시 황성동")
    radius_km = st.slider("반경 (km)", 0.5, 30.0, 3.0, 0.5)
    pages_to_fetch = st.number_input("페이지 수", 1, 45, 3)
    search_btn = st.button("🔎 검색")

if search_btn and keyword and address:
    with st.spinner("주소 좌표 변환 중…"):
        lat, lon = geocode(address)
    if lat is None:
        st.error("❌ 주소를 좌표로 변환할 수 없습니다. 다른 주소를 입력하세요.")
        st.stop()

    # Async fetch
    pages = list(range(1, pages_to_fetch + 1))
    with st.spinner("키워드 검색 중…"):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        responses = loop.run_until_complete(
            search_keyword_pages(keyword, lat, lon, int(radius_km * 1000), pages)
        )

    docs = []
    for resp in responses:
        docs.extend(resp.get("documents", []))

    if not docs:
        st.warning("검색 결과가 없습니다.")
        st.stop()

    df = pd.DataFrame(
        [
            {
                "상호": d["place_name"],
                "카테고리": d["category_name"],
                "거리(m)": int(d["distance"] or 0),
                "주소": d.get("road_address_name") or d.get("address_name"),
                "링크": d["place_url"],
                "lat": float(d["y"]),
                "lon": float(d["x"]),
            }
            for d in docs
        ]
    )

    st.subheader(f"📍 결과 {len(df)}건 — 반경 {radius_km} km (p{pages_to_fetch})")

    st.map(df[["lat", "lon"]])
    st.dataframe(
        df[["상호", "카테고리", "거리(m)", "주소", "링크"]].sort_values("거리(m)"),
        use_container_width=True,
    )

    st.download_button(
        "📥 CSV 다운로드",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"{keyword}_{radius_km}km.csv",
        mime="text/csv",
    )
else:
    st.info("좌측에서 키워드·주소를 입력 후 ‘검색’ 버튼을 누르세요.")

st.markdown("---")
st.caption("Async · HTTP/2 · p95 < 1 s 목표 | Kakao Local Search API | Clone of place-search-ratatouille")
