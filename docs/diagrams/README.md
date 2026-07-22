# Diagramas del sistema

Los cinco diagramas del proyecto en Mermaid (renderizan directo en GitHub).
Los de componentes y secuencia también aparecen contextualizados en
[ARCHITECTURE.md](../ARCHITECTURE.md); el de clases, en [TDD.md](../TDD.md).

---

## 1. Diagrama de componentes

```mermaid
flowchart TB
    subgraph EXT["Externos"]
        OUTLOOK[(Outlook 365)]
        EXCEL[(permisos.xlsx)]
        FS[(Sistema de archivos<br/>PDFs · logs)]
    end

    subgraph PAD["Power Automate Desktop"]
        FLOW[Flujo ProcesarPermisos]
    end

    subgraph MOTOR["Motor Python (permits)"]
        direction TB
        CLI[presentation/cli]
        API[presentation/api<br/>FastAPI]
        CONTRACT[adapters/contract]
        UC[application<br/>ProcessPermitUseCase]
        DOM[domain<br/>entidades · reglas · puertos]
        INF[infrastructure<br/>pdfplumber · openpyxl · fpdf2/WeasyPrint]
        CFG[config<br/>settings · container DI]
    end

    OUTLOOK <--> FLOW
    FLOW -->|CLI + JSON| CLI
    FLOW -.->|HTTP opcional| API
    CLI --> CONTRACT --> UC
    API --> CONTRACT
    UC --> DOM
    INF -.->|implementa puertos| DOM
    CFG -->|inyecta| UC
    INF --> EXCEL
    INF --> FS
```

## 2. Diagrama de secuencia

```mermaid
sequenceDiagram
    autonumber
    participant O as Outlook
    participant PAD as Power Automate
    participant CLI as CLI
    participant UC as UseCase
    participant EX as Extractor
    participant VA as Validator
    participant PD as Renderer
    participant RE as ExcelRepo

    O->>PAD: Correo + PDF adjunto
    PAD->>CLI: python -m ... process --pdf ruta
    CLI->>UC: execute(request)
    UC->>EX: extract(pdf)
    EX-->>UC: PermitDTO
    UC->>VA: validate(dto)
    VA-->>UC: ValidationResult
    UC->>PD: render(dto, validation)
    PD-->>UC: ruta PDF
    alt ValidationResult válido
        UC->>RE: save(permit)
        RE-->>UC: ok (fila en Excel)
    end
    UC-->>CLI: ProcessResult
    CLI-->>PAD: JSON + exit code (0/2/1)
    alt success
        PAD->>O: Correo éxito + PDF → mover a Procesados
    else validation_error
        PAD->>O: Correo errores + PDF → mover a Errores
    else error
        PAD->>O: Alerta a soporte (correo queda en bandeja)
    end
```

## 3. Diagrama de flujo (proceso de negocio)

```mermaid
flowchart TD
    A([Correo nuevo<br/>“Solicitud de Permiso”]) --> B[Descargar PDF adjunto]
    B --> C[Extraer datos del PDF]
    C -->|falla I/O| ERR[status = error]
    C --> D{¿Pasa las 5<br/>validaciones?}
    D -->|Sí| E[Generar PDF resumen]
    E --> F[Agregar fila al Excel<br/>estado PROCESADO]
    F --> G[status = success]
    D -->|No| H[Generar PDF<br/>reporte de errores]
    H --> I[NO tocar Excel]
    I --> J[status = validation_error]
    G --> K[Correo “procesado correctamente”<br/>+ PDF resumen]
    J --> L[Correo con errores<br/>+ PDF reporte]
    ERR --> M[Alerta a soporte]
    K --> N([Mover correo a Procesados])
    L --> O([Mover a Procesados/Errores])
    M --> P([Correo queda en bandeja])
```

## 4. Diagrama de carpetas

```mermaid
flowchart LR
    ROOT[mvp_powerAutomate/]
    ROOT --> SRC[src/permits/]
    SRC --> D1[domain/<br/>entities · value_objects · ports · services]
    SRC --> D2[application/<br/>dto · use_cases]
    SRC --> D3[infrastructure/<br/>extraction · persistence · rendering · logging]
    SRC --> D4[adapters/ · presentation/ · config/]
    ROOT --> T[tests/<br/>unit · integration]
    ROOT --> S[sample_data/<br/>emails · pdfs · expected_output · logs]
    ROOT --> PA[power_automate/<br/>FLOW.md · error_handling.md · screenshots]
    ROOT --> DOC[docs/<br/>ARCHITECTURE · SDD · TDD · RUNBOOK · manuales · adr · diagrams]
    ROOT --> OTR[templates/ · scripts/ · data/ · logs/]
```

## 5. Diagrama de clases

```mermaid
classDiagram
    direction TB

    class PdfExtractor { <<interface>> +extract(Path) PermitDTO }
    class PermitRepository { <<interface>> +save(Permit, ...) }
    class PdfRenderer { <<interface>> +render(...) Path }

    class ProcessPermitUseCase {
        +execute(ProcessRequest) ProcessResult
    }
    class PermitValidator { +validate(PermitDTO) ValidationResult }

    class Permit {
        +Folio folio
        +str empresa
        +DateRange date_range
        +bool vehiculo
        +Plates plates
        +list personas
        +create()$
    }
    class Folio
    class DateRange
    class Plates
    class ValidationResult { +is_valid +add() }
    class ProcessResult { +status +message +process_id +output_pdf +errors }

    class PdfplumberExtractor
    class ExcelPermitRepository
    class Fpdf2Renderer
    class WeasyPrintRenderer
    class Container { +process_permit_use_case() }

    PdfExtractor <|.. PdfplumberExtractor
    PermitRepository <|.. ExcelPermitRepository
    PdfRenderer <|.. Fpdf2Renderer
    PdfRenderer <|.. WeasyPrintRenderer

    ProcessPermitUseCase o-- PdfExtractor
    ProcessPermitUseCase o-- PermitValidator
    ProcessPermitUseCase o-- PermitRepository
    ProcessPermitUseCase o-- PdfRenderer
    ProcessPermitUseCase ..> ProcessResult
    PermitValidator ..> ValidationResult
    Permit *-- Folio
    Permit *-- DateRange
    Permit *-- Plates
    Container ..> ProcessPermitUseCase : ensambla (DI)
```
