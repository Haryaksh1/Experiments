from pathlib import Path

import yaml
from pydantic import BaseModel


class Config(BaseModel):
    model: str = "phi3:mini"
    host: str = "http://127.0.0.1:11434"
    temperature: float = 0.7
    judge_temperature: float = 0.1
    num_ctx: int = 4096
    max_tokens: int = 512
    seed: int = 0
    num_thread: int = 4
    keep_alive: str = "5m"
    max_retries: int = 2
    budget_margin: float = 0.10
    chars_per_token: float = 2.3


def load_config(path: str | None = None, **overrides) -> Config:
    """Load config.yaml (or an explicit path), then apply non-None overrides."""
    p = Path(path or "config.yaml")
    data = {}
    if path or p.exists():  # an explicit path must exist; the default one is optional
        data = yaml.safe_load(p.read_text()) or {}
    data.update({k: v for k, v in overrides.items() if v is not None})
    return Config(**data)
