# SDD — Solution Design Document

**Proyecto:** RPA Procesamiento de Permisos
**Versión:** 1.1.0 · **Fecha:** 2026-07-21

---

## 1. Alcance

### 1.1 Incluido
- Procesamiento automático de correos con asunto "Solicitud de Permiso" que
  adjuntan un PDF con los datos del permiso.
- Extracción, validación, registro en Excel y generación de PDF resumen.
- Notificación por correo del resultado (éxito o errores) con PDF adjunto.
- Clasificación del correo original (Procesados / Errores).
- Operación 100% local en una máquina Windows con Outlook empresarial.

### 1.2 Excluido (fuera del MVP)
- Base de datos (la persistencia es Excel).
- OCR de PDFs escaneados (solo PDFs con texto).
- Procesamiento en tiempo real (el flujo corre bajo demanda o programado).
- Portal web de consulta; múltiples buzones; firma digital de PDFs.

## 2. Requerimientos funcionales

| ID | Requerimiento |
|---|---|
| RF-01 | Detectar correos no leídos cuyo asunto contenga "Solicitud de Permiso" |
| RF-02 | Descargar el PDF adjunto a una carpeta local |
| RF-03 | Extraer del PDF: folio, empresa, fecha inicio, fecha fin, vehículo, placas, personas |
| RF-04 | Validar las 5 reglas de negocio (sección 4) |
| RF-05 | Si el permiso es válido: agregar una fila al Excel maestro |
| RF-06 | Si el permiso es inválido: NO tocar el Excel y generar reporte de errores |
| RF-07 | Generar un PDF resumen en ambos casos (resumen o reporte de errores) |
| RF-08 | Enviar correo al remitente con el resultado y el PDF adjunto |
| RF-09 | Mover el correo procesado a la carpeta correspondiente |
| RF-10 | Registrar toda la operación en logs diarios |

## 3. Requerimientos no funcionales

| ID | Categoría | Requerimiento |
|---|---|---|
| RNF-01 | Arquitectura | Lógica de negocio exclusivamente en Python; PAD sin reglas |
| RNF-02 | Contrato | Salida única JSON `{status, message, output_pdf, errors}` + exit codes estables |
| RNF-03 | Portabilidad | Sin rutas hardcodeadas; configuración en `config.yaml` + `.env` |
| RNF-04 | Portabilidad | El motor debe correr en cualquier máquina sin dependencias del SO (renderer default fpdf2) |
| RNF-05 | Trazabilidad | Cada corrida identificada por `process_id`; logs con nivel y timestamp |
| RNF-06 | Robustez | Un correo fallido no detiene el procesamiento del lote |
| RNF-07 | Calidad | SOLID, PEP8, tests unitarios y de integración, tipado |
| RNF-08 | Reemplazabilidad | El orquestador debe poder sustituirse (UiPath, cron) sin tocar el motor |

## 4. Reglas de negocio

| ID | Regla | Acción si falla |
|---|---|---|
| RN-01 | El folio es obligatorio | Rechazo con detalle |
| RN-02 | La empresa es obligatoria | Rechazo con detalle |
| RN-03 | Fecha inicio estrictamente menor que fecha fin (ambas presentes) | Rechazo con detalle |
| RN-04 | Si vehículo = Sí, las placas son obligatorias | Rechazo con detalle |
| RN-05 | La lista de personas no puede estar vacía | Rechazo con detalle |

Las reglas se evalúan **todas** (se acumulan los fallos); el reporte contiene la
lista completa, no solo el primer error. Un rechazo NUNCA modifica el Excel.

## 5. Casos de uso

### CU-01 Procesar permiso válido (camino feliz)
1. Llega correo "Solicitud de Permiso" con `permiso.pdf`.
2. PAD descarga el PDF e invoca el motor.
3. El motor extrae los 7 campos, valida RN-01…RN-05 → OK.
4. Se agrega la fila al Excel con estado `PROCESADO`.
5. Se genera `"{folio}_{process_id}.pdf"` con el resumen.
6. PAD envía "Permiso procesado correctamente" + PDF y mueve el correo a Procesados.

### CU-02 Procesar permiso inválido
1–3. Igual, pero al menos una regla falla.
4. El Excel NO se modifica.
5. Se genera el PDF con el **reporte de errores** (lista completa de fallos).
6. PAD envía correo de errores al remitente y mueve el correo a Procesados/Errores.

### CU-03 Fallo técnico
1. El PDF está corrupto / el Excel está bloqueado / error inesperado.
2. El motor devuelve `status = error` (exit code 1) sin romper el contrato.
3. PAD alerta a soporte; el correo queda en bandeja para reproceso.

## 6. Excepciones y manejo de errores

| Excepción (Python) | Código | Se traduce a |
|---|---|---|
| `ExtractionError` | `extraction_error` | `status = error` |
| `ValidationError` | `validation_error` | `status = validation_error` |
| `PersistenceError` | `persistence_error` | `status = error` |
| `RenderingError` | `rendering_error` | `status = error` |
| `ConfigurationError` | `configuration_error` | `status = error` |
| Cualquier otra | — | `status = error` (red de seguridad en CLI/API) |

Los fallos del lado PAD (Outlook caído, JSON corrupto, Python ausente) se
gestionan según la matriz de [power_automate/error_handling.md](../power_automate/error_handling.md).

## 7. Riesgos

| # | Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|---|
| 1 | PDF con formato distinto al esperado | Alta | Medio | Parser tolerante (alias de etiquetas, varios formatos de fecha); `status=error` controlado; formato documentado |
| 2 | Excel abierto/bloqueado por un usuario | Media | Medio | `PersistenceError` → correo no se pierde; Runbook indica reproceso |
| 3 | WeasyPrint sin GTK en Windows | Alta | Bajo | fpdf2 como default; WeasyPrint opcional (ADR-006) |
| 4 | Cambio de contraseña / sesión Outlook | Media | Alto | On-error en PAD + alerta a soporte; Runbook |
| 5 | Folios duplicados reprocesados | Media | Bajo | `process_id` único por corrida; detección de duplicados como mejora futura |
| 6 | Crecimiento del Excel | Baja | Bajo | Migración a BD prevista por Repository Pattern (solo cambia infraestructura) |
| 7 | PAD sin trigger en tiempo real (licencia) | Alta | Bajo | Programador de tareas de Windows; upgrade a cloud trigger documentado |
