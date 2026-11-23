from __future__ import annotations

import os
import statistics
import time
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BackendTarget:
    """OpenAI 호환 엔드포인트 하나. RNGD(furiosa-llm), GPU(vLLM/Ollama), API 모두 같은 형태로 다룬다."""

    name: str
    kind: str
    base_url: str
    model: str
    api_key_env: str | None = None
    # 하드웨어(RNGD/GPU): 시간당 비용. API: 1M 토큰당 비용.
    usd_per_hour: float | None = None
    input_usd_per_1m: float | None = None
    output_usd_per_1m: float | None = None
    max_tokens_param: str = "max_tokens"
    stream_usage: bool = True
    temperature: float | None = None
    extra_body: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BackendTarget:
        known = {f for f in cls.__dataclass_fields__}
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"backend `{data.get('name')}`에 알 수 없는 설정: {sorted(unknown)}")
        return cls(**data)

    def api_key(self) -> str:
        if self.api_key_env:
            return os.environ.get(self.api_key_env, "")
        return "not-needed"


@dataclass(frozen=True)
class RequestResult:
    backend: str
    scenario: str
    # 첫 생성 토큰(추론 토큰 포함)까지 시간. 하드웨어 prefill 지연 비교용.
    ttft_s: float | None
    e2e_s: float
    input_tokens: int | None
    output_tokens: int
    tokens_estimated: bool
    error: str | None = None
    output_preview: str = ""
    # 첫 답변(content) 토큰까지 시간. 사용자가 체감하는 지연. thinking 모델은 ttft_s보다 길다.
    ttft_content_s: float | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    @property
    def decode_tokens_per_s(self) -> float | None:
        """첫 토큰 이후 생성 속도. (output_tokens - 1) / (e2e - ttft)."""
        if self.ttft_s is None or self.output_tokens < 2:
            return None
        decode_s = self.e2e_s - self.ttft_s
        if decode_s <= 0:
            return None
        return (self.output_tokens - 1) / decode_s


@dataclass(frozen=True)
class BatchResult:
    backend: str
    scenario: str
    concurrency: int
    wall_s: float
    requests: tuple[RequestResult, ...]


def measure_stream(
    client: Any,
    target: BackendTarget,
    scenario: str,
    messages: Sequence[dict[str, str]],
    max_tokens: int,
    clock: Callable[[], float] = time.perf_counter,
) -> RequestResult:
    """스트리밍 요청 하나를 보내고 첫 content 토큰까지 시간과 전체 시간을 잰다."""
    kwargs: dict[str, Any] = {
        "model": target.model,
        "messages": list(messages),
        "stream": True,
        target.max_tokens_param: max_tokens,
    }
    if target.stream_usage:
        kwargs["stream_options"] = {"include_usage": True}
    if target.temperature is not None:
        kwargs["temperature"] = target.temperature
    if target.extra_body:
        kwargs["extra_body"] = target.extra_body

    started = clock()
    first_token_at: float | None = None
    first_content_at: float | None = None
    token_chunks = 0
    parts: list[str] = []
    usage = None
    try:
        for chunk in client.chat.completions.create(**kwargs):
            if getattr(chunk, "usage", None):
                usage = chunk.usage
            for choice in getattr(chunk, "choices", None) or ():
                text = getattr(choice.delta, "content", None)
                # Ollama는 `reasoning`, vLLM 계열은 `reasoning_content`로 추론 토큰을 보낸다.
                reasoning = getattr(choice.delta, "reasoning", None) or getattr(
                    choice.delta, "reasoning_content", None
                )
                if not text and not reasoning:
                    continue
                now = clock()
                if first_token_at is None:
                    first_token_at = now
                if text and first_content_at is None:
                    first_content_at = now
                token_chunks += 1
                if text:
                    parts.append(text)
    except Exception as error:  # 백엔드별 오류를 결과에 남기고 다음 요청을 계속한다.
        return RequestResult(
            backend=target.name,
            scenario=scenario,
            ttft_s=None,
            e2e_s=clock() - started,
            input_tokens=None,
            output_tokens=0,
            tokens_estimated=True,
            error=f"{type(error).__name__}: {error}",
        )
    finished = clock()

    output_tokens = getattr(usage, "completion_tokens", None) if usage else None
    return RequestResult(
        backend=target.name,
        scenario=scenario,
        ttft_s=None if first_token_at is None else first_token_at - started,
        e2e_s=finished - started,
        input_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
        output_tokens=output_tokens if output_tokens is not None else token_chunks,
        tokens_estimated=output_tokens is None,
        error=None if first_token_at is not None else "EmptyResponse: 생성된 토큰이 없습니다.",
        output_preview="".join(parts)[:120],
        ttft_content_s=None if first_content_at is None else first_content_at - started,
    )


