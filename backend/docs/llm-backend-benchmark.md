# LLM 백엔드 성능 비교 (RNGD / GPU / API)

Pet Log의 LLM 백엔드를 FuriosaAI RNGD(NPU), GPU(vLLM 또는 Ollama), 외부 API(OpenAI)로 바꿔 가며 같은 프롬프트로 TTFT, tokens/s, 비용을 비교하는 도구다. 결과 파일을 그대로 포트폴리오 자료로 쓸 수 있도록 마크다운 표·JSON·CSV로 남긴다.

## 구성

| 파일 | 역할 |
| --- | --- |
| `scripts/benchmark_llm_backends.py` | 실행 CLI. 설정을 읽고 백엔드 × 시나리오를 측정해 결과를 저장한다. |
| `src/infrastructure/llm/benchmark/measure.py` | 스트리밍 요청 1건 측정(TTFT, 생성 속도), 동시 요청 배치, 요약·비용 계산 |
| `src/infrastructure/llm/benchmark/scenarios.py` | 앱의 실제 프롬프트 빌더로 시나리오별 메시지 생성 |
| `src/infrastructure/llm/benchmark/report.py` | `summary.md`, `results.json`, `requests.csv` 작성 |
| `benchmarks/backends.example.toml` | 백엔드 설정 예시 (복사해서 `backends.toml`로 사용, git 제외) |
| `tests/test_llm_benchmark.py` | 가짜 스트림·가짜 시계로 지표·비용 계산 검증 |
| `scripts/compare_benchmark_results.py` | 여러 결과 폴더를 하나의 비교표(`compare.md`, `compare.json`)로 합치는 CLI |
| `src/infrastructure/llm/benchmark/compare.py` | 결과 로딩, 측정 조건 불일치 경고, 시나리오 평균, 기준 백엔드 대비 배수 계산 |
| `tests/test_llm_benchmark_compare.py` | 비교 로직 검증 |

### 왜 앱 안이 아니라 별도 스크립트인가

- 앱의 provider는 LangChain `invoke`(비스트리밍)로 호출한다. 응답이 한 번에 오기 때문에 첫 토큰 시점, 즉 TTFT를 앱 안에서는 잴 수 없다.
- 백엔드 비교는 같은 입력을 여러 번, 같은 조건(워밍업, 동시성, 최대 토큰)으로 반복해야 의미가 있다.
- 그래서 앱의 **프롬프트 빌더는 그대로 재사용**하고, 호출만 OpenAI 호환 스트리밍(`openai` SDK)으로 직접 보낸다. RNGD의 `furiosa-llm serve`, vLLM, Ollama, OpenAI API 모두 `/v1/chat/completions`를 제공하므로 `base_url`과 `model`만 바꿔 같은 코드로 측정한다.

## 측정 시나리오

입력은 in-memory SQLite에 seed 데이터를 넣어 만든다. 매번 같은 반려동물 프로필과 기록이 들어가므로 실행 간 비교가 가능하다. `--database-path`로 실제 DB를 넣을 수도 있다.

| 시나리오 | 앱 기능 | 프롬프트 빌더 |
| --- | --- | --- |
| `record_structuring` | 기록 입력 구조화 | `record_structuring.prompt.build_record_structuring_messages` |
| `care_question` | 케어 질문 답변 (AI 케어 패널) | `care_answer.prompt.build_care_answer_messages` |
| `pet_chat` | 반려동물 페르소나 대화 | `pet_persona.prompt.build_pet_persona_messages` |
| `shopping_category` | 쇼핑 에이전트 1단계: 검색 상품군 결정 | `shopping_reason.prompt.build_shopping_category_messages` |
| `shopping_selection` | 쇼핑 에이전트 2단계: Top 3 후보 선택 + 추천 이유 | `shopping_reason.prompt.build_shopping_selection_messages` |

- 쇼핑 2단계의 후보 상품은 고정된 샘플 3개를 쓴다. 네이버 쇼핑 API 지연이 LLM 측정에 섞이지 않게 하기 위해서다.
- 동물병원 추천은 Google Places 조회와 규칙 기반 정렬(`application/agents/hospital.py`)로 동작하고 LLM을 호출하지 않는다. 그래서 백엔드 비교 대상에서 제외했다.
- 앱의 `record_structuring`은 JSON schema structured output을 쓰지만, 벤치마크는 같은 프롬프트를 일반 chat 요청으로 보낸다. 지연·속도 비교용이며 출력 형식 검증은 하지 않는다.

