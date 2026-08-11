# 에이전트 흐름 인포그래픽

포트폴리오에서 쇼핑 추천과 병원 추천의 내부 흐름을 한 장으로 설명하기 위한 도식입니다.
왼쪽은 단계, 오른쪽은 각 단계에서 실제로 무슨 일이 일어나는지 + 실패했을 때의 fallback입니다.

| 파일 | 내용 |
| --- | --- |
| `infographic-shopping-agent.png` | 쇼핑 추천 에이전트. `prepare_categories → search_products → select_recommendations → build_result` LangGraph 노드 흐름 |
| `infographic-hospital-recommendation.png` | 병원 추천. 응급 판단 → 반경/검색어 조정 → Google Places 검색 → 정렬·필터의 규칙 기반 흐름 |
| `infographic-shopping-agent-compact.png` | 위 내용의 세로 압축 버전 (440px 폭) |
| `infographic-hospital-recommendation-compact.png` | 위 내용의 세로 압축 버전 (440px 폭) |

`-compact` 두 장은 발표 슬라이드에서 **왼쪽 열(폰 스크린샷 옆 빈 공간)**에 넣는 용도입니다.
가로 440px 기준이라 슬라이드 좌측 여백에 그대로 올라가고, 문장을 한 줄씩으로 줄여 멀리서도 읽힙니다.
기본 버전(가로 900px)은 문서·노션처럼 폭이 넉넉한 곳에 쓰세요.

두 장을 나란히 놓으면 "왜 쇼핑에는 LangGraph를 쓰고 병원에는 쓰지 않았는가"를 그대로 설명할 수 있습니다.
쇼핑은 LLM 판단이 두 번 들어가는 다단계 흐름이라 노드 분리가 유리했고, 병원은 규칙 판단이 핵심이라
provider/middleware 조합이 더 단순했습니다.

## 근거 코드

- 쇼핑: `backend/src/application/agents/shopping.py`, `backend/src/middleware/shopping_fallback.py`
- 병원: `backend/src/application/agents/hospital.py`, `backend/src/middleware/hospital_cache_rate_limit.py`, `backend/src/middleware/hospital_fallback.py`

## 수정 · 재생성 방법

1. 문구를 고칩니다. 기본 버전은 `infographics.source.html`(단계 박스 ↔ 오른쪽 설명이 한 행씩 대응),
   슬라이드용 압축 버전은 `infographics-compact.source.html`입니다.
2. 아래 명령으로 PNG를 다시 뽑습니다. (2x 해상도로 캡처)

```bash
cd frontend/app/web && npx playwright test tests/eval/portfolio-infographics.spec.ts
```

렌더링 스펙: `frontend/app/web/tests/eval/portfolio-infographics.spec.ts`
