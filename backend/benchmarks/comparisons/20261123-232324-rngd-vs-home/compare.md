# LLM 백엔드 비교표

## 실행 환경

| 실행 폴더 | 머신 | 하드웨어 | 런타임 | 양자화 | runs | warmup | 동시성 | max_tokens |
|---|---|---|---|---|---:|---:|---:|---:|
| `20261123-135130-rngd-qwen3-8b-c1` | rngd-server | FuriosaAI RNGD x1 (npu:7) | furiosa-llm 2026.4.0 (--enable-overlap-scheduling) | FP8 | 10 | 1 | 1 | 256 |
| `20261123-135328-rngd-qwen3-8b-c4` | rngd-server | FuriosaAI RNGD x1 (npu:7) | furiosa-llm 2026.4.0 (--enable-overlap-scheduling) | FP8 | 16 | 1 | 4 | 256 |
| `20261123-230107-home-qwen3-8b-c1` | home-pc | NVIDIA GeForce RTX 3060 12GB (driver 610.88) | Ollama 0.40.17 (OpenAI 호환 /v1) | Q4_K_M (4bit) | 10 | 1 | 1 | 256 |
| `20261123-230235-home-qwen3-8b-c4` | home-pc | NVIDIA GeForce RTX 3060 12GB (driver 610.88) | Ollama 0.40.17 (OpenAI 호환 /v1) | Q4_K_M (4bit) | 16 | 1 | 4 | 256 |
| `20261123-231611-home-qwen3-8b-q8-c1` | home-pc | NVIDIA GeForce RTX 3060 12GB (driver 610.88) | Ollama 0.40.17 (OpenAI 호환 /v1) | Q8_0 (8bit) | 10 | 1 | 1 | 256 |
| `20261123-231901-home-qwen3-8b-q8-c4` | home-pc | NVIDIA GeForce RTX 3060 12GB (driver 610.88) | Ollama 0.40.17 (OpenAI 호환 /v1) | Q8_0 (8bit) | 16 | 1 | 4 | 256 |

## 전체 요약 (시나리오 평균)

| 동시성 | 백엔드 | 모델 | TTFT p50 | 첫 답변 p50 | 생성 tok/s | 처리량 tok/s | 1K 요청 비용 | 오류 |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | home-ollama-qwen3-8b | `qwen3:8b` | 0.042s | 0.042s | 58.3 | 56.9 | - | 0/50 |
| 1 | home-ollama-qwen3-8b-q8 | `qwen3:8b-q8_0` | 0.052s | 0.052s | 37.4 | 36.9 | - | 0/50 |
| 1 | rngd-furiosa-qwen3-8b | `furiosa-ai/Qwen3-8B-FP8` | 0.027s | 0.027s | 104.4 | 102.3 | - | 0/50 |
| 4 | home-ollama-qwen3-8b | `qwen3:8b` | 4.121s | 4.121s | 58.5 | 58.2 | - | 0/80 |
| 4 | home-ollama-qwen3-8b-q8 | `qwen3:8b-q8_0` | 8.797s | 8.797s | 37.5 | 37.4 | - | 0/80 |
| 4 | rngd-furiosa-qwen3-8b | `furiosa-ai/Qwen3-8B-FP8` | 0.073s | 0.073s | 94.9 | 346.4 | - | 0/80 |

## 시나리오별 비교

배수 기준: `home-ollama-qwen3-8b` (처리량 배수 > 1 이면 더 빠름, TTFT 배수 < 1 이면 첫 토큰이 더 빠름)

