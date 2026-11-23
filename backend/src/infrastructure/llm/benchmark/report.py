from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from infrastructure.llm.benchmark.measure import BatchResult
from infrastructure.llm.benchmark.scenarios import SCENARIO_DESCRIPTIONS

REQUEST_CSV_FIELDS = (
    "backend",
    "scenario",
    "concurrency",
    "ttft_s",
    "ttft_content_s",
    "e2e_s",
    "decode_tokens_per_s",
    "input_tokens",
    "output_tokens",
    "tokens_estimated",
    "error",
    "output_preview",
)


def write_report(
    output_dir: Path,
    *,
    meta: dict[str, Any],
    summaries: list[dict[str, Any]],
    batches: list[BatchResult],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "results.json").write_text(
        json.dumps({"meta": meta, "summaries": summaries}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    with (output_dir / "requests.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=REQUEST_CSV_FIELDS)
        writer.writeheader()
        for batch in batches:
            for request in batch.requests:
                row = asdict(request)
                row["concurrency"] = batch.concurrency
                row["decode_tokens_per_s"] = request.decode_tokens_per_s
                writer.writerow({key: row.get(key) for key in REQUEST_CSV_FIELDS})
    (output_dir / "summary.md").write_text(render_markdown(meta, summaries), encoding="utf-8")


def render_markdown(meta: dict[str, Any], summaries: list[dict[str, Any]]) -> str:
    lines = [
        "# LLM 백엔드 성능 비교 결과",
        "",
        f"- 측정 시각: {meta.get('started_at', '-')}",
        f"- 반복 횟수(시나리오당): {meta.get('runs')} / 워밍업: {meta.get('warmup')} / 동시성: {meta.get('concurrency')}",
        f"- 최대 출력 토큰: {meta.get('max_tokens')}",
        "",
        "| 시나리오 | 백엔드 | 종류 | 모델 | TTFT p50 | TTFT p95 | 첫 답변 p50 | 생성 tok/s p50 | 처리량 tok/s | 1K 요청 비용 | 1M 출력 토큰 비용 | 오류 |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        tokens_mark = "*" if row.get("tokens_estimated") else ""
        lines.append(
            "| {scenario} | {backend} | {kind} | `{model}` | {ttft50} | {ttft95} | {content50} | {tps}{mark} | {thr}{mark} | {c1k} | {c1m} | {err}/{req} |".format(
                scenario=row["scenario"],
                backend=row["backend"],
                kind=row["kind"],
                model=row["model"],
                ttft50=_seconds(row["ttft_p50_s"]),
                ttft95=_seconds(row["ttft_p95_s"]),
                content50=_seconds(row["ttft_content_p50_s"]) + (" †" if row.get("no_content_requests") else ""),
                tps=_number(row["decode_tokens_per_s_p50"]),
                thr=_number(row["throughput_tokens_per_s"]),
                mark=tokens_mark,
                c1k=_usd(row["cost_usd_per_1k_requests"]),
                c1m=_usd(row["cost_usd_per_1m_output_tokens"]),
                err=row["errors"],
                req=row["requests"],
            )
        )
    lines += [
        "",
        "## 시나리오 설명",
        "",
        *(f"- `{name}`: {desc}" for name, desc in SCENARIO_DESCRIPTIONS.items()),
        "",
        "## 지표 정의",
        "",
        "- TTFT: 요청 전송부터 첫 생성 토큰(추론 토큰 포함) 수신까지 걸린 시간. 하드웨어 prefill 지연 비교용.",
        "- 첫 답변: 요청 전송부터 첫 답변(content) 토큰까지 걸린 시간. 사용자가 체감하는 지연이며 thinking 모델은 TTFT보다 길다.",
        "- `†`: 최대 출력 토큰 안에 답변 없이 추론만 생성한 요청이 있다. `--max-tokens`를 늘리거나 thinking을 끄고 다시 측정한다.",
        "- 생성 tok/s: 첫 토큰 이후 생성 속도 `(출력 토큰 - 1) / (전체 시간 - TTFT)`. 요청 하나 기준.",
        "- 처리량 tok/s: 배치 전체 출력 토큰 / 배치 wall time. 동시성을 올리면 하드웨어의 batching 효율이 드러난다.",
        "- 비용: API는 `입력·출력 토큰 × 1M 토큰 단가`, RNGD/GPU는 `시간당 단가 × 배치 wall time`으로 계산한다. 단가가 비어 있으면 `-`.",
        "- `*`: 서버가 usage를 주지 않아 스트리밍 chunk 수로 토큰 수를 추정한 값.",
        "",
    ]
    return "\n".join(lines)


def _seconds(value: float | None) -> str:
    return "-" if value is None else f"{value:.3f}s"


def _number(value: float | None) -> str:
    return "-" if value is None else f"{value:.1f}"


def _usd(value: float | None) -> str:
    return "-" if value is None else f"${value:.4f}"
