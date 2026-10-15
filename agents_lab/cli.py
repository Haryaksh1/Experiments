import random
from pathlib import Path

import pandas as pd
import typer
from pydantic import BaseModel, Field

from agents_lab.core.config import load_config
from agents_lab.core.llm import LLM, OllamaBackend
from agents_lab.core.trace import Run, md_table
from agents_lab.decision_single.agent import DecisionAgent
from agents_lab.decision_single.evaluate import evaluate, load_scenarios, report
from agents_lab.decision_single.schemas import Problem

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.callback()
def main():
    """agents_lab: offline agent systems on phi3:mini via Ollama."""


class BenchItem(BaseModel):
    name: str = Field(max_length=40)
    score: int = Field(ge=0, le=10)
    reason: str = Field(max_length=120)


class BenchOut(BaseModel):
    items: list[BenchItem] = Field(min_length=3, max_length=3)


@app.command()
def bench(calls: int = 3, long_facts: int = 120, threads: int = None, config: str = None):
    """Check the model answers schema-constrained JSON and measure speed (short and long prompts)."""
    cfg = load_config(config, num_thread=threads)
    run = Run("bench", cfg)
    backend = OllamaBackend(cfg)
    info = backend.info()
    if not info.get("model_digest"):
        typer.echo(f"Model {cfg.model!r} not available: {info}. Run `ollama pull {cfg.model}`.")
        raise typer.Exit(1)
    llm = LLM(backend, cfg, run)
    system = "You rate options. Return exactly three items with a 0-10 score and a one-line reason."
    for i in range(calls):
        rng = random.Random(i)  # new first line each call so the KV cache cannot reuse the prompt
        facts = "\n".join(f"Fact {j}: option {'ABC'[j % 3]} costs {rng.randint(1, 99)} dollars." for j in range(long_facts))
        for kind, user in [("short", f"Run {i}. Options: A, B, C. Rate cost-effectiveness."),
                           ("long", f"Run {i}. Options: A, B, C.\n{facts}\nRate cost-effectiveness.")]:
            llm.structured(system, user, BenchOut, tag=f"bench_{kind}", judge=True, max_tokens=200)
    df = pd.DataFrame([e for e in run.events if e["event"] == "llm_call"])
    df["prompt_tok_s"] = df["prompt_tokens"] / df["prompt_eval_s"].where(df["prompt_eval_s"] > 0)
    df["gen_tok_s"] = df["completion_tokens"] / df["eval_s"].where(df["eval_s"] > 0)
    df["chars_per_token"] = (df["system"].str.len() + df["user"].str.len()) / df["prompt_tokens"]
    t = df.groupby("tag")[["prompt_tokens", "completion_tokens", "prompt_tok_s", "gen_tok_s", "latency_s",
                           "chars_per_token"]].mean().reset_index()
    body = (f"Ollama {info.get('ollama_version')}, digest `{info.get('model_digest')}`, num_thread={cfg.num_thread}\n\n"
            "## Means per prompt size\n\n" + md_table(t) + "\n")
    p = run.write_summary(body)
    typer.echo(p.read_text(encoding="utf-8"))


def _live(name: str, config: str | None, **overrides) -> LLM:
    cfg = load_config(config, **overrides)
    return LLM(OllamaBackend(cfg), cfg, Run(name, cfg))


@app.command()
def decide(problem: Path, seed: int = None, config: str = None):
    """Phase 1: run the single decision agent on one YAML problem."""
    p = Problem.from_yaml(problem)
    llm = _live(f"decide_{p.id}", config, seed=seed)
    r = DecisionAgent(llm).run(p)
    llm.run.log("decision_result", **r.to_dict())
    typer.echo(llm.run.write_summary(r.to_markdown()).read_text(encoding="utf-8"))


@app.command("eval-decision")
def eval_decision(stability: int = typer.Option(4, help="scenarios that get 3 seeds (10 = full eval)"),
                  limit: int = None, config: str = None):
    """Phase 1 eval over agents_lab/evals/decision."""
    llm = _live("eval_decision", config)
    df = evaluate(load_scenarios(limit=limit), llm, stability=stability)
    df.to_csv(llm.run.dir / "runs.csv", index=False)
    typer.echo(llm.run.write_summary(report(df, llm)).read_text(encoding="utf-8"))


if __name__ == "__main__":
    app()