def run_batch(
    client: Any,
    target: BackendTarget,
    scenario: str,
    messages: Sequence[dict[str, str]],
    *,
    runs: int,
    concurrency: int,
    max_tokens: int,
    clock: Callable[[], float] = time.perf_counter,
) -> BatchResult:
    """같은 요청을 runs번, 최대 concurrency개씩 동시에 보낸다. wall_s는 처리량·하드웨어 비용 계산에 쓴다."""

    def one(_: int) -> RequestResult:
        return measure_stream(client, target, scenario, messages, max_tokens, clock)

    started = clock()
    if concurrency <= 1:
        results = [one(i) for i in range(runs)]
    else:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            results = list(pool.map(one, range(runs)))
    return BatchResult(
        backend=target.name,
        scenario=scenario,
        concurrency=concurrency,
        wall_s=clock() - started,
        requests=tuple(results),
    )


def summarize_batch(batch: BatchResult, target: BackendTarget) -> dict[str, Any]:
    ok = [r for r in batch.requests if r.ok]
    ttfts = [r.ttft_s for r in ok if r.ttft_s is not None]
    decode_tps = [v for r in ok if (v := r.decode_tokens_per_s) is not None]
    total_output = sum(r.output_tokens for r in ok)
    cost = _batch_cost_usd(batch, ok, target)

    return {
        "backend": batch.backend,
        "kind": target.kind,
        "model": target.model,
        "scenario": batch.scenario,
        "concurrency": batch.concurrency,
        "requests": len(batch.requests),
        "errors": len(batch.requests) - len(ok),
        "ttft_p50_s": _percentile(ttfts, 50),
        "ttft_p95_s": _percentile(ttfts, 95),
        "ttft_content_p50_s": _percentile([r.ttft_content_s for r in ok if r.ttft_content_s is not None], 50),
        "no_content_requests": sum(1 for r in ok if r.ttft_content_s is None),
        "e2e_p50_s": _percentile([r.e2e_s for r in ok], 50),
        "decode_tokens_per_s_p50": _percentile(decode_tps, 50),
        "throughput_tokens_per_s": total_output / batch.wall_s if ok and batch.wall_s > 0 else None,
        "output_tokens_mean": statistics.fmean(r.output_tokens for r in ok) if ok else None,
        "tokens_estimated": any(r.tokens_estimated for r in ok),
        "cost_usd_per_1k_requests": cost / len(ok) * 1000 if cost is not None and ok else None,
        "cost_usd_per_1m_output_tokens": cost / total_output * 1_000_000 if cost is not None and total_output else None,
    }


def _batch_cost_usd(batch: BatchResult, ok: list[RequestResult], target: BackendTarget) -> float | None:
    if target.usd_per_hour is not None:
        # 하드웨어는 사용량과 무관하게 시간 단위로 과금된다고 보고, 이 배치를 처리한 시간만큼 비용을 매긴다.
        return target.usd_per_hour * batch.wall_s / 3600
    if target.input_usd_per_1m is None or target.output_usd_per_1m is None:
        return None
    if any(r.input_tokens is None for r in ok):
        return None
    input_tokens = sum(r.input_tokens or 0 for r in ok)
    output_tokens = sum(r.output_tokens for r in ok)
    return (input_tokens * target.input_usd_per_1m + output_tokens * target.output_usd_per_1m) / 1_000_000


def _percentile(values: Sequence[float], pct: int) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    return statistics.quantiles(values, n=100, method="inclusive")[pct - 1]
