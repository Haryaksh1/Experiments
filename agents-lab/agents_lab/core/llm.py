"""LLM wrapper: schema-constrained JSON, validation + repair retries, budget check, tracing.

Backends return a dict: content, prompt_tokens, completion_tokens, done_reason (+ optional timings).
"""
import math
import time
from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from agents_lab.core.config import Config
from agents_lab.core.trace import Run

T = TypeVar("T", bound=BaseModel)
MSG_OVERHEAD = 8  # chat-template tokens per message (phi3 role markers)


class BudgetExceeded(RuntimeError):
    """Prompt would not fit num_ctx; the caller must summarize older content first."""


class LLMFailed(RuntimeError):
    """No valid response after max_retries repair attempts."""


class OllamaBackend:
    def __init__(self, cfg: Config):
        import ollama

        self.cfg, self.client = cfg, ollama.Client(host=cfg.host)

    def chat(self, messages: list[dict], fmt: dict | None, options: dict) -> dict:
        import httpx
        import ollama

        for i in range(self.cfg.max_retries + 1):  # transport retries (server busy / restarting)
            try:
                r = self.client.chat(model=self.cfg.model, messages=messages, format=fmt,
                                     options=options, keep_alive=self.cfg.keep_alive)
                break
            except (ollama.ResponseError, httpx.HTTPError, ConnectionError):
                if i == self.cfg.max_retries:
                    raise
                time.sleep(2 * (i + 1))
        return {"content": r.message.content, "prompt_tokens": r.prompt_eval_count or 0,
                "completion_tokens": r.eval_count or 0, "done_reason": r.done_reason,
                "prompt_eval_s": (r.prompt_eval_duration or 0) / 1e9, "eval_s": (r.eval_duration or 0) / 1e9,
                "load_s": (r.load_duration or 0) / 1e9}

    def info(self) -> dict:
        import httpx

        try:
            version = httpx.get(f"{self.cfg.host}/api/version", timeout=5).json().get("version")
            digest = next((m.digest for m in self.client.list().models if m.model == self.cfg.model), None)
        except Exception as e:  # server down: report it in the trace, fail later on the first call
            return {"backend": "ollama", "error": str(e)}
        return {"backend": "ollama", "ollama_version": version, "model": self.cfg.model, "model_digest": digest}


class MockBackend:
    """Deterministic offline backend.

    `script` is either a list of raw outputs (consumed in order) or a function
    (messages, schema_title) -> raw output.
    """

    def __init__(self, script: list[str] | Callable[[list[dict], str | None], str]):
        self.script, self.calls = script, []

    def chat(self, messages, fmt, options):
        title = (fmt or {}).get("title")
        self.calls.append({"messages": messages, "schema": title, "options": options})
        out = self.script.pop(0) if isinstance(self.script, list) else self.script(messages, title)
        return {"content": out, "prompt_tokens": sum(len(m["content"]) for m in messages) // 4,
                "completion_tokens": len(out) // 4, "done_reason": "stop"}

    def info(self):
        return {"backend": "mock"}


def _fmt_error(e: ValidationError) -> str:
    errs = e.errors(include_url=False)
    parts = [f"{'.'.join(map(str, x['loc'])) or 'root'}: {x['msg']}" for x in errs[:5]]
    if len(errs) > 5:
        parts.append(f"(+{len(errs) - 5} more errors)")
    return "; ".join(parts)


class LLM:
    def __init__(self, backend, cfg: Config, run: Run):
        self.backend, self.cfg, self.run = backend, cfg, run
        run.log("backend", **backend.info())

    def estimate_tokens(self, *texts: str) -> int:
        return sum(math.ceil(len(t) / self.cfg.chars_per_token) + MSG_OVERHEAD for t in texts)

    def prompt_budget(self, max_tokens: int | None = None) -> int:
        return int((self.cfg.num_ctx - (max_tokens or self.cfg.max_tokens)) * (1 - self.cfg.budget_margin))

    def fits(self, system: str, user: str, max_tokens: int | None = None) -> bool:
        return self.estimate_tokens(system, user) <= self.prompt_budget(max_tokens)

    def structured(self, system: str, user: str, schema: type[T], *, tag: str, judge: bool = False,
                   max_tokens: int | None = None, seed: int | None = None) -> T:
        """One schema-constrained call. Validates; on failure re-asks with the error (new seed each retry)."""
        max_tokens = max_tokens or self.cfg.max_tokens
        base_seed = self.cfg.seed if seed is None else seed
        temperature = self.cfg.judge_temperature if judge else self.cfg.temperature
        fmt, prompt = schema.model_json_schema(), user
        for attempt in range(self.cfg.max_retries + 1):
            est, budget = self.estimate_tokens(system, prompt), self.prompt_budget(max_tokens)
            if est > budget:
                self.run.log("budget_exceeded", tag=tag, est_tokens=est, budget=budget)
                raise BudgetExceeded(f"{tag}: ~{est} prompt tokens > budget {budget}")
            options = {"temperature": temperature, "num_ctx": self.cfg.num_ctx, "num_predict": max_tokens,
                       "seed": base_seed + attempt, "num_thread": self.cfg.num_thread}
            t0 = time.perf_counter()
            r = self.backend.chat([{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                                  fmt, options)
            latency = time.perf_counter() - t0
            try:
                obj, err = schema.model_validate_json(r["content"]), None
            except ValidationError as e:
                obj, err = None, _fmt_error(e)
                if r.get("done_reason") == "length":
                    err += " (output hit max_tokens: be more concise)"
            self.run.log("llm_call", tag=tag, attempt=attempt, schema=schema.__name__, system=system, user=prompt,
                         output=r["content"], ok=err is None, error=err, est_tokens=est,
                         **{k: v for k, v in r.items() if k != "content"},
                         latency_s=round(latency, 3), options=options)
            if err is None:
                return obj
            prompt = f"{user}\n\nYour previous reply was invalid: {err}\nReply again with corrected JSON only."
        self.run.log("llm_failed", tag=tag, error=err)
        raise LLMFailed(f"{tag}: invalid output after {self.cfg.max_retries} retries: {err}")
