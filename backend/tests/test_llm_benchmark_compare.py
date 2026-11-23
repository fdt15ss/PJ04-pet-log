import json
import tempfile
import unittest
from pathlib import Path

from infrastructure.llm.benchmark.compare import (
    build_comparison,
    find_run_dirs,
    load_run,
    render_comparison_markdown,
)


def _summary(backend, scenario, concurrency, ttft, throughput, errors=0):
    return {
        "backend": backend,
        "kind": "npu" if backend.startswith("rngd") else "gpu",
        "model": "qwen3-8b",
        "scenario": scenario,
        "concurrency": concurrency,
        "requests": 10,
        "errors": errors,
        "ttft_p50_s": ttft,
        "ttft_p95_s": ttft,
        "ttft_content_p50_s": ttft,
        "no_content_requests": 0,
        "e2e_p50_s": 1.0,
        "decode_tokens_per_s_p50": throughput,
        "throughput_tokens_per_s": throughput,
        "output_tokens_mean": 80,
        "tokens_estimated": False,
        "cost_usd_per_1k_requests": None,
        "cost_usd_per_1m_output_tokens": None,
    }


def _write_run(root: Path, name: str, summaries, meta=None, environment=None) -> Path:
    run_dir = root / name
    run_dir.mkdir(parents=True)
    meta = meta or {"runs": 10, "warmup": 1, "max_tokens": 256, "concurrency": summaries[0]["concurrency"]}
    (run_dir / "results.json").write_text(json.dumps({"meta": meta, "summaries": summaries}), encoding="utf-8")
    if environment is not None:
        (run_dir / "environment.json").write_text(json.dumps(environment), encoding="utf-8")
    return run_dir


class TestBenchmarkCompare(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_finds_and_loads_runs_with_optional_environment(self):
        _write_run(self.root, "b-home", [_summary("home", "pet_chat", 1, 0.05, 50)], environment={"machine": "home-pc"})
        _write_run(self.root, "a-rngd", [_summary("rngd", "pet_chat", 1, 0.02, 100)])
        (self.root / "not-a-run").mkdir()

        run_dirs = find_run_dirs(self.root)

        self.assertEqual(["a-rngd", "b-home"], [path.name for path in run_dirs])
        self.assertEqual({}, load_run(run_dirs[0])["environment"])
        self.assertEqual("home-pc", load_run(run_dirs[1])["environment"]["machine"])

    def test_baseline_ratios_match_same_scenario_and_concurrency(self):
        runs = [
            load_run(_write_run(self.root, "home-c1", [_summary("home", "pet_chat", 1, 0.05, 50)])),
            load_run(_write_run(self.root, "rngd-c1", [_summary("rngd", "pet_chat", 1, 0.02, 100)])),
            load_run(_write_run(self.root, "rngd-c4", [_summary("rngd", "pet_chat", 4, 0.03, 300)])),
        ]

        comparison = build_comparison(runs, baseline="home")
        rows = {(row["backend"], row["concurrency"]): row for row in comparison["rows"]}

        self.assertAlmostEqual(2.0, rows[("rngd", 1)]["throughput_vs_baseline"])
        self.assertAlmostEqual(0.4, rows[("rngd", 1)]["ttft_vs_baseline"])
        self.assertAlmostEqual(1.0, rows[("home", 1)]["throughput_vs_baseline"])
        # 집 PC에 동시성 4 결과가 없으므로 배수를 계산하지 않는다.
        self.assertIsNone(rows[("rngd", 4)]["throughput_vs_baseline"])

    def test_overview_averages_scenarios_per_backend_and_concurrency(self):
        run = load_run(
            _write_run(
                self.root,
                "rngd-c1",
                [_summary("rngd", "pet_chat", 1, 0.02, 100), _summary("rngd", "care_question", 1, 0.04, 80, errors=1)],
            )
        )

        overview = build_comparison([run])["overview"]

        self.assertEqual(1, len(overview))
        self.assertAlmostEqual(0.03, overview[0]["ttft_p50_s_mean"])
        self.assertAlmostEqual(90, overview[0]["throughput_tokens_per_s_mean"])
        self.assertEqual(1, overview[0]["errors"])
        self.assertEqual(20, overview[0]["requests"])
        self.assertIsNone(overview[0]["cost_usd_per_1k_requests_mean"])

    def test_warns_when_measurement_conditions_differ(self):
        runs = [
            load_run(_write_run(self.root, "a", [_summary("home", "pet_chat", 1, 0.05, 50)], meta={"runs": 10, "warmup": 1, "max_tokens": 256})),
            load_run(_write_run(self.root, "b", [_summary("rngd", "pet_chat", 1, 0.02, 100)], meta={"runs": 10, "warmup": 1, "max_tokens": 512})),
        ]

        comparison = build_comparison(runs)

        self.assertEqual(1, len(comparison["warnings"]))
        self.assertIn("max_tokens", comparison["warnings"][0])
        self.assertIn("측정 조건이 다릅니다", render_comparison_markdown(comparison))

    def test_runs_only_need_to_match_within_same_concurrency(self):
        c1 = {"runs": 10, "warmup": 1, "max_tokens": 256, "concurrency": 1}
        c4 = {"runs": 16, "warmup": 1, "max_tokens": 256, "concurrency": 4}
        runs = [
            load_run(_write_run(self.root, "home-c1", [_summary("home", "pet_chat", 1, 0.05, 50)], meta=c1)),
            load_run(_write_run(self.root, "home-c4", [_summary("home", "pet_chat", 4, 4.0, 50)], meta=c4)),
        ]
        self.assertEqual([], build_comparison(runs)["warnings"])

        runs.append(
            load_run(_write_run(self.root, "rngd-c4", [_summary("rngd", "pet_chat", 4, 0.1, 200)], meta={**c4, "runs": 8}))
        )
        warnings = build_comparison(runs)["warnings"]
        self.assertEqual(1, len(warnings))
        self.assertIn("동시성 4", warnings[0])

    def test_markdown_includes_ratio_columns_only_with_baseline(self):
        runs = [load_run(_write_run(self.root, "home-c1", [_summary("home", "pet_chat", 1, 0.05, 50)]))]

        self.assertNotIn("처리량 배수", render_comparison_markdown(build_comparison(runs)))
        self.assertIn("처리량 배수", render_comparison_markdown(build_comparison(runs, baseline="home")))


if __name__ == "__main__":
    unittest.main()
