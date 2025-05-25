
# Place Search · Ratatouille Clone (Async)

### 1. 환경 준비
```bash
pip install -r requirements.txt
```

### 2. secrets.toml
Streamlit Cloud 또는 로컬 `.streamlit/secrets.toml`

```toml
[kakao]
rest_api_key = "YOUR_KAKAO_REST_API_KEY"
```

### 3. 실행
```bash
streamlit run place_search_app.py
```

### 4. 배포 (Streamlit Cloud)
1. GitHub 저장소에 코드 업로드
2. Streamlit Cloud ▸ New App
   - Repo / Branch / `place_search_app.py`
3. Settings ▸ Secrets ▸ `kakao.rest_api_key` 입력
4. URL 자동 생성 → 접속 확인