## 지표 정의

| 지표 | 정의 |
| --- | --- |
| TTFT | 요청 전송부터 첫 생성 토큰(추론 토큰 포함)까지. 하드웨어의 prefill 지연을 비교할 때 쓴다. |
| 첫 답변 | 요청 전송부터 첫 답변(content) 토큰까지. 사용자가 체감하는 지연. thinking 모델은 TTFT보다 길다. |
| 생성 tok/s | 요청 1건 기준 `(출력 토큰 - 1) / (전체 시간 - TTFT)`. 디코딩 속도. |
| 처리량 tok/s | 배치 전체 출력 토큰 / 배치 wall time. `--concurrency`를 올리면 서버의 batching 효율이 드러난다. |
| 1K 요청 비용 | 해당 시나리오 요청 1,000건 비용 |
| 1M 출력 토큰 비용 | 출력 토큰 100만 개당 비용 |

비용 계산:

- API: `입력 토큰 × input_usd_per_1m + 출력 토큰 × output_usd_per_1m` (토큰 수는 서버가 주는 usage 사용)
- RNGD / GPU: `usd_per_hour × 배치 wall time`. 장비는 쓰든 안 쓰든 시간 단위로 비용이 나간다고 보고, 그 시간 동안 처리한 요청·토큰 수로 나눈다. 따라서 동시성 1에서는 하드웨어가 불리하고, 동시성을 올릴수록 실제 운영 비용에 가까워진다.
- 단가를 비워 두면 비용 칸은 `-`로 나온다.

표 기호:

- `*`: 서버가 usage를 주지 않아 스트리밍 chunk 수로 토큰 수를 추정했다.
- `†`: 최대 출력 토큰 안에서 답변 없이 추론만 생성한 요청이 있다.

## 실행 방법

1. 설정 파일을 만든다. API 키는 값 대신 환경변수 이름(`api_key_env`)만 적고, 값은 `backend/.env`에 둔다.

   ```bash
   cp benchmarks/backends.example.toml benchmarks/backends.toml
   ```

2. RNGD 서버에 올라간 Qwen3 8B의 모델 ID를 확인해 `rngd` 항목의 `model`에 넣는다.

   ```bash
   curl http://RNGD_HOST:8000/v1/models
   ```

3. LLM 호출 없이 시나리오 프롬프트가 만들어지는지 확인한다.

   ```bash
   uv run python -B scripts/benchmark_llm_backends.py --dry-run
   ```

4. 측정한다.

   ```bash
   uv run python -B scripts/benchmark_llm_backends.py --runs 10 --label rngd-vs-gpu
   ```

5. 동시성별로 처리량과 비용을 비교한다.

   ```bash
   uv run python -B scripts/benchmark_llm_backends.py --runs 32 --concurrency 8 --label c8
   ```

주요 옵션:

| 옵션 | 기본값 | 설명 |
| --- | --- | --- |
| `--config` | `benchmarks/backends.toml` | 백엔드 설정 파일 |
| `--backends` | 전체 | 측정할 backend `name` (쉼표 구분) |
| `--scenarios` | 전체 | 측정할 시나리오 (쉼표 구분) |
| `--runs` | 5 | 시나리오당 측정 요청 수 |
| `--warmup` | 1 | 기록하지 않는 워밍업 요청 수 |
| `--concurrency` | 1 | 동시에 보낼 요청 수 |
| `--max-tokens` | 256 | 최대 출력 토큰 |
| `--label` | 없음 | 결과 폴더 이름 뒤에 붙는 라벨 |
| `--database-path` | 없음 | seed 대신 실제 SQLite DB로 프롬프트 생성 |

결과는 `benchmarks/results/<YYYYMMDD-HHMMSS>-<라벨>/`에 저장된다.

- `summary.md`: 포트폴리오에 바로 붙일 수 있는 비교표와 지표 정의
- `results.json`: 측정 조건(meta)과 백엔드 × 시나리오 요약
- `requests.csv`: 요청 1건 단위 원본 (그래프용)

## 여러 머신 결과 비교 (RNGD 서버 ↔ 집 PC)

### 1. 이름 규칙

결과를 합칠 때 행은 backend `name`으로, 폴더는 `--label`로 구분된다. 두 머신이 섞여도 구분되도록 **장소-런타임-모델**, **장소-모델-동시성** 형식으로 붙인다.

