import pytest

from agents_lab.core.config import Config
from agents_lab.core.llm import LLM, MockBackend
from agents_lab.core.trace import Run


def pytest_addoption(parser):
    parser.addoption("--live", action="store_true", help="run tests that call the local Ollama server")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--live"):
        skip = pytest.mark.skip(reason="live test: pass --live")
        for item in items:
            if "live" in item.keywords:
                item.add_marker(skip)


def pytest_configure(config):
    config.addinivalue_line("markers", "live: needs a running Ollama server")


@pytest.fixture
def cfg():
    return Config()


@pytest.fixture
def make_llm(cfg, tmp_path):
    def _make(script, **overrides):
        c = cfg.model_copy(update=overrides)
        backend = MockBackend(script)
        return LLM(backend, c, Run("test", c, root=tmp_path)), backend
    return _make
