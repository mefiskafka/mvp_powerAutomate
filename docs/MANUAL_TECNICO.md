# Manual Técnico

Recorrido módulo a módulo del motor Python: responsabilidad, diseño interno y
flujo. Público objetivo: desarrollador que mantiene o extiende el sistema.
Complementa al [TDD.md](TDD.md) (contratos y modelos).

---

## 1. `domain/` — el núcleo puro

Sin imports de librerías de I/O. Todo lo que está aquí se puede testear sin
disco, red ni Excel.

### 1.1 `exceptions.py`
Jerarquía única: `DomainError` (base, con `message` y `code`) → `ExtractionError`,
`ValidationError` (transporta `errors: list[dict]`), `PersistenceError`,
`RenderingError`, `ConfigurationError`. La CLI y el API capturan `DomainError`
para mapear al contrato sin conocer los detalles.

### 1.2 `value_objects/`
Inmutables (`@dataclass(frozen=True, slots=True)`), validan en `__post_init__`:

- **`Folio`** — no vacío, `[A-Za-z0-9-]`, hace trim. Lanza `ValidationError`.
- **`DateRange`** — exige `start < end`; expone `days`.
- **`Plates`** — normaliza a mayúsculas; permite vacío (`is_empty`) porque la
  obligatoriedad depende de otro campo (regla del validador, no del VO).

Diseño: *make illegal states unrepresentable* — si existe un `DateRange`, es válido.

### 1.3 `entities/`
- **`Permit`** — agregado central. `Permit.create(...)` fabrica desde primitivos
  ensamblando los VOs (segunda barrera de validación). Propiedad
  `cantidad_personas`.
- **`ValidationResult` / `ValidationIssue`** — acumulador de fallos
  `{campo, regla, detalle}`; `is_valid` ⇔ lista vacía.
- **`ProcessResult` / `ProcessStatus`** — desenlace interno de una corrida
  (`StrEnum`: `success | validation_error | error`). Es lo que la capa de
  presentación traduce al contrato.

### 1.4 `ports/`
Interfaces ABC que invierten las dependencias (la D de SOLID):
`PdfExtractor.extract`, `PermitRepository.save`, `PdfRenderer.render`.
Cualquier implementación nueva (OCR, base de datos, otro motor PDF) se enchufa
implementando el puerto y registrándola en `config/container.py`.

### 1.5 `services/permit_validator.py`
`PermitValidator.validate(dto) -> ValidationResult`. Evalúa las 5 reglas de
negocio **acumulando** fallos (no fail-fast) para que el remitente reciba el
reporte completo. No lanza excepciones: devolver datos > lanzar control de flujo.

## 2. `application/` — orquestación de negocio

### 2.1 `dto/`
- **`PermitDTO`** — datos crudos post-extracción (Pydantic, todo opcional/default;
  la validación de negocio NO vive aquí a propósito).
- **`ProcessRequest`** — entrada del caso de uso (`pdf_path`).
- **`ProcessResponse`** — **el contrato** JSON; `from_result()` traduce desde
  `ProcessResult`.

### 2.2 `use_cases/process_permit.py`
`ProcessPermitUseCase` recibe TODO por constructor (extractor, validador,
repositorio, renderer, `output_dir`, `clock`). Flujo de `execute()`:

```
extract → validate → render (siempre) → ¿válido? → sí: Permit.create + save
                                                  → no: retornar sin persistir
```

Decisiones internas:
- `process_id = clock().strftime("%Y%m%d-%H%M%S")` — el reloj se inyecta para
  tests deterministas.
- El PDF se genera **antes** de decidir persistencia: ambos desenlaces adjuntan
  PDF (resumen o reporte de errores).
- `ExtractionError` y `RenderingError` se capturan y devuelven como
  `ProcessResult(error)`; nunca burbujean crudas.
- `_safe_folio()` sanea el folio para usarlo en el nombre del archivo.

## 3. `infrastructure/` — detalles reemplazables

### 3.1 `extraction/pdfplumber_extractor.py`
Parser por etiquetas línea a línea (`Etiqueta: valor`):
- `_LABELS`: alias por campo ("empresa"/"compañía", "fecha inicio"/"fecha de inicio"…).
- `_parse_date`: intenta `%Y-%m-%d`, `%d/%m/%Y`, `%d-%m-%Y`; devuelve `None` si
  ninguno aplica (el validador lo convierte en error de negocio).