| 머신 | `backends.toml`의 `name` | `--label` 예시 |
| --- | --- | --- |
| RNGD 서버 | `rngd-furiosa-qwen3-8b` | `rngd-qwen3-8b-c1`, `rngd-qwen3-8b-c4` |
| 집 PC | `home-ollama-qwen3-8b` | `home-qwen3-8b-c1`, `home-qwen3-8b-c4` |

### 2. 측정 조건 맞추기

같은 동시성끼리는 `--runs`, 모든 실행에서 `--warmup`, `--max-tokens`를 같게 한다. 다르면 비교표 맨 위에 경고가 뜬다. 집 PC 기준값은 다음 두 실행이다.

```bash
uv run python -B scripts/benchmark_llm_backends.py --runs 10 --warmup 1 --concurrency 1 --max-tokens 256 --label rngd-qwen3-8b-c1
```

```bash
uv run python -B scripts/benchmark_llm_backends.py --runs 16 --warmup 1 --concurrency 4 --max-tokens 256 --label rngd-qwen3-8b-c4
```

### 3. 실행 환경 기록 (`environment.json`)

측정 스크립트는 하드웨어 정보를 기록하지 않는다. 각 결과 폴더에 `environment.json`을 직접 넣으면 비교표의 "실행 환경" 칸에 표시된다. 표에 쓰이는 키는 `machine`, `gpu`(또는 `accelerator`), `runtime`, `quantization`이고 나머지 키는 `compare.json`에만 남는다.

```json
{
  "machine": "rngd-server",
  "accelerator": "FuriosaAI RNGD x1",
  "runtime": "furiosa-llm <버전>",
  "model": "<서빙 모델 ID>",
  "quantization": "<BF16 / FP8 등>",
  "thinking": "off (chat_template_kwargs.enable_thinking = false)",
  "network": "localhost (같은 서버에서 측정)"
}
```

### 4. 결과 모아서 비교

RNGD 서버의 결과 폴더를 집 PC의 `backend/benchmarks/results/`로 복사한 뒤 실행한다. 폴더를 지정하지 않으면 `results/` 아래 전체를 합친다.

```bash
uv run python -B scripts/compare_benchmark_results.py --baseline home-ollama-qwen3-8b --label rngd-vs-home
```

결과는 `benchmarks/comparisons/<시각>-<라벨>/`에 저장된다.

- `compare.md`: 실행 환경 표, 백엔드 × 동시성별 시나리오 평균(헤드라인 숫자), 시나리오별 비교표
- `compare.json`: 같은 내용의 기계용 데이터

`--baseline`을 주면 같은 시나리오·동시성의 기준 백엔드 대비 배수가 붙는다. 처리량 배수가 1보다 크면 기준보다 빠르고, TTFT 배수가 1보다 작으면 첫 토큰이 더 빠르다.

## 공정한 비교를 위한 체크리스트

- 비교 모델은 **Qwen3 8B**로 맞춘다. RNGD에 올라간 Qwen3 8B와 같은 모델을 GPU에서는 vLLM(`vllm serve Qwen/Qwen3-8B`)으로 띄운다. Ollama `qwen3:8b`는 4bit 양자화라 정밀도가 달라서, 쓰면 결과에 그 사실을 적는다.
- Qwen3는 thinking 모델이다. 양쪽 모두 끄고 잰다.
  - RNGD, vLLM: `extra_body.chat_template_kwargs.enable_thinking = false`
  - Ollama: `extra_body.reasoning_effort = "none"`
- thinking을 끄지 못하거나 서버가 reasoning parser 없이 동작하면 `<think>...</think>`가 content로 섞여 나온다. 이 경우 `첫 답변` 값이 실제보다 빠르게 잡히므로 `requests.csv`의 `output_preview`에 `<think>`가 보이는지 확인한다.
- 워밍업을 1회 이상 둔다. 첫 요청은 모델 로드·컴파일 시간이 섞인다.
- 측정 PC와 서버 사이 네트워크 위치를 기록한다. 원격 서버면 TTFT에 왕복 지연이 포함된다.
- 동시성 1, 4, 8, 16처럼 여러 단계로 측정한다. 단일 요청 지연과 운영 처리량은 다른 이야기다.
- 단가의 출처와 기준일(클라우드 인스턴스 가격, API 가격표)을 결과와 함께 적어 둔다.
- 전력 효율(tokens/W)을 주장하려면 측정 중 장비 전력을 따로 기록해야 한다. 이 스크립트는 전력을 재지 않는다.

## 앱 백엔드를 RNGD로 바꾸기

