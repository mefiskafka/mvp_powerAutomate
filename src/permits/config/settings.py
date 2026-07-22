"""Carga y validación de configuración (config.yaml + .env).

Precedencia (de menor a mayor): valores por defecto -> config.yaml -> variables de
entorno (.env con prefijo ``PERMITS_`` y anidación ``__``). No hay rutas
hardcodeadas: todo se resuelve contra la raíz del proyecto vía ``pathlib``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Raíz del proyecto: .../src/permits/config/settings.py -> parents[3]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_YAML = PROJECT_ROOT / "config.yaml"


class AppConfig(BaseModel):
    name: str = "permits-rpa"
    environment: str = "local"


class PathsConfig(BaseModel):
    excel_file: str = "data/permisos.xlsx"
    output_dir: str = "sample_data/expected_output"
    logs_dir: str = "logs"
    templates_dir: str = "templates"


class ExcelConfig(BaseModel):
    sheet_name: str = "Permisos"
    headers: list[str] = Field(
        default_factory=lambda: [
            "Fecha proceso",
            "Folio",
            "Empresa",
            "Fecha Inicio",
            "Fecha Fin",
            "Vehículo",
            "Placas",
            "Cantidad Personas",
            "Estado",
            "Observaciones",
        ]
    )


class PdfConfig(BaseModel):
    renderer: str = "fpdf2"


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file_prefix: str = "permits"
    console: bool = True


class Settings(BaseSettings):
    """Configuración raíz de la aplicación."""

    app: AppConfig = Field(default_factory=AppConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    excel: ExcelConfig = Field(default_factory=ExcelConfig)
    pdf: PdfConfig = Field(default_factory=PdfConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    model_config = SettingsConfigDict(
        env_prefix="PERMITS_",
        env_nested_delimiter="__",
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        # El YAML entra como kwargs del constructor (init_settings). Por defecto
        # pydantic-settings da prioridad a init sobre el entorno, lo que
        # invertiría nuestra precedencia documentada (.env > config.yaml).
        # Reordenamos: entorno > .env > YAML.
        return (env_settings, dotenv_settings, init_settings, file_secret_settings)

    # ---- Rutas absolutas resueltas contra la raíz del proyecto -------- #
    def resolve(self, relative: str) -> Path:
        path = Path(relative)
        return path if path.is_absolute() else (PROJECT_ROOT / path)

    @property
    def excel_path(self) -> Path:
        return self.resolve(self.paths.excel_file)

    @property
    def output_dir(self) -> Path:
        return self.resolve(self.paths.output_dir)

    @property
    def logs_dir(self) -> Path:
        return self.resolve(self.paths.logs_dir)

    @property
    def templates_dir(self) -> Path:
        return self.resolve(self.paths.templates_dir)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve la configuración (cacheada). YAML como base, env como override."""
    base = _load_yaml(CONFIG_YAML)
    # Pydantic-settings aplica env vars por encima de los valores pasados aquí.
    return Settings(**base)
