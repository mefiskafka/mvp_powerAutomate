# ADR-006 — Strategy Pattern para el motor de PDF (fpdf2 default, WeasyPrint opcional)

**Estado:** Aceptada · **Fecha:** 2026-07-21

## Contexto

El requerimiento original pedía WeasyPrint (Jinja2 → HTML/CSS → PDF, excelente
calidad tipográfica). Pero WeasyPrint depende de GTK/Pango a nivel de sistema
operativo, y en Windows esa instalación manual es la causa número uno de que
proyectos así no arranquen al clonarlos — inaceptable para un MVP de portafolio
que debe reproducirse en cualquier máquina.

## Decisión

Puerto `PdfRenderer` (Strategy) con dos implementaciones intercambiables por
configuración (`config.yaml → pdf.renderer`):

- **`Fpdf2Renderer`** — **default**. Pure-Python, cero dependencias del SO;
  garantiza la primera corrida en cualquier equipo.
- **`WeasyPrintRenderer`** — opcional. Usa `templates/summary.html.j2`; el
  `import weasyprint` es perezoso (dentro de `render()`) para que el paquete
  cargue aunque GTK no exista.

Un **Factory** (`renderer_factory.create_renderer`) traduce la config a la
estrategia; valor desconocido → `ConfigurationError`.

## Consecuencias

- `git clone` + `pip install` + correr: funciona siempre (fpdf2).
- Quien quiera calidad HTML/CSS activa WeasyPrint siguiendo RUNBOOK §1.4, sin
  tocar código.
- Doble mantenimiento del layout del PDF — aceptado: el resumen es un documento
  corto y estable, y el patrón Strategy exhibido es en sí un objetivo del
  proyecto.
- El renderer recibe el DTO crudo (no la entidad) para poder generar el PDF de
  reporte de errores de permisos inválidos.
