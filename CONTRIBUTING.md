# Guía de contribución

Gracias por el interés en mejorar este proyecto. Reglas mínimas para mantener la
calidad y la arquitectura.

## Flujo de trabajo

1. Crear una rama desde `main`: `feature/<descripcion>` o `fix/<descripcion>`.
2. Desarrollar con tests. **`pytest` y `ruff check src tests scripts` deben pasar.**
3. Commit con mensajes descriptivos (imperativo: "Agrega validación de duplicados").
4. Pull request hacia `main` describiendo el qué y el porqué.

## Reglas de arquitectura (no negociables)

- **La regla de dependencias apunta hacia adentro**: `domain` no importa de
  ninguna otra capa; `application` solo de `domain`; nada de I/O fuera de
  `infrastructure`.
- **Toda nueva integración entra por un puerto** (interfaz ABC en
  `domain/ports/`) implementado en `infrastructure/` y cableado en
  `config/container.py`.
- **El contrato PA↔Python es estable**: cambios en
  `ProcessResponse`/`adapters/contract.py` son *breaking changes* — requieren
  versión mayor, actualización de `power_automate/FLOW.md` y del CHANGELOG.
- **Power Automate no recibe lógica de negocio.** Si una regla puede escribirse
  en Python, va en Python.
- **Cero rutas hardcodeadas**: toda ruta nueva pasa por `config.yaml`/`.env`.
- Decisiones de arquitectura relevantes → nuevo ADR en `docs/adr/`.

## Estilo

- PEP8 vía ruff (config en `pyproject.toml`, línea 100).
- Type hints en firmas públicas; docstrings de módulo y de clase.
- Español para docs/docstrings/mensajes (consistencia con el dominio), inglés
  para identificadores.

## Tests

- Regla de negocio nueva → test unitario en `tests/unit/`.
- Adaptador/integración nueva → test en `tests/integration/` usando los dobles
  de `tests/conftest.py` cuando aplique.
- No se aceptan PRs que bajen la cobertura del caso de uso central.

## Registro de cambios

Toda modificación visible para el usuario u operador se anota en `CHANGELOG.md`
(formato Keep a Changelog).
