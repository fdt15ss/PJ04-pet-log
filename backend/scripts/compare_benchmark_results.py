"""여러 벤치마크 결과 폴더를 하나의 비교표로 합친다.

예시:
    # benchmarks/results 아래 모든 실행을 비교
    uv run python -B scripts/compare_benchmark_results.py --label rngd-vs-home

    # 특정 폴더만, 집 PC 대비 배수까지
    uv run python -B scripts/compare_benchmark_results.py \
        benchmarks/results/20261124-101500-rngd-qwen3-8b-c1 \
        benchmarks/results/20261123-221252-home-qwen3-8b-c1 \
        --baseline home-ollama-qwen3-8b --label c1
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT / "src"))

from infrastructure.llm.benchmark.compare import (  # noqa: E402
    build_comparison,
    find_run_dirs,
    load_run,
    render_comparison_markdown,
)


def main() -> None:
    args = parse_args()
    run_dirs = args.run_dirs or find_run_dirs(args.results_root)
    missing = [path for path in run_dirs if not (path / "results.json").exists()]
    if missing:
        raise SystemExit(f"results.json 이 없는 폴더: {', '.join(map(str, missing))}")
    if not run_dirs:
        raise SystemExit(f"{args.results_root} 아래에 비교할 결과가 없습니다.")

    comparison = build_comparison([load_run(path) for path in run_dirs], baseline=args.baseline)
    if args.baseline and not any(row["backend"] == args.baseline for row in comparison["rows"]):
        raise SystemExit(f"--baseline `{args.baseline}` 백엔드가 결과에 없습니다.")

    folder = datetime.now().strftime("%Y%m%d-%H%M%S") + (f"-{args.label}" if args.label else "")
    output_dir = args.output_dir / folder
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "compare.json").write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    markdown = render_comparison_markdown(comparison)
    (output_dir / "compare.md").write_text(markdown, encoding="utf-8")

    print(markdown)
    print(f"비교 결과 저장: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="벤치마크 결과 폴더들을 하나의 비교표로 합친다")
    parser.add_argument("run_dirs", nargs="*", type=Path, help="비교할 결과 폴더. 생략하면 --results-root 아래 전체")
    parser.add_argument("--results-root", type=Path, default=BACKEND_ROOT / "benchmarks" / "results")
    parser.add_argument("--output-dir", type=Path, default=BACKEND_ROOT / "benchmarks" / "comparisons")
    parser.add_argument("--baseline", help="배수 계산 기준 backend name (예: home-ollama-qwen3-8b)")
    parser.add_argument("--label", help="비교 폴더 이름 뒤에 붙일 라벨")
    return parser.parse_args()


if __name__ == "__main__":
    main()
