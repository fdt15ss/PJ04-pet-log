# 에이전트 실행 전후 스크린샷

포트폴리오에서 "쇼핑 추천 에이전트"와 "병원 추천"의 동작을 설명하기 위한 전후 비교 캡처입니다.
같은 뷰포트/같은 화면 위치에서 찍었기 때문에 좌우로 나란히 붙여도 바로 비교됩니다.

## 쇼핑 추천 에이전트 (LangGraph workflow)

| 파일 | 상태 | 설명 |
| --- | --- | --- |
| `01-shopping-agent-before.png` | 실행 전 | 에이전트 호출 중. 헤더에 `상품 추천 동기화 중` 로딩 표시가 뜨고, 목록은 기록 기반 기본 후보(가격·판매처 없음)만 보입니다. |
| `02-shopping-agent-after.png` | 실행 후 | 에이전트 응답이 반영된 상태. 상품명·최저가·판매처·상품 링크가 붙은 실제 추천 카드로 교체됩니다. |
| `03-shopping-agent-after-reason.png` | 실행 후(근거) | `추천 이유 보기`를 펼친 화면. 어떤 기록에서 이 상품이 나왔는지 근거 문장이 노출됩니다. |

설명 포인트: 실행 전은 프론트 로컬 규칙 기반 후보, 실행 후는 에이전트가 기록을 근거로 뽑아온 실제 상품 후보라는 점.

## 병원 추천

| 파일 | 상태 | 설명 |
| --- | --- | --- |
| `04-hospital-agent-before.png` | 실행 전 | 증상 메모만 입력된 상태. 위치 미적용이라 지도에 내 위치 핀만 있고 병원 후보는 없습니다. (`내 위치 찾기`) |
| `05-hospital-agent-loading.png` | 실행 중 | 위치 전달 후 추천 요청 진행 중(`병원 정보를 불러오는 중...`). |
| `06-hospital-agent-after.png` | 실행 후 | 위치·증상 기반 병원 후보가 거리순으로 채워진 상태. 지도 마커, 거리/소요시간, 24시 여부, 진료 중 여부가 표시됩니다. |
| `07-hospital-agent-after-selected.png` | 실행 후(선택) | 병원을 선택해 상단 요약이 `미정 → 선택`으로 바뀐 상태. 상담 준비 흐름으로 이어집니다. |

설명 포인트: 병원 추천은 LangGraph가 아니라 위치 + 증상 텍스트를 받아 외부 장소 데이터를 정렬/필터하는 provider·middleware 구조라는 점.

## 재생성 방법

```bash
cd frontend/app/web && npx playwright test tests/eval/agent-before-after.spec.ts
```

- 캡처 스펙: `frontend/app/web/tests/eval/agent-before-after.spec.ts`
- 백엔드/LLM 키 없이 돌아갑니다. API 응답은 Playwright 라우트로 목킹하고, 에이전트 응답 시점을 직접 잡아 실행 전/중/후를 각각 캡처합니다.
- `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`가 없으면 지도는 목업 지도로 렌더됩니다. 실제 구글맵 화면이 필요하면 `frontend/app/web/.env.dev`에 키를 넣고 다시 실행하세요.
- 앱 셸이 `h-dvh` + 내부 스크롤 구조라 `fullPage` 캡처가 뷰포트 높이로 잘립니다. 그래서 스펙에서 화면 높이를 늘려(쇼핑 1560px, 병원 1960px) 한 장에 담았습니다.
