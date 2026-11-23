# Pet Log — 기록을 행동으로 연결하는 AI 반려동물 케어 에이전트

> 자연어·음성으로 남긴 반려동물의 일상 기록을 구조화하고, 누적 맥락을 분석해 알림·제안·병원 및 상품 추천으로 연결하는 모바일 우선 웹 서비스

## 1. 프로젝트 개요

**Pet Log**는 반려동물의 행동과 건강 기록을 단순히 저장하는 데서 끝내지 않고, 누적된 기록을 AI Agent가 해석해 상태 변화, 기록 누락, 위험 신호, 다음 행동 제안까지 연결하는 반려동물 관리 서비스입니다.

기존 반려동물 관리 앱은 예방접종, 진료, 사료량 등을 캘린더나 기록 형태로 저장하는 데 집중하는 경우가 많습니다. Pet Log는 보호자가 남긴 자연어, 음성, 사진 기반 기록을 구조화하고, 반려동물 프로필과 최근 기록 맥락을 함께 분석해 보호자가 다음 행동을 판단할 수 있도록 돕는 것을 목표로 했습니다.

| 항목 | 내용 |
| --- | --- |
| 프로젝트명 | Pet Log |
| 주제 | AI Agent 기반 반려동물 건강/행동 기록 관리 서비스 |
| 개발 기간 | 2026.04.22 ~ 2026.05.18 |
| 팀 구성 | 강현준, 김경표, 복만수, 임경빈 |
| 개인 역할 | 백엔드·AI Agent·외부 API 연동 |
| 주요 형태 | 모바일 우선 웹 MVP + Python AI Agent 백엔드 |
| 핵심 가치 | 기록 부담 완화, 누적 맥락 분석, 행동 제안, 알림, 대화형 케어 경험 |
| 저장소 | [GitHub](https://github.com/fdt15ss/pj04-pet-log) |

### 핵심 결과

- 자연어 기록을 구조화하고, 분석 결과와 함께 SQLite에 저장하는 end-to-end 파이프라인을 구현했습니다.
- 기록 누락·위험 신호·행동 변화·일정에 따른 알림 후보 생성부터 중복 제거와 읽음 처리까지 연결했습니다.
- Naver Shopping과 Google Places를 연동하고, API 장애나 빈 결과에도 사용자 흐름이 끊기지 않도록 fallback·cache·rate limit 경계를 마련했습니다.
- 프론트엔드 단위 테스트와 Playwright, 백엔드 unittest·pytest를 사용해 주요 기능과 계층 경계를 검증했습니다.

### 개인 기여

아래는 팀 전체 구현 가운데 임경빈이 주도한 범위입니다.

- **데이터 영속화**: SQLite 연결과 seed data를 구성하고, 반려동물·기록·일정 repository를 실제 DB 구현으로 연결했습니다. ([database.py](backend/src/infrastructure/database.py), [repositories](backend/src/infrastructure/repositories))
- **외부 추천 기능**: Naver Shopping 상품 검색/추천과 Google Places 위치 기반 동물병원 추천을 구현하고, fallback·cache·rate limit middleware를 추가했습니다. ([shopping](backend/src/infrastructure/shopping), [hospital.py](backend/src/application/agents/hospital.py), [middleware](backend/src/middleware))
- **커뮤니티 end-to-end 연동**: 게시판·게시글·댓글·반응 API와 repository를 구현하고, Next.js 커뮤니티 화면을 실제 API에 연결했습니다. ([community_routes.py](backend/src/presentation/http/community_routes.py), [community page](frontend/app/web/src/app/community/page.tsx))
- **AI workflow 개선**: 프로젝트 종료 후 쇼핑 추천의 카테고리 준비, 검색, 후보 선택, 결과 생성을 LangGraph 상태 전이로 분리해 단계별 테스트가 가능한 흐름으로 개선했습니다. ([shopping.py](backend/src/application/agents/shopping.py))
- **검증**: 데이터베이스, 커뮤니티, 쇼핑, 병원 추천의 단위·HTTP·smoke test를 작성해 정상 경로와 실패 경로를 함께 검증했습니다. ([backend tests](backend/tests))

## 2. 문제 정의

반려동물 보호자는 매일의 식사, 배변, 산책, 행동, 병원 방문, 약 복용 같은 정보를 꾸준히 관리해야 하지만, 실제로는 기록이 누락되거나 중단되기 쉽습니다. 또한 기록이 쌓이더라도 단순 목록으로 남으면 보호자가 직접 패턴을 해석해야 하므로 데이터가 충분히 활용되지 못합니다.

이 프로젝트는 다음 문제를 해결 대상으로 삼았습니다.

- 보호자가 매번 정해진 양식에 맞춰 입력해야 하는 기록 부담
- 기록이 누락되거나 중단되면서 누적 데이터가 불완전해지는 문제
- 단일 기록만으로는 알기 어려운 반복 행동, 상태 변화, 위험 신호 해석의 어려움
- 기록 저장 이후 실제 행동 가이드, 일정 리마인더, 병원 상담 판단으로 이어지지 않는 한계
- 보호자가 앱에 지속적으로 재방문할 만한 감성적 동기 부족

## 3. 해결 방향

Pet Log는 기록 앱이 아니라 **기록을 해석하고 다음 행동으로 연결하는 AI 케어 Agent**를 지향했습니다.

핵심 방향은 다음과 같습니다.

- 자연어, 음성, 사진 기반 입력을 받아 보호자의 기록 부담을 낮춘다.
- 자유 입력을 카테고리, 제목, 상세 내용, 측정값, 신뢰도, 확인 필요 여부로 구조화한다.
- 반려동물 프로필, 최근 기록, 일정, 알림 후보를 함께 조립해 맥락 기반 분석을 수행한다.
- 누락 기록, 위험 신호, 행동 변화, 일정 기반 리마인더를 알림으로 제공한다.
- 건강 판단이 필요한 상황에서는 진단을 단정하지 않고 병원 상담을 권장하는 안전 경계를 유지한다.
- 반려동물 페르소나 기반 대화 경험으로 기록 관리의 피로도를 낮춘다.

## 4. 주요 기능

### 4.1 기록 입력 및 구조화

- 보호자가 입력한 자연어 기록을 AI가 식사, 산책/활동, 배변/소변, 병원/약/접종, 행동 등으로 분류합니다.
- 기록 입력은 미리보기와 저장 흐름으로 나뉘며, 사용자가 구조화 결과를 확인한 뒤 저장할 수 있습니다.
- 음성 파일은 Whisper 기반 STT로 텍스트화하고, AI가 `corrected_text`로 문장을 정리합니다.
- 사진 기반 기록 이해는 확장 가능한 provider 구조로 설계했습니다.

### 4.2 분석 및 제안

- 최근 기록을 기준으로 식사, 행동, 체중, 활동량 변화와 반복 패턴을 분석합니다.
- 통증, 호흡 이상, 혈변, 반복 구토, 지속적인 식욕 저하 같은 위험 신호를 탐지합니다.
- 분석 결과를 바탕으로 행동 개선 가이드와 건강 관리 제안을 생성합니다.
- 질병 확정 진단이나 처방이 아니라, 보호자가 다음 행동을 판단하도록 돕는 안내에 집중했습니다.

### 4.3 알림 및 일정

- `missing_record`, `risk`, `behavior_change`, `schedule` 4가지 유형의 알림 후보를 생성합니다.
- 알림은 중복 제거 키를 기준으로 관리하고, DB 기반 읽음 처리를 지원합니다.
- 예방접종, 약 복용, 건강검진, 사료 변경 시기 같은 케어 일정을 기반으로 리마인더를 제공합니다.

### 4.4 펫 대화 및 케어 질문

- 반려동물 이름, 사진, 성격, 최근 기록을 반영한 펫 페르소나 응답 구조를 설계했습니다.
- 보호자가 현재 키우는 반려동물과 대화하는 듯한 감성 인터페이스를 제공합니다.
- 케어 판단이 필요한 질문은 AI 케어 질문 흐름으로 연결하고, 위험 신호가 있는 경우 병원 상담을 권장합니다.

### 4.5 외부 서비스 연동

- Google Places API 기반 위치별 동물병원 추천을 제공합니다.
- 응급, 야간, 24시간, 호흡, 출혈, 경련, 중독 같은 표현을 반영해 병원 검색 반경과 검색어를 조정합니다.
- Naver Shopping API와 LLM을 결합해 반려동물 케어 맥락에 맞는 상품 추천 이유를 생성합니다.

### 4.6 커뮤니티 및 확장 기능

- 유기동물, 용품 나눔, 자유게시판, 행동 고민, 후기 게시판 구조를 제공합니다.
- 커뮤니티 글, 댓글, 반응 API를 기본 구현했습니다.
- 공동 관리, 병원 리포트, RAG 기반 케어 지식, 커머스 개인화로 확장 가능한 구조를 마련했습니다.

## 5. 구현 화면

구현된 주요 웹 페이지는 다음과 같습니다.

| 경로 | 화면 |
| --- | --- |
| `/` | 홈 |
| `/record` | 기록 입력 |
| `/analysis` | 분석 |
| `/timeline` | 기록 타임라인 |
| `/suggestions` | AI 제안 |
| `/profile` | 반려동물 프로필 |
| `/notifications` | 알림 |
| `/schedule` | 일정 |
| `/community` | 커뮤니티 |
| `/hospital` | 병원 연계 |
| `/shopping` | 쇼핑 |
| `/shared-care` | 공동 관리 |
| `/settings` | 설정 |

### 전체 화면 구성

![Pet Log 전체 화면 구성](frontend/_workspace/portfolio-screenshots/selected/portfolio-01-overall-screens.png)

### 자연어 기록 구조화

보호자가 자연어로 기록하면 AI가 카테고리와 상세 항목으로 구조화하고, 사용자가 저장 전에 결과를 확인할 수 있습니다.

![자연어 기록 입력과 AI 구조화 미리보기](frontend/_workspace/portfolio-screenshots/selected/portfolio-04-record-ai-structure.png)

### 기록 기반 분석

저장된 기록을 기간·카테고리별로 모아 변화와 패턴을 보여주고, AI 분석 결과를 다음 행동으로 연결합니다.

![기록 기반 분석 리포트](frontend/_workspace/portfolio-screenshots/selected/portfolio-05-analysis-report.png)

### 외부 서비스 연동

누적 기록과 반려동물 맥락을 상품 추천에 반영하고, 병원 상담에 필요한 기록 요약을 제공합니다.

![기록 기반 쇼핑 추천](frontend/_workspace/portfolio-screenshots/selected/portfolio-06-shopping-recommendation.png)

![병원 상담용 기록 요약](frontend/_workspace/portfolio-screenshots/selected/portfolio-07-hospital-report.png)

### AI 케어 질문

홈의 선제 질문과 별도 케어 패널을 통해 기록 맥락에 기반한 질문 흐름으로 진입할 수 있습니다.

![AI 질문 진입 흐름](frontend/_workspace/portfolio-screenshots/selected/portfolio-02-ai-question-flow.png)

## 6. 기술 스택

### 6.1 Frontend

| 영역 | 기술 | 역할 |
| --- | --- | --- |
| Framework | Next.js `^16.2.4` | App Router, Route Handler, standalone build |
| UI | React `^19.2.5` | 페이지 및 공통 컴포넌트 구성 |
| Language | TypeScript | 타입 안정성 확보 |
| Styling | Tailwind CSS, global CSS | 모바일 우선 UI 스타일링 |
| HTTP | Axios | API 호출 및 FastAPI 프록시 연동 |
| Test | `tsx --test` | 프론트엔드 단위 테스트 |
| E2E/QA | Playwright | 모바일 UI, 주요 플로우, 시각 QA |
| Deploy | Azure App Service | Node.js 런타임 기반 배포 |

### 6.2 Backend

| 영역 | 기술 | 역할 |
| --- | --- | --- |
| Language | Python `>=3.12` | AI Agent 백엔드 구현 |
| API | FastAPI `>=0.136.1` | HTTP API, health check, 기록 입력, STT, 추천 API |
| Server | Uvicorn | ASGI 서버 실행 |
| Agent Graph | LangGraph `>=1.1,<2.0` | Pet Log agent pipeline과 쇼핑 추천 workflow orchestration |
| LLM Adapter | LangChain `>=1.0,<2.0` | 모델, tool, middleware adapter |
| Storage | SQLite | 로컬 영구 저장소 |
| Speech | OpenAI Whisper, edge-tts | STT/TTS provider |
| Search/RAG | ChromaDB, Tavily, pypdf | 케어 지식 검색 확장 기반 |
| Test/Lint | unittest, pytest, Ruff | 백엔드 검증 및 정적 분석 |
| Package | uv, pyproject.toml | 의존성 및 실행 환경 관리 |

## 7. 시스템 아키텍처

프로젝트는 프론트엔드와 백엔드를 분리하고, 백엔드는 계층형 구조로 외부 SDK와 비즈니스 로직의 결합을 낮추도록 설계했습니다.

```text
Browser
  -> Next.js App Router pages
  -> Next.js Route Handler /api/v1/...
  -> FastAPI backend /api/v1/...
  -> application pipeline
  -> application agents
  -> repositories, policies, LLM providers, speech providers, external APIs
```

백엔드 내부 구조는 다음 흐름을 따릅니다.

```text
presentation
  -> application pipelines
  -> application agents
  -> interfaces
  -> infrastructure / tools / agent_runtime
```

각 계층의 책임은 다음과 같습니다.

- `domain`: 순수 도메인 타입. DB, HTTP, LLM SDK에 직접 의존하지 않습니다.
- `application`: 제품 흐름과 interface 계약을 정의합니다.
- `infrastructure`: DB, LLM, STT/TTS, rule-based policy, 외부 API 구현체를 둡니다.
- `agent_runtime`: LLM agent 실행 loop, prompt, tool registry, memory를 담당합니다.
- `middleware`: safety, logging, tracing, retry, validation 같은 공통 처리를 담당합니다.
- `tools`: agent가 호출할 수 있는 record, profile, schedule, care, speech tool을 제공합니다.
- `presentation`: FastAPI HTTP와 CLI 같은 외부 진입점을 담당합니다.

LangGraph는 모든 에이전트에 무조건 적용하지 않고, 상태 전이가 분명한 흐름에 선택적으로 사용했습니다. 자연어 기록 입력 파이프라인은 `structure_record -> load_context -> analyze_context -> detect_risk -> save_records -> suggest_care -> recommend_shopping -> plan_reminders` 순서의 `StateGraph`로 구성했고, 쇼핑 추천 에이전트는 내부적으로 `prepare_categories -> search_products -> select_recommendations -> build_result` 노드로 나누어 실행합니다. 반면 병원 추천은 응급 여부 판단, 반경 조정, Google Places 검색, 정렬/필터링 흐름이 비교적 짧기 때문에 LangGraph보다 일반 application agent와 provider/middleware 조합으로 단순하게 유지했습니다.

## 8. AI Agent 설계

### 8.1 기록 분석 Agent Track

| Agent | 역할 |
| --- | --- |
| RecordStructuringAgent | 자유 텍스트를 구조화된 기록 후보로 변환 |
| ContextAnalysisAgent | 최근 기록 패턴, 누락 기록, 상태 변화, UI 이동 경로 분석 |
| RiskDetectionAgent | 건강/안전 위험 신호 탐지 |
| SuggestionAgent | 행동 개선 가이드와 건강 관리 제안 생성 |
| ReminderAgent | 접종, 약 복용, 사료 변경, 건강검진 리마인더 계획 |
| NotificationAgent | 알림 후보 생성, 중복 제거, 읽음 처리 흐름 연결 |

### 8.2 대화, 검색, 외부 연동 Track

| Agent 또는 Provider | 역할 |
| --- | --- |
| PetPersonaAgent | 반려동물 프로필과 최근 기록을 반영한 대화 응답 |
| CareAnswerProvider | 케어 질문에 반려동물 맥락과 케어 지식 검색 결과를 결합 |
| ShoppingAgent | LangGraph 기반으로 쇼핑 카테고리 생성, Naver Shopping 후보 검색, LLM 상품 선택, 추천 이유 생성을 오케스트레이션 |
| HospitalRecommendationAgent | 응급/야간 문맥을 반영해 Google Places 기반 위치별 동물병원 추천 |
| PhotoRecordUnderstandingAgent | 이미지 기반 기록 이해 확장 지점 |

쇼핑 추천은 LLM 판단과 외부 검색 API가 여러 단계로 이어지기 때문에 LangGraph로 각 단계를 노드화했습니다. 카테고리 생성에 실패하면 빈 추천으로 종료하고, 상품 선택 LLM이 실패하면 첫 번째 후보를 유지하는 식으로 fallback 경계를 명확히 했습니다. 병원 추천은 같은 외부 연동 기능이지만 의료 안전 문맥이 더 중요하므로, 검색 반경 확대와 24시간 병원 우선 정렬은 명시적 규칙으로 두고 provider 실패 시 Google Maps 검색 링크 fallback을 제공했습니다.

## 9. 주요 API 구현

백엔드는 FastAPI 기반으로 기능별 API 경계를 구성했습니다.

| 영역 | 주요 endpoint | 책임 |
| --- | --- | --- |
| 사용자·반려동물 | `GET /api/v1/me`, `GET /api/v1/pets` | 사용자와 반려동물 프로필 조회 |
| 기록·일정 | `GET·POST /api/v1/pet-log/records`, `GET /api/v1/pet-log/schedules` | 자연어 기록 파이프라인 실행, 기록 및 일정 조회 |
| 파일·음성 | `POST·GET /api/v1/files`, `POST /api/v1/speech/*` | 이미지 업로드, STT 변환, 음성 문장 보정 |
| 알림 | `GET·PATCH·PUT /api/v1/notifications*` | 알림 후보 생성, 조회, 읽음 상태 관리 |
| 추천 | `POST /api/v1/hospitals/recommendations`, `GET /api/v1/shopping/recommendations` | 위치 기반 병원 추천, Naver Shopping과 LLM 기반 상품 추천 |
| 커뮤니티 | `GET·POST /api/v1/community/*` | 게시판·게시글·댓글·반응 관리 |

## 10. 검증 및 품질 관리

검증은 세 축으로 구성했습니다.

| 축 | 내용 |
| --- | --- |
| 프론트엔드 | `tsx --test` 단위 테스트, Playwright E2E, lint·typecheck·build |
| 백엔드 | unittest 기반 **테스트 265개 / 39개 파일**. 정상 경로와 실패 경로를 분리해 작성 |
| 계층 경계 | 정적 검사로 아키텍처 규칙 위반을 탐지 |

세 번째 축이 이 프로젝트에서 특히 효과가 컸습니다. `application`과 `domain` 계층이 외부 framework나 SDK에 직접 의존하지 않아야 한다는 규칙을 문서가 아니라 **실행 가능한 명령**으로 만들어, 위반이 생기면 바로 드러나게 했습니다.

```bash
# 출력이 없어야 정상 — 도메인/애플리케이션 계층에 외부 SDK가 새어 들어오지 않았는지 검사
rg -n "fastapi|openai|sqlalchemy|sqlite|postgres|psycopg" src/application src/domain
```

이 규칙이 지켜졌기 때문에 SQLite 스키마가 바뀌거나 LLM provider를 교체해도 상위 코드는 그대로 유지됐습니다. 전체 검증 명령은 [README](README.md)에 정리했습니다.

### 10.1 NPU(RNGD) 추론 성능 비교

LLM 백엔드를 FuriosaAI RNGD(NPU)로 바꿨을 때 응답이 얼마나 빨라지는지 쟀습니다. 같은 Qwen3 8B 모델을 집 PC의 GPU와 RNGD에서 돌리고, Pet Log가 실제로 보내는 프롬프트 5종(기록 구조화, 케어 질문, 반려동물 대화, 쇼핑 에이전트 2단계)으로 측정했습니다. 앱 코드는 바꾸지 않고 OpenAI 호환 서버 주소만 바꿨습니다. 집 PC는 가정에서 흔히 쓰는 4bit와, RNGD의 FP8과 비트 수를 맞춘 8bit 두 가지로 쟀습니다.

| 동시 요청 | 구성 | TTFT p50 | 요청당 생성 속도 | 전체 처리량 | 오류 |
| --- | --- | ---: | ---: | ---: | ---: |
| 1개 | 집 PC · Ollama · Q4_K_M (4bit) | 0.042초 | 58.3 tok/s | 56.9 tok/s | 0 / 50 |
| 1개 | 집 PC · Ollama · Q8_0 (8bit) | 0.052초 | 37.4 tok/s | 36.9 tok/s | 0 / 50 |
| 1개 | RNGD · furiosa-llm · FP8 | 0.027초 | 104.4 tok/s | 102.3 tok/s | 0 / 50 |
| 4개 | 집 PC · Ollama · Q4_K_M (4bit) | 4.121초 | 58.5 tok/s | 58.2 tok/s | 0 / 80 |
| 4개 | 집 PC · Ollama · Q8_0 (8bit) | 8.797초 | 37.5 tok/s | 37.4 tok/s | 0 / 80 |
| 4개 | RNGD · furiosa-llm · FP8 | 0.073초 | 94.9 tok/s | **346.4 tok/s** | 0 / 80 |

- **요청 1개**: RNGD가 생성 속도 기준 4bit 대비 1.8배, 8bit 대비 2.8배 빠릅니다. 집 PC는 8bit로 올리면 읽어야 할 가중치가 두 배가 되어 오히려 36% 느려졌습니다.
- **동시 요청 4개**: 집 PC의 Ollama는 요청을 하나씩 처리해 처리량이 그대로이고, 뒤 요청은 수 초를 기다렸습니다. RNGD는 4개를 한꺼번에 처리해 처리량이 4bit 대비 **6.0배**, 8bit 대비 **9.3배**, 첫 토큰은 **56~120배** 빨랐습니다. 대신 요청당 생성 속도는 약 9% 줄었습니다.
- **측정 환경**: 집 PC는 RTX 3060 12GB, Ollama 0.40.17, `qwen3:8b`(Q4_K_M)와 `qwen3:8b-q8_0`(Q8_0, 전부 GPU에 적재). RNGD는 1장, furiosa-llm 2026.4.0, `furiosa-ai/Qwen3-8B-FP8`. 모두 같은 머신 안에서 localhost로 호출했고, thinking을 끄고 최대 출력 256토큰, 워밍업 1회로 맞췄습니다.
- **한계**: Ollama에는 FP8 형식이 없고 RTX 3060은 FP8 연산을 지원하지 않아 정수 8bit(Q8_0)로 비트 수만 맞췄습니다. 서버 엔진(Ollama vs furiosa-llm)도 다르므로 하드웨어 단독 비교가 아니라 구성 비교입니다. 시간당 비용과 전력은 재지 않았습니다.

측정 도구는 앱의 프롬프트 빌더를 그대로 재사용하고, 스트리밍으로 첫 토큰 시간을 따로 기록합니다. 앱은 응답을 한 번에 받는 방식이라 앱 안에서는 첫 토큰 시점을 알 수 없기 때문입니다. 처음 로컬 Gemma로 측정했을 때 thinking 모델이 출력 토큰을 모두 추론에 써서 답이 비는 문제가 있었고, 첫 생성 토큰과 첫 답변 토큰을 나눠 기록하도록 바꿨습니다. 실행 방법과 비교 절차는 [LLM 백엔드 벤치마크 문서](backend/docs/llm-backend-benchmark.md)에, 결과 원본은 [benchmarks 폴더](backend/benchmarks/comparisons/)에 있습니다.

## 11. 배포 준비

프론트엔드는 Next.js App Router와 API route를 사용하므로 정적 호스팅이 아니라 **Node.js 런타임이 있는 Azure App Service**를 기준으로 구성했습니다. 백엔드도 같은 App Service에 FastAPI로 배포합니다. 양쪽 모두 package/deploy 2단계 스크립트를 제공해, 빌드 산출물 생성과 배포를 분리했습니다.

- 프론트엔드: `npm run azure:package`, `npm run azure:deploy`
- 백엔드: [scripts/azure-package.sh](backend/scripts/azure-package.sh), [scripts/azure-deploy.sh](backend/scripts/azure-deploy.sh)

## 12. 설계 성과

구현 범위는 4장과 9장에, 문제 해결 과정은 13장에 정리했습니다. 이 장에는 그중 **설계 판단에 해당하는 결과만** 남겼습니다.

- 단순 기록 앱이 아니라 기록, 분석, 제안, 알림, 대화로 이어지는 agent 제품 흐름을 설계했습니다.
- `presentation -> application -> infrastructure` 계층 구조로 HTTP, DB, LLM SDK 의존성을 분리했습니다.
- LangGraph를 기록 분석 파이프라인과 쇼핑 추천 에이전트에 적용해 단계별 상태 업데이트를 테스트하고 관찰할 수 있게 했습니다.
- LLM provider를 기능별로 분리해 기록 구조화, 기록 요약, 케어 답변, 펫 페르소나, 이미지 기록 이해로 확장할 수 있게 했습니다.
- Gemma(Ollama)와 GPT를 primary/fallback으로 전환할 수 있는 하이브리드 LLM 구조를 지원했습니다.
- RAG, 이미지 기록 이해, 병원 제출용 리포트, 커머스 개인화로 확장 가능한 경계를 마련했습니다.

## 13. 시행착오와 해결 과정

### 13.1 실패 지점마다 반환값을 먼저 정의해 장애를 격리

**문제**

쇼핑 추천은 Naver Shopping API, 병원 추천은 Google Places API에 의존하고, 쇼핑 추천 내부에는 두 번의 LLM 판단이 더 있습니다. 이들은 API key 미설정, quota 소진, 타임아웃, 결과 0건, LLM 응답 실패로 언제든 결과를 주지 못할 수 있습니다. 그런데 쇼핑 추천은 기록 저장과 같은 요청, 같은 그래프 안에서 `save_records → suggest_care → recommend_shopping` 순으로 실행됩니다. 예외가 그대로 올라가면 쇼핑 추천 한 단계의 실패가 요청 전체를 500으로 만듭니다. 기록은 이미 DB에 저장된 뒤인데 사용자에게는 저장 실패로 보여, 재시도로 같은 기록이 중복 저장됩니다. **부가 기능의 실패가 핵심 기능의 성공까지 무효로 만드는 구조입니다.**

**판단**

`try/except`를 에이전트마다 흩뿌리면 어떤 실패가 어디서 처리되는지 추적할 수 없습니다. 그래서 코드를 쓰기 전에 **각 실패 지점에서 무엇을 반환할지 표로 먼저 확정**했습니다. 핵심은 실패 지점마다 남아 있는 정보의 양이 달라서 복구 정책도 달라야 한다는 점이었습니다.

| 실패 지점 | 반환 | 근거 |
| --- | --- | --- |
| 카테고리 생성 LLM 실패 | 빈 추천으로 종료 | 무엇을 추천할지 모르는 상태. 근거 없는 추천을 노출하지 않는 편이 낫습니다 |
| 검색 결과 0건 + 카테고리 있음 | 규칙 fallback 억제, 빈 결과 | 에이전트가 정한 카테고리를 규칙 추천이 덮어써 모순되는 것을 방지 |
| 검색 실패 + 카테고리 없음 | 기록 기반 규칙 검색 링크 | 최소한의 다음 행동을 남김 |
| 후보 선택 LLM 실패 | 첫 번째 후보 유지 | 후보 자체는 유효하므로 추천을 잃을 이유가 없음 |
| 선택 결과가 후보에 없는 URL | 첫 번째 후보로 대체 | 환각으로 존재하지 않는 상품이 노출되는 경로를 차단 |
| Google Places 예외 또는 0건 | Google Maps 검색 링크 1건 | 대체 결과임을 알리는 안내 문구를 함께 반환 |
| rate limit 초과 | 예외가 아니라 빈 결과 | 바깥 fallback 계층이 자연스럽게 흡수하도록 |

이 정책을 에이전트 본문이 아니라 **provider를 감싸는 미들웨어 체인**에 배치해, 계층마다 책임을 하나씩만 갖게 했습니다.

```python
# composition.py — 바깥에서 안쪽 순서로 fallback → cache/rate limit → 실제 API
HospitalRecommendationAgent(
    HospitalFallbackMiddleware(HospitalCacheRateLimitMiddleware(GooglePlacesClient()))
)
```

```python
# application/agents/shopping.py — 선택 단계는 실패해도 후보를 잃지 않는다
fallback = candidates[0]
try:
    selection = self._recommendation_agent.select_recommendation(...)
except Exception as exc:
    logger.warning("shopping_selection_agent_failed error=%s detail=%s", exc.__class__.__name__, exc)
    return fallback
selected = _find_selected_candidate(selection.product_url, candidates)
return replace(selected, reason=selection.reason) if selected else fallback
```

**결과**

- API key가 전혀 없는 환경에서도 서버가 정상 기동하고, 병원·쇼핑 화면이 오류 대신 사용 가능한 대체 결과를 보여줍니다.
- 동일 좌표(소수점 3자리) 반복 조회는 **TTL 600초 캐시로 외부 호출 1회에 수렴**하고, **60초당 30회** 상한으로 quota 소진을 막습니다. Naver 호출은 **타임아웃 3초**, LLM에는 쿼리당 **상위 3개 후보만** 전달해 토큰과 지연에 상한을 뒀습니다.
- LLM 한 단계가 실패해도 추천이 사라지지 않고 품질이 한 단계 낮은 결과로 하강합니다. 모든 실패는 예외 클래스명과 함께 구조화 로그로 남습니다.
- 정상 경로와 실패 경로를 **테스트 19개**(쇼핑 11, 병원 8)로 나눠 검증했습니다.

**회고**

처음에는 "LLM 호출을 `try/except`로 감싸면 된다"고 생각했지만, 중요한 것은 예외를 잡는 일이 아니라 각 실패 지점에서 무엇을 반환할지 결정하는 일이었습니다. 이 결정을 표로 정리하고 나서야 실패 케이스별로 테스트를 나눌 수 있었고, "이 기능은 실패하면 무엇을 보여주는가"를 코드로 설명할 수 있게 되었습니다.

관련 파일: [shopping.py](backend/src/application/agents/shopping.py), [middleware](backend/src/middleware), [naver_shopping.py](backend/src/infrastructure/shopping/naver_shopping.py)

### 13.2 기능 복잡도에 맞춰 LangGraph 적용 범위를 결정

**문제**

모든 AI 기능을 graph로 표현하면 기술 스택은 통일되지만, 단순한 규칙 흐름까지 상태 타입·노드·엣지를 정의해야 해서 코드가 길어지고 제어 흐름이 엣지 선언으로 흩어집니다. 무엇보다 "왜 LangGraph를 썼는가"에 "요구사항이라서"라고 답하게 됩니다.

**판단**

기준을 **"상태 전이가 존재하는가"** 하나로 정하고, 다음 셋 중 둘 이상을 만족할 때만 적용했습니다.

1. 단계가 3개 이상이고 각 단계가 앞 단계 결과에 의존한다.
2. 중간에 조건부 분기가 필요하다.
3. 단계별 중간 상태를 관찰하거나 개별적으로 테스트할 가치가 있다.

**적용한 곳 ① 기록 입력 파이프라인** — `detect_risk` 이후 조건부 엣지로 미리보기 흐름과 저장 흐름이 갈립니다. "AI 구조화 결과를 확인한 뒤 저장한다"는 제품 요구사항이 그래프 구조에 그대로 드러납니다.

```text
structure_record → load_context → analyze_context → detect_risk
   ├─(미리보기 또는 확인 필요)→ build_confirmation_result → END
   └─(확정 저장)→ save_records → suggest_care → recommend_shopping → plan_reminders → build_saved_result → END
```

**적용한 곳 ② 쇼핑 추천** — `prepare_categories → search_products → select_recommendations → build_result`. 13.1의 실패 정책이 노드 경계와 정확히 일치합니다.

**적용하지 않은 곳: 병원 추천** — 응급 판단 → 반경 조정 → 검색 → 필터·정렬이 모두 분기 없는 단일 경로이고 각 단계가 순수 함수에 가까워, 일반 application agent로 두는 편이 짧고 명확했습니다.

```python
# application/agents/hospital.py — graph 없이도 읽히는 선형 흐름
emergency_mode = query.emergency or _is_late_hour(current_time) or _has_emergency_terms(query.text)
radius_meters = max(query.radius_meters, 10_000) if emergency_mode else query.radius_meters
hospitals = self._hospital_provider.search(
    ..., search_query="24시 동물병원" if emergency_mode else "동물병원", require_24_hours=emergency_mode,
)
```

**결과**

graph를 쓴 흐름은 `stream_updates()`로 노드 단위 상태 변화를 스트리밍하고, 노드가 끝날 때마다 갱신된 상태 키를 로그로 남깁니다. 덕분에 미리보기 분기와 저장 분기를 각각 **테스트 7개**로 나눠 검증할 수 있었습니다. 반대로 단순한 흐름은 짧고 명시적인 코드로 남았고, 기술 선택에 대해 "이 기능은 왜 graph가 아닌가"까지 근거를 갖고 설명할 수 있게 되었습니다.

**회고**

프레임워크를 넓게 적용하는 것보다 적용 기준을 명문화하는 쪽이 더 어려웠습니다. 실제로 초기에는 병원 추천도 graph로 만들려다, 노드 3개가 전부 단순 대입인 것을 보고 되돌렸습니다. 도구는 문제의 형태를 따라가야지 문제를 도구의 형태로 바꾸면 안 된다는 것을 배웠습니다.

관련 파일: [pet_log_graph.py](backend/src/application/pipelines/pet_log_graph.py), [hospital.py](backend/src/application/agents/hospital.py)

### 13.3 건강 도메인의 안전 경계 유지

**문제**

Pet Log는 구토, 혈변, 호흡 이상, 식욕 저하처럼 건강과 직결된 기록을 다룹니다. 사용자는 "병원 가야 하나요"를 알고 싶어 하고 LLM은 그럴듯하게 답할 수 있지만, "위염일 가능성이 높습니다" 같은 문장은 병원 방문 결정을 지연시킬 수 있습니다. 반대로 모든 건강 질문을 회피하면 제품 가치가 사라집니다.

**판단**

문제는 모델 성능이 아니라 출력의 역할 정의에 있었습니다. 에이전트가 "판단하는 주체"인지 "판단을 돕는 도구"인지 흐릿하면 출력 문장의 강도도 흐릿해집니다. 그래서 경계를 프롬프트 문장이 아니라 **구조로** 강제했습니다.

- **탐지와 제안을 다른 에이전트로 분리** — `RiskDetectionAgent`는 위험 신호 여부만 판정하고 무엇을 하라는 말은 하지 않습니다. 행동 제안은 `SuggestionAgent`가 담당합니다. 한 에이전트가 "위험하다 + 이렇게 하라"를 동시에 말하지 못하게 막았습니다.
- **위험 판정은 교체 가능한 정책 객체로** — `RiskSignalPolicy`가 반환한 `SafetyNotice`만 알림으로 승격됩니다. LLM이 위험 여부를 자유롭게 판단하지 못합니다.
- **출력 어휘 제한** — 진단명·처방 대신 관찰 항목과 병원 상담 권장 문구를 사용하도록 프롬프트와 응답 매퍼를 설계했습니다.
- **불확실하면 사용자에게 확인 요청** — 구조화 결과의 `needs_confirmation` 플래그가 서면 저장 대신 미리보기 분기로 라우팅합니다(13.2의 조건부 엣지).
- **응급 문맥은 규칙으로 강화** — "응급·야간·24시·호흡·출혈·경련·중독" 표현이나 22시~6시에는 검색 반경을 10km 이상으로 넓히고 24시간 병원을 우선 정렬합니다. 판단 주체는 LLM이 아니라 명시적 규칙입니다.
- **반복 노출 차단** — 안전 알림은 `risk` 종류로 분류되고 메시지 해시 기반 중복 제거 키를 받아, 같은 위험이 반복 노출되어 둔감해지는 것을 막습니다.
- **고위험 도구는 승인과 제한** — `HumanInTheLoopMiddleware` 기반 승인 미들웨어와 함께 재시도, 도구 호출 횟수 제한, 입력 PII 마스킹을 factory로 구성했습니다.

```python
# application/agents/risk_detection.py — 탐지 에이전트는 판정만 위임한다
class RiskDetectionAgent:
    def detect(self, text, records) -> tuple[SafetyNotice, ...]:
        return self._risk_signal_policy.detect_risks(text, records)
```

**결과와 한계**

위험 기록이 `risk` 알림으로 승격되는 경로와 중복 제거 키 형식을 **테스트 8개**로 검증했고, 정책이 비어 있을 때도 파이프라인이 안전하게 진행되는지 함께 확인했습니다. 다만 `RiskSignalPolicy`와 `SafetyGuard`는 인터페이스와 배선까지 완성했지만 판정 규칙 본문은 최소 구현 상태입니다. **안전 경계의 구조는 갖췄고 규칙 채우기가 다음 단계**라는 것이 정확한 현재 상태입니다.

**회고**

건강 도메인에서 배운 가장 큰 교훈은 "AI가 무엇을 말할 수 있는가"보다 **"AI가 무엇을 말하면 안 되는가"를 먼저 정해야 한다**는 것이었습니다. 그리고 그 경계는 에이전트 분리와 정책 객체라는 구조로 강제해야 실제로 지켜졌습니다. 프롬프트만으로 막으려 했다면 모델을 바꿀 때마다 다시 무너졌을 것입니다.

관련 파일: [risk_detection.py](backend/src/application/agents/risk_detection.py), [notifications/policy.py](backend/src/infrastructure/notifications/policy.py), [safety.py](backend/src/middleware/safety.py)

### 13.4 프로젝트 회고

**잘한 결정**

- **계층 경계를 처음부터 강제한 것** — `application`과 `domain`이 FastAPI·SQLite·LLM SDK를 모르기 때문에 provider 교체와 미들웨어 추가가 상위 코드 변경 없이 가능했습니다. 금지 import를 `rg`로 검사하는 명령을 검증 절차에 넣어 경계가 무너지지 않게 했습니다.
- **저장소를 처음부터 SQLite로 둔 것** — 첫 스프린트부터 실제 DB에 기록을 쌓았기 때문에, 누적 기록을 전제로 하는 패턴 분석과 누락 기록 탐지를 만들 때 정렬 기준·시간대·중복 같은 문제를 실제 데이터로 바로 확인할 수 있었습니다.
- **실패 정책을 미들웨어로 분리한 것** — "이 기능은 실패하면 무엇을 반환하는가"가 파일 하나에 모여 리뷰와 테스트 대상이 명확해졌습니다.
- **프레임워크 적용 기준을 명문화한 것** — LangGraph를 쓴 이유와 쓰지 않은 이유를 모두 설명할 수 있게 되었습니다.

**아쉬운 결정**

- **정량 평가 지표를 뒤늦게 준비한 것** — 구조화 정확도, 카테고리 적중률, 응답 지연, 실패율을 처음부터 측정했다면 프롬프트 변경의 효과를 숫자로 말할 수 있었을 것입니다. 현재는 **백엔드 테스트 265개**로 동작을 보장하지만, 품질을 수치로 추적하지는 못합니다.
- **안전 정책의 규칙 구현이 최소 수준인 것** — 인터페이스 설계와 규칙 채우기를 같은 작업 단위로 묶었어야 했습니다.

**다시 한다면 이 순서로**

1. 대표 입력 30~50건과 기대 출력으로 **평가 셋을 먼저** 만들고 시작합니다. 프롬프트를 고칠 때마다 회귀를 확인할 수 있어야 합니다.
2. 저장소는 이번처럼 처음부터 실제 DB로 두고 repository 인터페이스를 함께 유지합니다.
3. 각 외부 의존성과 LLM 단계에 대해 **실패 정책 표를 코드보다 먼저** 확정합니다.
4. 노드 단위 로그와 구조화 로그를 초기에 배선합니다. 나중에 넣으면 이미 디버깅에 시간을 쓴 뒤입니다.

이 프로젝트에서 얻은 핵심 역량은 LLM을 호출하는 능력이 아니라, **LLM과 외부 API가 실패할 수 있다는 전제 위에서 제품이 계속 동작하도록 경계와 정책을 설계하는 능력**입니다.

## 14. 향후 개선 방향

- 승인된 케어 지식 URL을 수집하고, chunking, embedding, similarity search, citation prompt를 포함한 RAG 답변을 고도화합니다.
- 사진 기반 사료량, 배변 상태, 자세, 행동 기록 이해 기능을 강화합니다.
- 누적 기록과 증상 요약을 병원 제출용 리포트로 정리하고 예약/상담 흐름과 연결합니다.
- 건강 상태와 기록 맥락을 기반으로 사료, 용품, 보험, 제휴 상품 추천을 정교화합니다.
- 가족/보호자 초대, 역할 설정, 산책·다이어트·문제행동 개선 미션 같은 공동 관리 기능을 확장합니다.
