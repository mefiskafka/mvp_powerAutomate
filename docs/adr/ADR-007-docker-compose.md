# ADR-007 — Docker Compose para encapsular el motor

**Estado:** Aceptada · **Fecha:** 2026-07-22

## Contexto

El motor Python corre nativamente con venv, pero eso exige Python 3.12 y
dependencias correctas en cada máquina. Para demos, evaluación del portafolio y
despliegues del API se quería un arranque de un solo comando y un entorno
idéntico en cualquier host.

## Decisión

`Dockerfile` (python:3.12-slim, usuario sin privilegios uid 1000) +
`compose.yaml` con tres servicios sobre la misma imagen:

| Servicio | Rol | Invocación |
|---|---|---|
| `api` | FastAPI residente, healthcheck, restart | `docker compose up -d` |
| `cli` (profile) | Corrida one-shot con el contrato JSON | `docker compose run --rm cli process --pdf ...` |
| `tests` (profile) | pytest dentro de la imagen | `docker compose --profile test run --rm tests` |

Principios aplicados:
- **La persistencia vive en el host** (volúmenes `data/`, `logs/`,
  `sample_data/`): el contenedor es efímero.
- **El `.env` nunca se hornea en la imagen** (`.dockerignore`); entra por
  `env_file` opcional de compose.
- **Puerto del host parametrizado** (`PERMITS_API_PORT`, default 8000) para
  convivir con otros servicios.
- uid 1000 en el contenedor = uid típico del usuario Linux → los volúmenes
  quedan escribibles sin ajustes de permisos.

## Relación con Power Automate

PAD en Windows no ejecuta dentro del contenedor: consume el **API por HTTP**
(`process/upload` elimina la necesidad de rutas compartidas) o sigue usando la
CLI nativa con venv (RUNBOOK §1.1). Docker no reemplaza esa vía: la complementa.

## Consecuencias

- `git clone` + `docker compose up -d` = motor corriendo idéntico en cualquier
  máquina; los 34 tests se validan también dentro de la imagen.
- La imagen usa fpdf2 (default); WeasyPrint requeriría agregar libpango al
  Dockerfile — trivial en Linux, documentable si se necesita.
- Costo: mantener Dockerfile/compose sincronizados con requirements —
  mitigado porque la imagen instala desde el mismo `requirements.txt`.
