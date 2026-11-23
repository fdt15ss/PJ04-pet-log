"""RNGD / GPU / API LLM 백엔드를 Pet Log 실제 프롬프트로 비교한다.

예시:
    uv run python -B scripts/benchmark_llm_backends.py --config benchmarks/backends.toml --runs 10
    uv run python -B scripts/benchmark_llm_backends.py --dry-run
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT / "src"))

from infrastructure.database import connect  # noqa: E402
from infrastructure.llm.benchmark.measure import BackendTarget, run_batch, summarize_batch  # noqa: E402
from infrastructure.llm.benchmark.report import render_markdown, write_report  # noqa: E402
from infrastructure.llm.benchmark.scenarios import build_scenarios  # noqa: E402


def main() -> None:
    args = parse_args()
    load_dotenv(BACKEND_ROOT / ".env")

    connection = connect(args.database_path) if args.database_path else None
    scenarios = build_scenarios(connection)
    if args.scenarios:
        scenarios = {name: scenarios[name] for name in _split(args.scenarios)}

    if args.dry_run:
        for name, messages in scenarios.items():
            chars = sum(len(message["content"]) for message in messages)
            print(f"{name}: messages={len(messages)} chars={chars}")
        return

    targets = load_targets(args.config, args.backends)
    started_at = datetime.now()
    batches = []
    summaries = []
    for target in targets:
        client = OpenAI(base_url=target.base_url, api_key=target.api_key(), timeout=args.timeout, max_retries=0)
        for name, messages in scenarios.items():
            print(f"[{target.name}] {name}: warmup {args.warmup}, runs {args.runs}, concurrency {args.concurrency}")
            for _ in range(args.warmup):
                run_batch(client, target, name, messages, runs=1, concurrency=1, max_tokens=args.max_tokens)
            batch = run_batch(
                client,
                target,
                name,
                messages,
                runs=args.runs,
                concurrency=args.concurrency,
                max_tokens=args.max_tokens,
            )
            for request in batch.requests:
                if request.error:
                    print(f"  ! {request.error}")
            batches.append(batch)
            summaries.append(summarize_batch(batch, target))

    meta = {
        "started_at": started_at.isoformat(timespec="seconds"),
        "runs": args.runs,
        "warmup": args.warmup,
        "concurrency": args.concurrency,
        "max_tokens": args.max_tokens,
        "backends": [
            {"name": t.name, "kind": t.kind, "model": t.model, "base_url": t.base_url} for t in targets
        ],
    }
    folder = started_at.strftime("%Y%m%d-%H%M%S") + (f"-{args.label}" if args.label else "")
    output_dir = args.output_dir / folder
    write_report(output_dir, meta=meta, summaries=summaries, batches=batches)
    print()
    print(render_markdown(meta, summaries))
    print(f"결과 저장: {output_dir}")


def load_targets(config_path: Path, only: str | None) -> list[BackendTarget]:
    if not config_path.exists():
        raise SystemExit(
            f"{config_path} 가 없습니다. benchmarks/backends.example.toml 을 복사해 값을 채운 뒤 다시 실행하세요."
        )
    with config_path.open("rb") as file:
        config = tomllib.load(file)
    targets = [BackendTarget.from_dict(item) for item in config.get("backends", [])]
    if only:
        wanted = set(_split(only))
        targets = [target for target in targets if target.name in wanted]
    if not targets:
        raise SystemExit("측정할 backend가 없습니다. 설정 파일 또는 --backends 값을 확인하세요.")
    return targets


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pet Log LLM 백엔드 TTFT / tokens/s / 비용 비교")
    parser.add_argument("--config", type=Path, default=BACKEND_ROOT / "benchmarks" / "backends.toml")
    parser.add_argument("--backends", help="측정할 backend name 목록 (쉼표 구분). 생략하면 전체")
    parser.add_argument("--scenarios", help="측정할 시나리오 목록 (쉼표 구분). 생략하면 전체")
    parser.add_argument("--runs", type=int, default=5, help="시나리오당 측정 요청 수")
    parser.add_argument("--warmup", type=int, default=1, help="기록하지 않는 워밍업 요청 수")
    parser.add_argument("--concurrency", type=int, default=1, help="동시에 보낼 요청 수")
    parser.add_argument("--max-tokens", type=int, default=256)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--output-dir", type=Path, default=BACKEND_ROOT / "benchmarks" / "results")
    parser.add_argument("--label", help="결과 폴더 이름 뒤에 붙일 라벨 (예: rngd-vs-gpu)")
    parser.add_argument("--database-path", help="seed 대신 실제 SQLite DB로 프롬프트를 만들 때 경로")
    parser.add_argument("--dry-run", action="store_true", help="LLM 호출 없이 시나리오 프롬프트만 확인")
    return parser.parse_args()


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


if __name__ == "__main__":
    main()
