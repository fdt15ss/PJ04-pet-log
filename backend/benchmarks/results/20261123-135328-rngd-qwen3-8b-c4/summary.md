# LLM 백엔드 성능 비교 결과

- 측정 시각: 2026-11-23T13:53:28
- 반복 횟수(시나리오당): 16 / 워밍업: 1 / 동시성: 4
- 최대 출력 토큰: 256

| 시나리오 | 백엔드 | 종류 | 모델 | TTFT p50 | TTFT p95 | 첫 답변 p50 | 생성 tok/s p50 | 처리량 tok/s | 1K 요청 비용 | 1M 출력 토큰 비용 | 오류 |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| record_structuring | rngd-furiosa-qwen3-8b | npu | `furiosa-ai/Qwen3-8B-FP8` | 0.080s | 0.082s | 0.080s | 93.3 | 363.2 | - | - | 0/16 |
| care_question | rngd-furiosa-qwen3-8b | npu | `furiosa-ai/Qwen3-8B-FP8` | 0.079s | 0.095s | 0.079s | 97.8 | 352.8 | - | - | 0/16 |
| pet_chat | rngd-furiosa-qwen3-8b | npu | `furiosa-ai/Qwen3-8B-FP8` | 0.060s | 0.081s | 0.060s | 97.1 | 332.3 | - | - | 0/16 |
| shopping_category | rngd-furiosa-qwen3-8b | npu | `furiosa-ai/Qwen3-8B-FP8` | 0.080s | 0.083s | 0.080s | 95.9 | 358.0 | - | - | 0/16 |
| shopping_selection | rngd-furiosa-qwen3-8b | npu | `furiosa-ai/Qwen3-8B-FP8` | 0.066s | 0.086s | 0.066s | 90.2 | 326.0 | - | - | 0/16 |

## 시나리오 설명

- `record_structuring`: 기록 입력 구조화 (POST /records 계열)
- `care_question`: 케어 질문 답변 (AI 케어 패널)
- `pet_chat`: 반려동물 페르소나 대화
- `shopping_category`: 쇼핑 에이전트 1단계: 검색 상품군 결정
- `shopping_selection`: 쇼핑 에이전트 2단계: Top 3 후보 중 선택 + 추천 이유

## 지표 정의

- TTFT: 요청 전송부터 첫 생성 토큰(추론 토큰 포함) 수신까지 걸린 시간. 하드웨어 prefill 지연 비교용.
- 첫 답변: 요청 전송부터 첫 답변(content) 토큰까지 걸린 시간. 사용자가 체감하는 지연이며 thinking 모델은 TTFT보다 길다.
- `†`: 최대 출력 토큰 안에 답변 없이 추론만 생성한 요청이 있다. `--max-tokens`를 늘리거나 thinking을 끄고 다시 측정한다.
- 생성 tok/s: 첫 토큰 이후 생성 속도 `(출력 토큰 - 1) / (전체 시간 - TTFT)`. 요청 하나 기준.
- 처리량 tok/s: 배치 전체 출력 토큰 / 배치 wall time. 동시성을 올리면 하드웨어의 batching 효율이 드러난다.
- 비용: API는 `입력·출력 토큰 × 1M 토큰 단가`, RNGD/GPU는 `시간당 단가 × 배치 wall time`으로 계산한다. 단가가 비어 있으면 `-`.
- `*`: 서버가 usage를 주지 않아 스트리밍 chunk 수로 토큰 수를 추정한 값.
