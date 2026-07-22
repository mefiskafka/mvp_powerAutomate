# Documento de Arquitectura

Sistema RPA de procesamiento de permisos: **Power Automate Desktop orquesta,
Python decide**. Este documento describe los componentes, sus responsabilidades,
el flujo de datos y las dependencias.

---

## 1. Visión general

El sistema aplica **Clean Architecture** con el principio **API First**: existe un
único núcleo de negocio en Python, expuesto por dos adaptadores intercambiables
(CLI y HTTP), y un orquestador externo (PAD) que solo coordina eventos de Outlook.

```mermaid
flowchart LR
    subgraph Windows["Máquina Windows"]
        subgraph PAD["Power Automate Desktop (orquestador)"]
            A[Detectar correo] --> B[Descargar PDF]
            B --> C[Invocar motor]
            C --> D{status}
            D -->|success| E[Correo + PDF resumen]
            D -->|validation_error| F[Correo de errores]
            D -->|error| G[Alerta a soporte]
            E --> H[Mover a Procesados]
            F --> H
        end
        subgraph PY["Motor Python (lógica de negocio)"]
            CLI[CLI] --> UC[ProcessPermitUseCase]
            API[FastAPI] --> UC
            UC --> X[Extraer PDF]
            UC --> V[Validar reglas]
            UC --> R[Excel]
            UC --> P[PDF resumen]
        end
        C -.->|"JSON {status, message, output_pdf, errors}"| PAD
        C ===>|"python -m ... process --pdf"| CLI
    end
    OUT[(Outlook 365)] <--> PAD
```

## 2. Componentes y responsabilidades

| Componente | Ubicación | Responsabilidad | NO hace |
|---|---|---|---|
| **Orquestador PAD** | `power_automate/` | Detectar correos, descargar adjuntos, invocar el motor, enviar correos, mover mensajes | Validar, extraer, decidir reglas de negocio |
| **CLI** | `presentation/cli/` | Traducir argumentos → caso de uso → JSON por stdout + exit code | Lógica de negocio |
| **API HTTP** | `presentation/api/` | Traducir HTTP → caso de uso → JSON body | Lógica de negocio |
| **Contrato** | `adapters/contract.py` | Mapeo único resultado interno → JSON + exit codes | — |
| **Caso de uso** | `application/use_cases/` | Orquestar extraer → validar → persistir → renderizar | Conocer implementaciones concretas |
| **Dominio** | `domain/` | Entidades, Value Objects, reglas de negocio, puertos | I/O de cualquier tipo |
| **Infraestructura** | `infrastructure/` | pdfplumber, openpyxl, fpdf2/WeasyPrint, logging | Decidir reglas |
| **Configuración/DI** | `config/` | Cargar config.yaml + .env; ensamblar el grafo de objetos | — |

## 3. Regla de dependencias

Las dependencias apuntan **hacia adentro**; el dominio no conoce a nadie:

```mermaid
flowchart TD
    P[presentation<br/>CLI · FastAPI] --> AP[application<br/>use cases · DTOs]
    AD[adapters<br/>contrato PA↔Py] --> AP
    AP --> D[domain<br/>entidades · VOs · reglas · puertos]
    I[infrastructure<br/>pdfplumber · openpyxl · fpdf2 · WeasyPrint · logging] -->|implementa puertos| D
    C[config<br/>settings · container DI] -->|inyecta| P
    C -->|construye| I
```

- `domain` define **puertos** (interfaces ABC): `PdfExtractor`, `PermitRepository`, `PdfRenderer`.
- `infrastructure` los **implementa**; `config/container.py` es el único punto de unión.
- Cambiar Excel→BD, pdfplumber→OCR o fpdf2→WeasyPrint no toca `application` ni `domain`.

## 4. Flujo end-to-end (secuencia)

```mermaid
sequenceDiagram
    participant O as Outlook 365
    participant PAD as Power Automate
    participant CLI as CLI (python -m)
    participant UC as ProcessPermitUseCase
    participant EX as PdfplumberExtractor
    participant VA as PermitValidator
    participant RE as ExcelPermitRepository
    participant PD as PdfRenderer (fpdf2/WeasyPrint)

    O->>PAD: Correo "Solicitud de Permiso" + PDF
    PAD->>PAD: Guardar adjunto en disco
    PAD->>CLI: process --pdf <ruta>
    CLI->>UC: execute(ProcessRequest)
    UC->>EX: extract(pdf) → PermitDTO
    UC->>VA: validate(dto) → ValidationResult
    alt válido
        UC->>PD: render(resumen) → PDF
        UC->>RE: save(permit) → fila en Excel
        UC-->>CLI: ProcessResult(success)
    else inválido
        UC->>PD: render(reporte de errores) → PDF
        Note over UC,RE: El Excel NO se toca
        UC-->>CLI: ProcessResult(validation_error)
    end
    CLI-->>PAD: JSON {status, message, output_pdf, errors} + exit code
    alt status = success
        PAD->>O: Correo "Permiso procesado correctamente" + PDF
        PAD->>O: Mover correo a Procesados
    else status = validation_error
        PAD->>O: Correo de errores + PDF reporte
        PAD->>O: Mover a Procesados/Errores
    else status = error
        PAD->>O: Alerta a soporte (correo queda en bandeja)
    end
```

## 5. El contrato de integración

La pieza que desacopla orquestador y motor. Definido en `adapters/contract.py` y
`application/dto/process_response.py`:

```json
{
  "status": "success | validation_error | error",
  "message": "Permiso PER-001245 procesado correctamente.",
  "process_id": "20260721-120000",
  "folio": "PER-001245",
  "output_pdf": "C:\\...\\PER-001245_20260721-120000.pdf",
  "errors": [{"campo": "...", "regla": "...", "detalle": "..."}]
}
```

| Canal | Transporte del contrato |
|---|---|
| CLI | stdout (JSON) + exit code 0 / 2 / 1 |
| API | body JSON + HTTP 200 (negocio) / 500 (técnico) |

**Consecuencia arquitectónica**: PAD puede sustituirse por UiPath, un cron, o un
consumidor de colas sin modificar una línea del motor.

## 6. Dependencias externas

| Dependencia | Capa | Uso |
|---|---|---|
| pdfplumber | infrastructure | Extracción de texto del PDF |
| openpyxl | infrastructure | Lectura/escritura del Excel maestro |
| fpdf2 | infrastructure | Render PDF portable (default) |
| WeasyPrint + Jinja2 | infrastructure | Render PDF HTML/CSS (opcional, requiere GTK) |
| Pydantic / pydantic-settings | application, config | DTOs, contrato, settings tipados |
| FastAPI + uvicorn | presentation | Adaptador HTTP |
| PyYAML | config | Carga de config.yaml |

## 7. Decisiones de arquitectura

Registradas como ADRs en [adr/](adr/):

- [ADR-001 Clean Architecture](adr/ADR-001-clean-architecture.md)
- [ADR-002 Power Automate solo como orquestador](adr/ADR-002-power-automate-orquestador.md)
- [ADR-003 Contrato CLI + FastAPI sobre el mismo core](adr/ADR-003-contrato-cli-fastapi.md)
- [ADR-004 Excel como persistencia del MVP](adr/ADR-004-excel-persistencia.md)
- [ADR-005 Repository Pattern](adr/ADR-005-repository-pattern.md)
- [ADR-006 Strategy para el motor PDF](adr/ADR-006-strategy-motor-pdf.md)
