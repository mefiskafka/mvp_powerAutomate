# ADR-002 — Power Automate Desktop solo como orquestador

**Estado:** Aceptada · **Fecha:** 2026-07-21

## Contexto

Se necesita integración nativa con Outlook empresarial (Office 365) en Windows
sin costo de licencias adicionales. PAD ofrece acciones de Outlook de escritorio
listas para usar, pero permite (y tienta a) programar lógica dentro del flujo.

## Decisión

PAD ejecuta exclusivamente las responsabilidades de **orquestación**: detectar
correos, descargar adjuntos, invocar el motor Python, leer el JSON del contrato,
enviar correos y mover mensajes. **Cero reglas de negocio en el flujo**: ni
validaciones, ni parsing del PDF, ni escritura del Excel.

## Alternativas consideradas

| Alternativa | Rechazo |
|---|---|
| Toda la lógica en PAD | No testeable, no versionable en texto, vendor lock-in |
| Python también para Outlook (win32com/exchangelib) | Duplicaría la integración que PAD ya da gratis; permisos corporativos más complejos |
| UiPath | Licenciamiento; PAD viene con Windows |

## Consecuencias

- El flujo PAD es trivial (≈15 acciones) y se documenta por completo en
  `power_automate/FLOW.md` — reconstruible en minutos.
- El motor se desarrolla y prueba en cualquier SO; solo la capa PAD exige Windows.
- Sustituir PAD por UiPath/cron = reimplementar 15 acciones, no el sistema.
