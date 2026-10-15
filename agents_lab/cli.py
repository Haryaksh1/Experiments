import random
from datetime import datetime
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


EVALS = Path(__file__).resolve().parent / "evals"


@app.command()
def persona(persona_file: Path = EVALS / "persona" / "persona.yaml", day_file: Path = EVALS / "persona" / "day.yaml",
            questions_file: Path = EVALS / "persona" / "questions.yaml", reflect_threshold: int = 150,
            config: str = None):
    """Phase 2 persona mode: simulate one day, save the agent, then run the recall interview."""
    import yaml

    from agents_lab.simulation_single.agent import Day, GenerativeAgent, Persona, Question, recall_eval, run_day

    llm = _live("persona", config)
    day = Day.from_yaml(day_file)
    agent = GenerativeAgent(Persona.from_yaml(persona_file), llm, datetime.fromisoformat(day.date),
                            reflect_threshold=reflect_threshold)
    log = run_day(agent, day)
    agent.save(llm.run.dir / "agent.json")
    qs = [Question(**q) for q in yaml.safe_load(questions_file.read_text(encoding="utf-8"))]
    rows = pd.DataFrame(recall_eval(agent, qs))
    rec = rows[rows.source != "none"]
    body = "\n".join([
        "## Phase 2 persona run", "",
        f"- Memories: {len(agent.mem.memories)}, reflections: {agent.reflections} (threshold {reflect_threshold})",
        f"- Recall: {int(rec.passed.sum())} of {len(rec)} answers contain the expected detail; retrieval surfaced "
        f"the relevant memory for {int(rec.retrieved_relevant.sum())} of {len(rec)}",
        f"- Invented-memory probe passed (said it doesn't know): {bool(rows[rows.source == 'none'].passed.all())}",
        "", "### Day", "", md_table(pd.DataFrame(log)[["time", "planned", "action", "changes_plan"]]), "",
        "### Interview", "", md_table(rows), "",
        f"Interview this agent: `agents-lab interview {(llm.run.dir / 'agent.json').as_posix()}`", ""])
    typer.echo(llm.run.write_summary(body).read_text(encoding="utf-8"))


def _weights(s: str) -> tuple[float, float, float]:
    w = tuple(float(x) for x in s.split(","))
    if len(w) != 3:
        raise typer.BadParameter("weights are recency,importance,relevance e.g. 1,1,1")
    return w


@app.command()
def recall(agent_file: Path, weights: str = "1,1,1",
           questions_file: Path = EVALS / "persona" / "questions.yaml", config: str = None):
    """Re-run the recall interview on a saved persona with other retrieval weights (no re-simulation)."""
    import yaml

    from agents_lab.simulation_single.agent import GenerativeAgent, Question, recall_eval

    llm = _live("recall", config)
    agent = GenerativeAgent.load(agent_file, llm, weights=_weights(weights))
    qs = [Question(**q) for q in yaml.safe_load(questions_file.read_text(encoding="utf-8"))]
    rows = pd.DataFrame(recall_eval(agent, qs))
    rec = rows[rows.source != "none"]
    body = (f"## Recall with weights {weights} (recency, importance, relevance)\n\n- Recall: {int(rec.passed.sum())} "
            f"of {len(rec)}; retrieval surfaced the relevant memory for {int(rec.retrieved_relevant.sum())} of "
            f"{len(rec)}\n- Invented-memory probe passed: {bool(rows[rows.source == 'none'].passed.all())}\n\n"
            + md_table(rows) + "\n")
    typer.echo(llm.run.write_summary(body).read_text(encoding="utf-8"))


@app.command()
def interview(agent_file: Path, question: str = None, weights: str = "1,1,1", config: str = None):
    """Interview a saved persona. Without --question it asks interactively (empty line quits)."""
    from agents_lab.simulation_single.agent import GenerativeAgent

    llm = _live("interview", config)
    agent = GenerativeAgent.load(agent_file, llm, weights=_weights(weights))
    while True:
        q = question or typer.prompt("You", default="", show_default=False)
        if not q:
            break
        answer, _ = agent.interview(q)
        typer.echo(f"{agent.persona.name}: {answer}")
        if question:
            break
    llm.run.write_summary()


@app.command()
def silicon(dta: Path = typer.Option(None, help="GSS Stata file (enables calibration)"),
            personas_csv: Path = typer.Option(None, help="CSV of attributes or a backstory column, plus id"),
            instrument: Path = EVALS / "survey" / "instrument.yaml", n: int = 40, big_n: int = typer.Option(100, "--N"),
            config: str = None):
    """Phase 2 silicon-sample mode: independent personas answer a survey; with --dta, PPI++ calibration."""
    from agents_lab.simulation_single.calibrate import calibrate
    from agents_lab.simulation_single.silicon import Instrument, prepare_gss, run_survey

    ins = Instrument.from_yaml(instrument)
    llm = _live("silicon", config)
    if dta:
        personas, real, labeled = prepare_gss(dta, ins, n, big_n, seed=llm.cfg.seed)
        real.to_csv(llm.run.dir / "real.csv", index=False)
    elif personas_csv:
        personas, real = pd.read_csv(personas_csv), None
    else:
        raise typer.BadParameter("give --dta or --personas-csv")
    personas.to_csv(llm.run.dir / "personas.csv", index=False)
    sim = run_survey(personas, ins, llm)
    sim.to_csv(llm.run.dir / "simulated.csv", index=False)
    body = f"## Silicon sample\n\n- Personas: {len(personas)}, failed: {int(sim.iloc[:, 1:].isna().all(axis=1).sum())}\n"
    if real is not None:
        est, spread = calibrate(real, sim, labeled, [it.id for it in ins.items])
        est.to_csv(llm.run.dir / "ppi.csv", index=False)
        spread.to_csv(llm.run.dir / "spread.csv", index=False)
        body += ("\n### PPI++ per item (n labeled, N simulated-only; truth = real answers of all n+N)\n\n"
                 + md_table(est.round(3)) + "\n\n### Spread by party (sd_ratio < 1 = flattening)\n\n"
                 + md_table(spread.round(3)) + "\n")
    typer.echo(llm.run.write_summary(body).read_text(encoding="utf-8"))


if __name__ == "__main__":
    app()
