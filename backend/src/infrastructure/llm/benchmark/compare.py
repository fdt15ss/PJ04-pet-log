from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

# 모든 실행에서 같아야 공정한 비교가 되는 측정 조건
CONDITION_KEYS = ("warmup", "max_tokens")
# 동시성마다 요청 수를 다르게 잡을 수 있으므로, 같은 동시성끼리만 같아야 하는 조건
PER_CONCURRENCY_CONDITION_KEYS = ("runs",)

OVERVIEW_METRICS = (
    "ttft_p50_s",
    "ttft_content_p50_s",
    "decode_tokens_per_s_p50",
    "throughput_tokens_per_s",
    "cost_usd_per_1k_requests",
)


def find_run_dirs(results_root: Path) -> list[Path]:
    return sorted(path.parent for path in results_root.glob("*/results.json"))


def load_run(run_dir: Path) -> dict[str, Any]:
    """benchmark_llm_backends.py 결과 폴더 하나를 읽는다. environment.json은 있으면 같이 읽는다."""
    results = json.loads((run_dir / "results.json").read_text(encoding="utf-8"))
    environment_path = run_dir / "environment.json"
    environment = (
        json.loads(environment_path.read_text(encoding="utf-8")) if environment_path.exists() else {}
    )
    return {
        "run": run_dir.name,
        "meta": results.get("meta", {}),
        "environment": environment,
        "summaries": results.get("summaries", []),
    }


def comparison_rows(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        {"run": run["run"], "machine": run["environment"].get("machine"), **summary}
        for run in runs
        for summary in run["summaries"]
    ]
    return sorted(rows, key=lambda row: (row["concurrency"], row["scenario"], row["backend"], row["run"]))


def condition_warnings(runs: list[dict[str, Any]]) -> list[str]:
    warnings = [_mismatch(key, runs, "실행마다") for key in CONDITION_KEYS]
    by_concurrency: dict[Any, list[dict[str, Any]]] = {}
    for run in runs:
        by_concurrency.setdefault(run["meta"].get("concurrency"), []).append(run)
    for concurrency, group in sorted(by_concurrency.items(), key=lambda item: str(item[0])):
        warnings += [_mismatch(key, group, f"동시성 {concurrency} 실행끼리") for key in PER_CONCURRENCY_CONDITION_KEYS]
    return [warning for warning in warnings if warning]


def _mismatch(key: str, runs: list[dict[str, Any]], scope: str) -> str | None:
    values = {run["run"]: run["meta"].get(key) for run in runs}
    if len(set(values.values())) <= 1:
        return None
    detail = ", ".join(f"{name}={value}" for name, value in values.items())
    return f"`{key}` 값이 {scope} 다릅니다: {detail}"


def overview_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """백엔드 × 동시성별로 시나리오 평균을 낸다. 포트폴리오 헤드라인 숫자용."""
    groups: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault((row["backend"], row["concurrency"]), []).append(row)

    overview = []
    for (backend, concurrency), members in sorted(groups.items(), key=lambda item: (item[0][1], item[0][0])):
        entry: dict[str, Any] = {
            "backend": backend,
            "model": members[0]["model"],
            "concurrency": concurrency,
            "scenarios": len({member["scenario"] for member in members}),
            "requests": sum(member["requests"] for member in members),
            "errors": sum(member["errors"] for member in members),
        }
        for metric in OVERVIEW_METRICS:
            values = [member[metric] for member in members if member.get(metric) is not None]
            entry[f"{metric}_mean"] = statistics.fmean(values) if values else None
        overview.append(entry)
    return overview


def add_baseline_ratios(rows: list[dict[str, Any]], baseline: str) -> None:
    """같은 시나리오·동시성의 baseline 백엔드 대비 배수를 rows에 채운다.

    처리량 배수 > 1 이면 baseline보다 빠르고, TTFT 배수 < 1 이면 baseline보다 첫 토큰이 빠르다.
    """
    base = {(r["scenario"], r["concurrency"]): r for r in rows if r["backend"] == baseline}
    for row in rows:
        reference = base.get((row["scenario"], row["concurrency"]))
        row["throughput_vs_baseline"] = _ratio(row.get("throughput_tokens_per_s"), reference, "throughput_tokens_per_s")
        row["ttft_vs_baseline"] = _ratio(row.get("ttft_p50_s"), reference, "ttft_p50_s")