- `_parse_personas`: detecta la sección "personas...:" y recolecta viñetas
  (`- • *`), nombres sin viñeta, o lista inline separada por comas.
- Lanza `ExtractionError` solo por problemas de I/O (archivo ausente, PDF
  corrupto, sin texto); los campos faltantes NO son error de extracción — son
  datos vacíos que el validador reportará con detalle.

### 3.2 `persistence/excel_permit_repository.py`
- `_open_or_create()`: crea el libro/hoja con encabezados si no existen.
- `save()`: append de una fila (orden fijo alineado con `excel.headers`),
  crea el directorio padre si falta y guarda. Cualquier excepción se envuelve
  en `PersistenceError`.

### 3.3 `rendering/`
- **`fpdf2_renderer.py`** (default) — layout programático; encabezado con estado
  en color, metadatos (proceso, fecha), tabla de campos, lista de personas y
  sección de validaciones.
- **`weasyprint_renderer.py`** — Jinja2 (`templates/summary.html.j2`) → HTML →
  PDF. El `import weasyprint` es **perezoso** (dentro de `render`) para que el
  paquete funcione sin GTK instalado mientras se use fpdf2.
- **`renderer_factory.py`** — `create_renderer("fpdf2"|"weasyprint")`; valor no
  soportado → `ConfigurationError`.

### 3.4 `logging/logger.py`
`configure_logging()` idempotente sobre el root logger:
`TimedRotatingFileHandler` (medianoche, 30 backups, sufijo `%Y-%m-%d`) +
handler de consola opcional. Los módulos solo hacen
`logging.getLogger(__name__)`.

## 4. `adapters/contract.py`

Único punto donde se define el mapeo hacia el orquestador:
`EXIT_CODES = {SUCCESS: 0, VALIDATION_ERROR: 2, ERROR: 1}`,
`to_response()`, `to_exit_code()`. Si mañana el contrato cambia (p. ej. agregar
un campo), se toca aquí y en `ProcessResponse` — nada más.

## 5. `presentation/`

### 5.1 `cli/main.py`
`argparse` con subcomando `process --pdf`. Garantías:
- stdout = SOLO el JSON (los logs van a stderr) — crítico para que PAD parsee.
- try/except global: cualquier excepción imprevista se convierte en
  `status=error` con el contrato intacto (exit 1).

### 5.2 `api/`
- `app.py::create_app()` — app factory (instancias aisladas para tests);
  lifespan crea el `Container` y configura logging una vez; `GET /health`.
- `routers/permits.py` — `_execute()` centraliza caso de uso → HTTP:
  desenlaces de negocio → 200, técnicos → 500. Endpoint por ruta y por upload
  (multipart → archivo temporal → mismo flujo → cleanup en `finally`).

## 6. `config/`

### 6.1 `settings.py`
`PROJECT_ROOT = Path(__file__).resolve().parents[3]` — las rutas relativas se
resuelven contra la raíz del repo, no contra el CWD (PAD puede invocar desde
cualquier directorio). `Settings(BaseSettings)` con sub-modelos (`app`, `paths`,
`excel`, `pdf`, `logging`); base desde `config.yaml`, overrides desde `.env`
(`PERMITS_` + `__`). `get_settings()` cacheada con `lru_cache`.

### 6.2 `container.py`
DI manual (sin framework, transparente para entrevistas): `Container` construye
extractor/validador/repositorio/renderer (vía factory) y arma el
`ProcessPermitUseCase`. Acepta `settings` y `clock` inyectables para tests.
**Es el único módulo que importa a la vez aplicación e infraestructura.**

## 7. Cómo extender

| Necesidad | Dónde tocar |
|---|---|
| Nuevo campo del permiso | `PermitDTO` → `_LABELS` del extractor → regla en validador (si aplica) → `Permit` → fila del repositorio → renderers → headers en `config.yaml` |
| Nueva regla de negocio | Solo `PermitValidator` (+ test en `tests/unit/test_permit_validator.py`) |
| Persistir en BD | Nueva clase que implemente `PermitRepository` + cambio en `container.py` |
| OCR para escaneados | Nueva clase `PdfExtractor` + cambio en `container.py` |
| Otro orquestador (UiPath) | Nada: consumir la misma CLI o API |
