import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

from agents_lab.core.config import Config


def git_hash() -> str:
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
        return h + ("-dirty" if dirty else "")
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "no-commit"


def md_table(df: pd.DataFrame) -> str:
    cols = [str(c) for c in df.columns]
    rows = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in df.itertuples(index=False):
        rows.append("| " + " | ".join(f"{v:.3g}" if isinstance(v, float) else str(v) for v in r) + " |")
    return "\n".join(rows)


class Run:
    """One run = runs/<timestamp>_<name>/ with trace.jsonl (every event) and summary.md."""

    def __init__(self, name: str, cfg: Config, root: str | Path = "runs"):
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.dir = Path(root) / f"{ts}_{name}"
        i = 1
        while self.dir.exists():
            i += 1
            self.dir = Path(root) / f"{ts}_{name}_{i}"
        self.dir.mkdir(parents=True)
        self.path = self.dir / "trace.jsonl"
        self.name, self.events, self.t0 = name, [], time.perf_counter()
        self.log("run_start", name=name, config=cfg.model_dump(), git=git_hash(), python=sys.version.split()[0])

    def log(self, event: str, **data) -> None:
        rec = {"ts": datetime.now().isoformat(timespec="milliseconds"), "event": event, **data}
        self.events.append(rec)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str, ensure_ascii=False) + "\n")

    def stats(self) -> pd.DataFrame:
        """Per tag: calls, attempts, failed attempts (parse failure rate), final failures, tokens, latency."""
        att = pd.DataFrame([e for e in self.events if e["event"] == "llm_call"])
        if att.empty:
            return pd.DataFrame()
        failed = pd.DataFrame([e for e in self.events if e["event"] == "llm_failed"], columns=["tag"])
        g = att.groupby("tag")
        out = pd.DataFrame({
            "calls": g["attempt"].apply(lambda a: int((a == 0).sum())),
            "attempts": g.size(),
            "failed_attempts": g["ok"].apply(lambda ok: int((~ok).sum())),
            "final_failures": failed["tag"].value_counts().reindex(g.size().index, fill_value=0),
            "prompt_tokens": g["prompt_tokens"].sum(),
            "completion_tokens": g["completion_tokens"].sum(),
            "latency_s": g["latency_s"].sum(),
        })
        out["parse_fail_rate"] = out["failed_attempts"] / out["attempts"]
        return out.reset_index()

    def write_summary(self, body: str = "") -> Path:
        s = self.stats()
        start = self.events[0]
        head = (f"# Run `{self.name}`\n\n- dir: `{self.dir.as_posix()}`\n- git: `{start['git']}`\n"
                f"- model: `{start['config']['model']}`\n- wall clock: {time.perf_counter() - self.t0:.1f} s\n")
        if not s.empty:
            head += (f"- LLM calls: {s['calls'].sum()}, attempts: {s['attempts'].sum()}, "
                     f"parse failure rate: {s['failed_attempts'].sum() / s['attempts'].sum():.1%}\n\n"
                     "## LLM calls by tag\n\n" + md_table(s) + "\n")
        p = self.dir / "summary.md"
        p.write_text(head + ("\n" + body if body else ""), encoding="utf-8")
        return p
