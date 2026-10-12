import pytest


@pytest.fixture(autouse=True)
def _isolate_cairn(tmp_path, monkeypatch):
    """Keep sensor output and ledger writes out of the project during tests."""
    monkeypatch.setenv("CAIRN_CHECKS", str(tmp_path / "checks.jsonl"))
    monkeypatch.setenv("CAIRN_LEDGER", str(tmp_path / "numbers.json"))
