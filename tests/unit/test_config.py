import pytest

from dossier.common.config import Settings


def test_defaults() -> None:
    s = Settings(_env_file=None)
    assert s.model_triage == "claude-haiku-5-5"
    assert s.max_tool_calls == 25


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOSSIER_MAX_TOOL_CALLS", "5")
    assert Settings(_env_file=None).max_tool_calls == 5


def test_secret_is_masked() -> None:
    s = Settings(_env_file=None, anthropic_api_key="sk-test")
    assert "sk-test" not in repr(s)


def test_invalid_limit_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DOSSIER_MAX_TOOL_CALLS", "0")
    with pytest.raises(ValueError):
        Settings(_env_file=None)