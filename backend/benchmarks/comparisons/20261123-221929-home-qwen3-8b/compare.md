# LLM 백엔드 비교표

## 실행 환경

| 실행 폴더 | 머신 | 하드웨어 | 런타임 | 양자화 | runs | warmup | 동시성 | max_tokens |
|---|---|---|---|---|---:|---:|---:|---:|
| `20261123-221252-home-qwen3-8b-c1` | home-pc | NVIDIA GeForce RTX 3060 12GB (driver 610.88) | Ollama 0.40.17 (OpenAI 호환 /v1) | Q4_K_M (4bit) | 10 | 1 | 1 | 256 |
| `20261123-221424-home-qwen3-8b-c4` | home-pc | NVIDIA GeForce RTX 3060 12GB (driver 610.88) | Ollama 0.40.17 (OpenAI 호환 /v1) | Q4_K_M (4bit) | 16 | 1 | 4 | 256 |

## 전체 요약 (시나리오 평균)

| 동시성 | 백엔드 | 모델 | TTFT p50 | 첫 답변 p50 | 생성 tok/s | 처리량 tok/s | 1K 요청 비용 | 오류 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | home-ollama-qwen3-8b | `qwen3:8b` | 0.046s | 0.046s | 53.6 | 52.2 | - | 0/50 |
| 4 | home-ollama-qwen3-8b | `qwen3:8b` | 4.733s | 4.733s | 51.6 | 51.3 | - | 0/80 |

## 시나리오별 비교

| 동시성 | 시나리오 | 백엔드 | 실행 폴더 | TTFT p50 | 첫 답변 p50 | 생성 tok/s | 처리량 tok/s | 1K 요청 비용 | 오류 |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|
| 1 | care_question | home-ollama-qwen3-8b | `20261123-221252-home-qwen3-8b-c1` | 0.044s | 0.044s | 53.9 | 52.3 | - | 0/10 |
| 1 | pet_chat | home-ollama-qwen3-8b | `20261123-221252-home-qwen3-8b-c1` | 0.043s | 0.043s | 54.7 | 53.6 | - | 0/10 |
| 1 | record_structuring | home-ollama-qwen3-8b | `20261123-221252-home-qwen3-8b-c1` | 0.046s | 0.046s | 52.9 | 51.9 | - | 0/10 |
| 1 | shopping_category | home-ollama-qwen3-8b | `20261123-221252-home-qwen3-8b-c1` | 0.047s | 0.047s | 53.2 | 52.3 | - | 0/10 |
| 1 | shopping_selection | home-ollama-qwen3-8b | `20261123-221252-home-qwen3-8b-c1` | 0.048s | 0.048s | 53.2 | 50.8 | - | 0/10 |
| 4 | care_question | home-ollama-qwen3-8b | `20261123-221424-home-qwen3-8b-c4` | 4.034s | 4.034s | 52.3 | 51.7 | - | 0/16 |
| 4 | pet_chat | home-ollama-qwen3-8b | `20261123-221424-home-qwen3-8b-c4` | 3.533s | 3.533s | 52.1 | 51.8 | - | 0/16 |
| 4 | record_structuring | home-ollama-qwen3-8b | `20261123-221424-home-qwen3-8b-c4` | 6.560s | 6.560s | 52.7 | 52.5 | - | 0/16 |
| 4 | shopping_category | home-ollama-qwen3-8b | `20261123-221424-home-qwen3-8b-c4` | 5.513s | 5.513s | 50.8 | 50.6 | - | 0/16 |
| 4 | shopping_selection | home-ollama-qwen3-8b | `20261123-221424-home-qwen3-8b-c4` | 4.027s | 4.027s | 50.2 | 50.0 | - | 0/16 |
