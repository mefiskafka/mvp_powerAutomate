# Changelog

Todas las modificaciones relevantes de este proyecto se documentan aquí.
Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/)
y versionado [SemVer](https://semver.org/lang/es/).

## [Unreleased]

### Mejoras futuras identificadas
- Detección de folios duplicados en el motor.
- Trigger en tiempo real vía Power Automate cloud (licencia attended).
- OCR para PDFs escaneados (nueva implementación de `PdfExtractor`).
- Migración Excel → base de datos (nueva implementación de `PermitRepository`).

## [1.3.0] - 2026-07-22 — Docker Compose

### Added
- `Dockerfile` (python:3.12-slim, usuario sin privilegios) y `compose.yaml` con
  tres servicios: `api` (residente con healthcheck), `cli` (one-shot) y `tests`
  (pytest en contenedor). Persistencia en el host vía volúmenes.
- Puerto del host parametrizado con `PERMITS_API_PORT` (default 8000).
- `.dockerignore` (el `.env` y las salidas nunca se hornean en la imagen).
- ADR-007 (Docker Compose) + secciones Docker en README y RUNBOOK §1.3.

### Fixed
- Precedencia de configuración: las variables de entorno ahora sí sobrescriben
  a `config.yaml` (reordenamiento de fuentes en `Settings`); antes el YAML
  silenciaba los `PERMITS_*` (scar registrado).
- Los tests del API ya no escriben PDFs/filas en `sample_data/` ni `data/`:
  redirigen sus salidas a directorios temporales.

## [1.2.0] - 2026-07-21 — Fase 3: Documentación profesional

### Added
- `docs/ARCHITECTURE.md` — componentes, responsabilidades, regla de dependencias,
  contrato, diagramas Mermaid.
- `docs/SDD.md` — alcance, RF/RNF, reglas de negocio, casos de uso, excepciones, riesgos.
- `docs/TDD.md` — módulos, diagrama de clases, modelos, interfaces, API, CLI,
  configuración, logging, estrategia de pruebas.
- `docs/RUNBOOK.md` — instalación (Windows/Linux/WeasyPrint), ejecución,
  actualización, logs, recuperación de errores, reinicio, checklist de salud.
- `docs/MANUAL_OPERATIVO.md` — uso de PAD, cambiar carpeta Outlook, Excel y rutas.
- `docs/MANUAL_TECNICO.md` — recorrido módulo a módulo + guía de extensión.
- 6 ADRs en `docs/adr/` (Clean Architecture, PAD orquestador, contrato CLI+API,
  Excel, Repository, Strategy PDF).
- `docs/diagrams/README.md` — los 5 diagramas Mermaid (componentes, secuencia,
  flujo, carpetas, clases).
- `CONTRIBUTING.md` con reglas de arquitectura no negociables.
- README con índice completo de documentación.

## [1.1.0] - 2026-07-21 — Fase 2: API First + Power Automate

### Added
- Adaptador FastAPI con app factory (`create_app`) y contenedor DI en lifespan:
  `GET /health`, `POST /api/v1/permits/process` (por ruta) y
  `POST /api/v1/permits/process/upload` (multipart). Mismo contrato JSON que la CLI.
- 6 tests de integración del API con `TestClient` (34 tests en total).
- Documentación completa del flujo Power Automate Desktop:
  `power_automate/FLOW.md` (variables, acciones, conectores, Outlook, primera
  corrida) y `power_automate/error_handling.md` (matriz de fallos).
- Scripts `run_api.sh` / `run_api.ps1`.
- Dependencia `python-multipart` para uploads.

## [1.0.0] - 2026-07-21 — Fase 1: Núcleo funcional

### Added
- Clean Architecture completa: `domain`, `application`, `infrastructure`,
  `adapters`, `presentation`, `config`.
- Caso de uso `ProcessPermitUseCase` (extraer → validar → persistir → renderizar).
- Extracción de PDF con **pdfplumber**; persistencia en Excel con **openpyxl**
  (Repository Pattern).
- Renderizado de PDF con **Strategy Pattern**: `fpdf2` (por defecto, portable) y
  `WeasyPrint` (opcional, Jinja2/HTML/CSS).
- Validaciones de negocio centralizadas (`PermitValidator`).
- Contrato PA↔Python: JSON estable + exit codes (0 éxito / 2 validación / 1 error).
- CLI (`permits.presentation.cli.main`) que consume Power Automate.
- Configuración por `config.yaml` + `.env` (sin rutas hardcodeadas).
- Logging profesional con rotación diaria.
- 28 pruebas (unitarias + integración).
- MVP reproducible con `sample_data/` (PDF, correo, Excel, salidas y log).