| 동시성 | 시나리오 | 백엔드 | 실행 폴더 | TTFT p50 | 첫 답변 p50 | 생성 tok/s | 처리량 tok/s | 1K 요청 비용 | 오류 | 처리량 배수 | TTFT 배수 |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | care_question | home-ollama-qwen3-8b | `20261123-230107-home-qwen3-8b-c1` | 0.041s | 0.041s | 58.9 | 56.5 | - | 0/10 | 1.00x | 1.00x |
| 1 | care_question | home-ollama-qwen3-8b-q8 | `20261123-231611-home-qwen3-8b-q8-c1` | 0.050s | 0.050s | 37.7 | 37.3 | - | 0/10 | 0.66x | 1.22x |
| 1 | care_question | rngd-furiosa-qwen3-8b | `20261123-135130-rngd-qwen3-8b-c1` | 0.027s | 0.027s | 104.2 | 101.6 | - | 0/10 | 1.80x | 0.65x |
| 1 | pet_chat | home-ollama-qwen3-8b | `20261123-230107-home-qwen3-8b-c1` | 0.040s | 0.040s | 59.5 | 57.8 | - | 0/10 | 1.00x | 1.00x |
| 1 | pet_chat | home-ollama-qwen3-8b-q8 | `20261123-231611-home-qwen3-8b-q8-c1` | 0.050s | 0.050s | 37.9 | 37.2 | - | 0/10 | 0.64x | 1.24x |
| 1 | pet_chat | rngd-furiosa-qwen3-8b | `20261123-135130-rngd-qwen3-8b-c1` | 0.027s | 0.027s | 104.3 | 102.8 | - | 0/10 | 1.78x | 0.67x |
| 1 | record_structuring | home-ollama-qwen3-8b | `20261123-230107-home-qwen3-8b-c1` | 0.043s | 0.043s | 57.3 | 56.6 | - | 0/10 | 1.00x | 1.00x |
| 1 | record_structuring | home-ollama-qwen3-8b-q8 | `20261123-231611-home-qwen3-8b-q8-c1` | 0.054s | 0.054s | 36.7 | 36.6 | - | 0/10 | 0.65x | 1.26x |
| 1 | record_structuring | rngd-furiosa-qwen3-8b | `20261123-135130-rngd-qwen3-8b-c1` | 0.027s | 0.027s | 104.5 | 103.7 | - | 0/10 | 1.83x | 0.63x |
| 1 | shopping_category | home-ollama-qwen3-8b | `20261123-230107-home-qwen3-8b-c1` | 0.043s | 0.043s | 58.2 | 57.2 | - | 0/10 | 1.00x | 1.00x |
| 1 | shopping_category | home-ollama-qwen3-8b-q8 | `20261123-231611-home-qwen3-8b-q8-c1` | 0.053s | 0.053s | 37.4 | 37.0 | - | 0/10 | 0.65x | 1.25x |
| 1 | shopping_category | rngd-furiosa-qwen3-8b | `20261123-135130-rngd-qwen3-8b-c1` | 0.027s | 0.027s | 104.1 | 102.1 | - | 0/10 | 1.79x | 0.64x |
| 1 | shopping_selection | home-ollama-qwen3-8b | `20261123-230107-home-qwen3-8b-c1` | 0.042s | 0.042s | 57.8 | 56.4 | - | 0/10 | 1.00x | 1.00x |
| 1 | shopping_selection | home-ollama-qwen3-8b-q8 | `20261123-231611-home-qwen3-8b-q8-c1` | 0.054s | 0.054s | 37.2 | 36.4 | - | 0/10 | 0.64x | 1.27x |
| 1 | shopping_selection | rngd-furiosa-qwen3-8b | `20261123-135130-rngd-qwen3-8b-c1` | 0.027s | 0.027s | 104.6 | 101.1 | - | 0/10 | 1.79x | 0.64x |
| 4 | care_question | home-ollama-qwen3-8b | `20261123-230235-home-qwen3-8b-c4` | 3.586s | 3.586s | 59.1 | 58.8 | - | 0/16 | 1.00x | 1.00x |
| 4 | care_question | home-ollama-qwen3-8b-q8 | `20261123-231901-home-qwen3-8b-q8-c4` | 7.267s | 7.267s | 37.8 | 37.7 | - | 0/16 | 0.64x | 2.03x |
| 4 | care_question | rngd-furiosa-qwen3-8b | `20261123-135328-rngd-qwen3-8b-c4` | 0.079s | 0.079s | 97.8 | 352.8 | - | 0/16 | 6.00x | 0.02x |
| 4 | pet_chat | home-ollama-qwen3-8b | `20261123-230235-home-qwen3-8b-c4` | 2.653s | 2.653s | 59.6 | 59.2 | - | 0/16 | 1.00x | 1.00x |
| 4 | pet_chat | home-ollama-qwen3-8b-q8 | `20261123-231901-home-qwen3-8b-q8-c4` | 4.087s | 4.087s | 37.9 | 37.7 | - | 0/16 | 0.64x | 1.54x |
| 4 | pet_chat | rngd-furiosa-qwen3-8b | `20261123-135328-rngd-qwen3-8b-c4` | 0.060s | 0.060s | 97.1 | 332.3 | - | 0/16 | 5.61x | 0.02x |
| 4 | record_structuring | home-ollama-qwen3-8b | `20261123-230235-home-qwen3-8b-c4` | 6.010s | 6.010s | 57.8 | 57.6 | - | 0/16 | 1.00x | 1.00x |
| 4 | record_structuring | home-ollama-qwen3-8b-q8 | `20261123-231901-home-qwen3-8b-q8-c4` | 20.738s | 20.738s | 37.1 | 37.1 | - | 0/16 | 0.64x | 3.45x |
| 4 | record_structuring | rngd-furiosa-qwen3-8b | `20261123-135328-rngd-qwen3-8b-c4` | 0.080s | 0.080s | 93.3 | 363.2 | - | 0/16 | 6.31x | 0.01x |
| 4 | shopping_category | home-ollama-qwen3-8b | `20261123-230235-home-qwen3-8b-c4` | 4.848s | 4.848s | 58.1 | 57.8 | - | 0/16 | 1.00x | 1.00x |
| 4 | shopping_category | home-ollama-qwen3-8b-q8 | `20261123-231901-home-qwen3-8b-q8-c4` | 7.655s | 7.655s | 37.5 | 37.3 | - | 0/16 | 0.65x | 1.58x |
| 4 | shopping_category | rngd-furiosa-qwen3-8b | `20261123-135328-rngd-qwen3-8b-c4` | 0.080s | 0.080s | 95.9 | 358.0 | - | 0/16 | 6.20x | 0.02x |
| 4 | shopping_selection | home-ollama-qwen3-8b | `20261123-230235-home-qwen3-8b-c4` | 3.510s | 3.510s | 57.9 | 57.5 | - | 0/16 | 1.00x | 1.00x |
| 4 | shopping_selection | home-ollama-qwen3-8b-q8 | `20261123-231901-home-qwen3-8b-q8-c4` | 4.237s | 4.237s | 37.2 | 37.0 | - | 0/16 | 0.64x | 1.21x |
| 4 | shopping_selection | rngd-furiosa-qwen3-8b | `20261123-135328-rngd-qwen3-8b-c4` | 0.066s | 0.066s | 90.2 | 326.0 | - | 0/16 | 5.67x | 0.02x |
