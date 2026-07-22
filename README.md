# RPA — Procesamiento de Permisos (Power Automate Desktop + Python)

Automatización RPA de nivel profesional para procesar solicitudes de permiso que
llegan por correo Outlook empresarial. Aplica el principio **API First**: **Power
Automate Desktop solo orquesta** y **toda la lógica de negocio vive en Python**,
bajo **Clean Architecture**.

> Estado: **proyecto completo** — núcleo Python (Clean Architecture) + CLI +
> FastAPI + flujo Power Automate documentado + 34 tests + MVP reproducible +
> documentación profesional (SDD, TDD, Runbook, manuales, ADRs, diagramas).

## Objetivo

```
Outlook  →  Nuevo correo  →  Descargar PDF adjunto  →  [ PYTHON ]
   [ PYTHON: extraer · validar · actualizar Excel · generar PDF resumen ]
        →  Power Automate  →  Enviar correo con PDF  →  Mover a "Procesados"
```

Power Automate invoca **un único comando** y recibe **un único JSON** de contrato:

```json
{
  "status": "success | validation_error | error",
  "message": "Permiso PER-001245 procesado correctamente.",
  "process_id": "20260721-205204",
  "folio": "PER-001245",
  "output_pdf": "/ruta/.../PER-001245_20260721-205204.pdf",
  "errors": []
}
```

Esto desacopla el orquestador del motor: se podría reemplazar Power Automate por
UiPath sin tocar el código Python.

## Arquitectura (Clean Architecture)

```
presentation (CLI / API)  →  application (casos de uso, DTOs)  →  domain (entidades, reglas, puertos)
                                          ↑
                       infrastructure implementa los puertos (pdfplumber, openpyxl, fpdf2/WeasyPrint)
                                          ↑
                               config/container.py inyecta las dependencias (DI)
```

Patrones aplicados: **Repository** (Excel), **Strategy** (motor PDF), **Factory**
(selección de renderer), **Dependency Injection** (contenedor), **Service Layer**
(validador), **DTOs + Pydantic**, manejo centralizado de excepciones y logging.

## Instalación

Requiere **Python 3.12+**.

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:  .venv\Scripts\activate

pip install -r requirements.txt
pip install -e .
```

El motor de PDF por defecto es **fpdf2** (100% Python, sin dependencias del SO).
WeasyPrint es opcional (mejor tipografía, requiere GTK/Pango — ver `docs/RUNBOOK.md`).

## Ejecución (MVP)

```bash
# 1. Generar los insumos de ejemplo (PDF, correo .eml, Excel vacío)
python scripts/generate_sample_pdf.py

# 2. Procesar un permiso (esto es lo que Power Automate invocará)
python -m permits.presentation.cli.main process --pdf sample_data/pdfs/permiso_ejemplo.pdf
```

Resultado esperado: JSON `status: success`, una fila nueva en `data/permisos.xlsx`
y un PDF resumen en `sample_data/expected_output/`.

Caso de error (vehículo sin placas + fechas invertidas):

```bash
python -m permits.presentation.cli.main process --pdf sample_data/pdfs/permiso_invalido.pdf
# → status: validation_error, exit code 2, Excel NO modificado
```

Atajos: `scripts/run_sample.sh` (Linux/macOS) · `scripts/run_sample.ps1` (Windows).

## API (FastAPI)

El mismo caso de uso, expuesto vía HTTP con el mismo contrato JSON:

```bash
./scripts/run_api.sh          # o scripts\run_api.ps1 en Windows
# Swagger UI: http://127.0.0.1:8000/docs

curl -X POST http://127.0.0.1:8000/api/v1/permits/process \
  -H "Content-Type: application/json" \
  -d '{"pdf_path": "sample_data/pdfs/permiso_ejemplo.pdf"}'
```

Endpoints:

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/api/v1/permits/process` | Procesa un PDF ya presente en disco (escenario PAD local) |
| `POST` | `/api/v1/permits/process/upload` | Procesa un PDF subido como multipart (orquestador remoto) |

## Power Automate Desktop

El flujo completo (variables, acciones, conectores Outlook, invocación del motor,
ramificación por `status` y manejo de errores) está documentado paso a paso en
[`power_automate/FLOW.md`](power_automate/FLOW.md) y
[`power_automate/error_handling.md`](power_automate/error_handling.md).

## Estructura del proyecto

```
src/permits/
  domain/          Entidades, Value Objects, puertos (interfaces), reglas, excepciones
  application/     Casos de uso + DTOs (Pydantic)
  infrastructure/  pdfplumber, openpyxl, fpdf2/WeasyPrint, logging
  adapters/        Contrato PA↔Python (JSON + exit codes)
  presentation/    CLI (usada por Power Automate) y API (FastAPI, Fase 2)
  config/          settings (config.yaml + .env) y contenedor DI
templates/         Plantilla Jinja2/CSS del PDF (WeasyPrint)
tests/             Unit + integration
sample_data/       Insumos y salidas reproducibles del MVP
power_automate/    Documentación del flujo (Fase 2)
docs/              Documentación de arquitectura, SDD, TDD, ADR, diagramas (Fase 3)
```

## Pruebas

```bash
pytest        # 28 tests (unitarios + integración)
```

## Configuración

Sin rutas hardcodeadas: todo vive en `config.yaml` (base) y `.env` (overrides,
prefijo `PERMITS_`, anidación `__`). Ver `.env.example`.

## Documentación

| Documento | Contenido |
| --- | --- |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Componentes, responsabilidades, flujo, dependencias, diagramas |
| [docs/SDD.md](docs/SDD.md) | Alcance, requerimientos, reglas de negocio, casos de uso, riesgos |
| [docs/TDD.md](docs/TDD.md) | Módulos, clases, interfaces, APIs, modelos, validaciones |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | Instalar, ejecutar, actualizar, logs, recuperación, reinicio |
| [docs/MANUAL_OPERATIVO.md](docs/MANUAL_OPERATIVO.md) | Uso de Power Automate, cambiar carpetas/Excel/rutas sin código |
| [docs/MANUAL_TECNICO.md](docs/MANUAL_TECNICO.md) | Cada módulo Python: responsabilidad, diseño interno, cómo extender |
| [docs/adr/](docs/adr/) | 6 Architecture Decision Records |
| [docs/diagrams/](docs/diagrams/README.md) | Componentes, secuencia, flujo, carpetas, clases (Mermaid) |
| [power_automate/FLOW.md](power_automate/FLOW.md) | Flujo PAD paso a paso + primera corrida |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Reglas de contribución y de arquitectura |

## Licencia

MIT — ver [LICENSE](LICENSE).
