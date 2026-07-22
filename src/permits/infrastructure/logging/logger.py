"""Configuración centralizada de logging profesional.

Escribe logs diarios (rotación a medianoche) y, opcionalmente, a consola. El nivel
se controla por configuración. Todos los módulos usan ``logging.getLogger(__name__)``
y heredan de esta configuración raíz, de modo que INFO/WARNING/ERROR/DEBUG quedan
registrados de forma homogénea.
"""

from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_CONFIGURED = False


def configure_logging(
    *,
    logs_dir: Path,
    level: str = "INFO",
    file_prefix: str = "permits",
    console: bool = True,
) -> None:
    """Configura el logger raíz. Idempotente: solo aplica una vez por proceso."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    logs_dir = Path(logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    formatter = logging.Formatter(_FORMAT, datefmt=_DATE_FORMAT)

    # Handler de archivo con rotación diaria: permits.log -> permits.log.2026-07-21
    file_handler = TimedRotatingFileHandler(
        filename=logs_dir / f"{file_prefix}.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)

    _CONFIGURED = True
