"""Configuração da aplicação, lida de variáveis de ambiente (RNF06)."""

import os
from collections.abc import Mapping
from dataclasses import dataclass

from app.core import messages

DEFAULT_DATABASE_URL = "sqlite:///./tasks.db"
DEFAULT_APP_ENV = "development"
DEFAULT_LOG_LEVEL = "INFO"
LOG_LEVELS = ("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG")


class SettingsError(ValueError):
    """Configuração do ambiente inválida."""


@dataclass(frozen=True)
class Settings:
    """Configuração imutável da aplicação.

    Attributes:
        database_url: URL do banco (`DATABASE_URL`).
        app_env: Nome do ambiente (`APP_ENV`).
        log_level: Nível de log em maiúsculas (`LOG_LEVEL`).
    """

    database_url: str = DEFAULT_DATABASE_URL
    app_env: str = DEFAULT_APP_ENV
    log_level: str = DEFAULT_LOG_LEVEL

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "Settings":
        """Lê a configuração das variáveis de ambiente.

        Args:
            environ: Mapa de variáveis; usa `os.environ` quando omitido.

        Raises:
            SettingsError: Se `LOG_LEVEL` não for um nível conhecido.
        """
        env = os.environ if environ is None else environ
        log_level = _read(env, "LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
        if log_level not in LOG_LEVELS:
            raise SettingsError(
                messages.CONFIG_INVALID_LOG_LEVEL.format(
                    value=log_level, allowed=", ".join(LOG_LEVELS)
                )
            )
        return cls(
            database_url=_read(env, "DATABASE_URL", DEFAULT_DATABASE_URL),
            app_env=_read(env, "APP_ENV", DEFAULT_APP_ENV),
            log_level=log_level,
        )


def _read(env: Mapping[str, str], name: str, default: str) -> str:
    """Lê uma variável; vazia ou só com espaços vale como ausente."""
    return env.get(name, "").strip() or default