def build_comparison(runs: list[dict[str, Any]], baseline: str | None = None) -> dict[str, Any]:
    rows = comparison_rows(runs)
    if baseline:
        add_baseline_ratios(rows, baseline)
    return {
        "baseline": baseline,
        "runs": [{key: run[key] for key in ("run", "meta", "environment")} for run in runs],
        "warnings": condition_warnings(runs),
        "overview": overview_rows(rows),
        "rows": rows,
    }


def render_comparison_markdown(comparison: dict[str, Any]) -> str:
    baseline = comparison["baseline"]
    lines = ["# LLM 백엔드 비교표", ""]

    if comparison["warnings"]:
        lines += ["> **측정 조건이 다릅니다.** 공정한 비교가 아닐 수 있습니다.", ">"]
        lines += [f"> - {warning}" for warning in comparison["warnings"]]
        lines.append("")

    lines += ["## 실행 환경", "", "| 실행 폴더 | 머신 | 하드웨어 | 런타임 | 양자화 | runs | warmup | 동시성 | max_tokens |", "|---|---|---|---|---|---:|---:|---:|---:|"]
    for run in comparison["runs"]:
        env, meta = run["environment"], run["meta"]
        lines.append(
            f"| `{run['run']}` | {env.get('machine', '-')} | {env.get('gpu') or env.get('accelerator') or '-'} "
            f"| {env.get('runtime', '-')} | {env.get('quantization', '-')} | {meta.get('runs', '-')} "
            f"| {meta.get('warmup', '-')} | {meta.get('concurrency', '-')} | {meta.get('max_tokens', '-')} |"
        )

    lines += [
        "",
        "## 전체 요약 (시나리오 평균)",
        "",
        "| 동시성 | 백엔드 | 모델 | TTFT p50 | 첫 답변 p50 | 생성 tok/s | 처리량 tok/s | 1K 요청 비용 | 오류 |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for entry in comparison["overview"]:
        lines.append(
            f"| {entry['concurrency']} | {entry['backend']} | `{entry['model']}` "
            f"| {_seconds(entry['ttft_p50_s_mean'])} | {_seconds(entry['ttft_content_p50_s_mean'])} "
            f"| {_number(entry['decode_tokens_per_s_p50_mean'])} | {_number(entry['throughput_tokens_per_s_mean'])} "
            f"| {_usd(entry['cost_usd_per_1k_requests_mean'])} | {entry['errors']}/{entry['requests']} |"
        )

    ratio_header = " | 처리량 배수 | TTFT 배수" if baseline else ""
    ratio_align = "|---:|---:" if baseline else ""
    lines += ["", "## 시나리오별 비교", ""]
    if baseline:
        lines += [f"배수 기준: `{baseline}` (처리량 배수 > 1 이면 더 빠름, TTFT 배수 < 1 이면 첫 토큰이 더 빠름)", ""]
    lines += [
        f"| 동시성 | 시나리오 | 백엔드 | 실행 폴더 | TTFT p50 | 첫 답변 p50 | 생성 tok/s | 처리량 tok/s | 1K 요청 비용 | 오류{ratio_header} |",
        f"|---:|---|---|---|---:|---:|---:|---:|---:|---:{ratio_align}|",
    ]
    for row in comparison["rows"]:
        ratios = (
            f" | {_times(row.get('throughput_vs_baseline'))} | {_times(row.get('ttft_vs_baseline'))}" if baseline else ""
        )
        lines.append(
            f"| {row['concurrency']} | {row['scenario']} | {row['backend']} | `{row['run']}` "
            f"| {_seconds(row['ttft_p50_s'])} | {_seconds(row.get('ttft_content_p50_s'))} "
            f"| {_number(row['decode_tokens_per_s_p50'])} | {_number(row['throughput_tokens_per_s'])} "
            f"| {_usd(row['cost_usd_per_1k_requests'])} | {row['errors']}/{row['requests']}{ratios} |"
        )
    lines.append("")
    return "\n".join(lines)


def _ratio(value: float | None, reference: dict[str, Any] | None, key: str) -> float | None:
    if value is None or reference is None or not reference.get(key):
        return None
    return value / reference[key]


def _seconds(value: float | None) -> str:
    return "-" if value is None else f"{value:.3f}s"


def _number(value: float | None) -> str:
    return "-" if value is None else f"{value:.1f}"


def _usd(value: float | None) -> str:
    return "-" if value is None else f"${value:.4f}"


def _times(value: float | None) -> str:
    return "-" if value is None else f"{value:.2f}x"
