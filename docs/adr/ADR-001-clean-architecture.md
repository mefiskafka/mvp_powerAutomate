# ADR-001 — Clean Architecture para el motor Python

**Estado:** Aceptada · **Fecha:** 2026-07-21

## Contexto

Los proyectos RPA típicos concentran la lógica dentro de la herramienta de
automatización (PAD/UiPath), lo que produce flujos frágiles, no testeables y
atados al vendor. Este proyecto debe demostrar prácticas de ingeniería de
software y sobrevivir a cambios de orquestador, de persistencia y de formato.

## Decisión

Estructurar el motor en capas concéntricas — `domain` ← `application` ←
(`presentation`, `adapters`, `infrastructure`) — con la regla de dependencias
hacia adentro y **puertos** (interfaces ABC) definidos en el dominio e
implementados en infraestructura, ensamblados por un contenedor DI
(`config/container.py`).

## Consecuencias

**Positivas**
- La lógica de negocio se prueba sin Outlook, Excel ni PDFs (34 tests, dobles en
  `tests/conftest.py`).
- Excel→BD, pdfplumber→OCR, fpdf2→WeasyPrint: cada cambio queda confinado a una
  clase de infraestructura + una línea del contenedor.
- El código comunica arquitectura en una entrevista: cada carpeta responde a una
  pregunta distinta.

**Negativas / costos**
- Más archivos y algo de ceremonia (DTOs, puertos) para un MVP pequeño.
- Curva de entrada para quien espera "un script".

Aceptamos el costo: el objetivo del proyecto es precisamente exhibir esta
disciplina.
