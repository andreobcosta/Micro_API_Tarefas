"""Testes da configuração por variáveis de ambiente (RNF06)."""

import pytest

from app.core.config import Settings, SettingsError


def test_defaults_when_environment_is_empty() -> None:
    settings = Settings.from_env({})

    assert settings.database_url == "sqlite:///./tasks.db"
    assert settings.app_env == "development"
    assert settings.log_level == "INFO"


def test_reads_values_from_the_environment() -> None:
    settings = Settings.from_env(
        {"DATABASE_URL": "sqlite://", "APP_ENV": "test", "LOG_LEVEL": "debug"}
    )

    assert settings.database_url == "sqlite://"
    assert settings.app_env == "test"
    assert settings.log_level == "DEBUG"


def test_blank_values_fall_back_to_defaults() -> None:
    settings = Settings.from_env({"DATABASE_URL": "  ", "LOG_LEVEL": ""})

    assert settings.database_url == "sqlite:///./tasks.db"
    assert settings.log_level == "INFO"


def test_invalid_log_level_raises_message_in_portuguese() -> None:
    with pytest.raises(SettingsError) as error:
        Settings.from_env({"LOG_LEVEL": "BARULHENTO"})

    assert "LOG_LEVEL" in str(error.value)
    assert "inválido" in str(error.value)


def test_settings_are_immutable() -> None:
    settings = Settings.from_env({})

    with pytest.raises(AttributeError):
        settings.app_env = "outro"  # type: ignore[misc]