앱의 로컬 LLM 경로(`GEMMA_*` 환경변수)는 OpenAI 호환 서버라면 Ollama가 아니어도 붙는다. 코드 변경 없이 `.env`만 바꾼다. 복사해 쓸 수 있는 전체 예시는 `backend/.env.example`의 "예시: RNGD(furiosa-llm) Qwen3 8B" 블록에 있다. 아래는 RNGD 서버 안에서 앱을 함께 실행하는 경우다.

```env
LOCAL_LLM_AUTOSTART=0
LOCAL_LLM_RUNTIME=ollama
GEMMA_AUTO_PULL=0
GEMMA_PRELOAD=0
GEMMA_BASE_URL=http://127.0.0.1:8000/v1
GEMMA_MODEL=<RNGD의 Qwen3 8B 모델 ID>
GEMMA_API_KEY=local-gemma
OPENAI_RECORD_STRUCTURING_MODEL=${GEMMA_MODEL}
OPENAI_RECORD_SUMMARY_MODEL=${GEMMA_MODEL}
OPENAI_CARE_ANSWER_MODEL=${GEMMA_MODEL}
OPENAI_PET_PERSONA_MODEL=${GEMMA_MODEL}
OPENAI_SHOPPING_REASON_MODEL=${GEMMA_MODEL}
OPENAI_ACTION_NAVIGATION_MODEL=${GEMMA_MODEL}
OPENAI_SPEECH_TEXT_CORRECTION_MODEL=${GEMMA_MODEL}
OPENAI_IMAGE_RECORD_UNDERSTANDING_MODEL=gpt-5-mini
```

- `LOCAL_LLM_AUTOSTART`, `GEMMA_AUTO_PULL`, `GEMMA_PRELOAD`는 Ollama 전용(`ollama serve`, `ollama pull`)이므로 끈다.
- `LOCAL_LLM_RUNTIME`은 `ollama` 외의 값이면 코드가 오류를 내므로 그대로 둔다. 실제 서버가 furiosa-llm이어도 동작한다.
- `${GEMMA_MODEL}`은 python-dotenv가 펼쳐 준다. 모델 ID는 `GEMMA_MODEL` 한 줄만 바꾸면 된다.
- Qwen3 8B는 텍스트 전용이라 사진 기록 이해는 GPT를 유지한다.
- `GEMINI_API_KEY` 또는 `GOOGLE_API_KEY`가 있으면 `gemini-2.0-flash`가 폴백으로 자동 추가된다. RNGD 결과만 보려면 비운다.
- `OPENAI_*_MODEL`이 `GEMMA_MODEL`과 같으면 해당 기능은 `GEMMA_BASE_URL`로 호출된다 (`infrastructure/llm/model_factory.py`).
- 기록 구조화·요약처럼 structured output을 쓰는 기능은 서버가 JSON schema 응답을 지원하는지 먼저 확인한다.
- 앱의 provider는 지금 `enable_thinking = false`를 보내지 않는다. 서버에서 thinking이 기본으로 켜져 있으면 응답에 추론이 섞여 쇼핑 에이전트처럼 JSON을 파싱하는 기능이 실패할 수 있다. 서버 실행 옵션에서 thinking을 끄거나 앱 쪽에 옵션을 추가해야 한다.

## 동작 확인 기록

2026-11-23, 개발 PC의 Ollama `gemma4:e2b`(thinking 켜짐, `--max-tokens 512`, 동시성 1, 시나리오당 3회)로 스크립트 전체 흐름을 확인했다. 비교 대상 모델(Qwen3 8B)이 아니라 동작 확인용 측정이며, 비용은 임시 단가라 의미 없다.

- TTFT p50은 시나리오별 0.06~0.07초, 생성 속도 p50은 159~198 tok/s였다.
- `record_structuring`, `shopping_category`, `shopping_selection`은 512토큰을 모두 thinking에 써서 답변이 나오지 않았다(†). 케어 질문·대화도 첫 답변까지 2.7~3.1초가 걸렸다. RNGD와 비교할 때는 thinking을 끄고 측정해야 한다.
- 동시성 4로 `pet_chat`을 보냈을 때 TTFT p50이 5.9초로 늘었다. 이 PC의 Ollama 설정에서는 요청이 사실상 순서대로 처리됐다(`OLLAMA_NUM_PARALLEL` 값에 따라 달라진다). GPU 기준선은 continuous batching을 하는 vLLM으로 잡는 것이 공정하다.
