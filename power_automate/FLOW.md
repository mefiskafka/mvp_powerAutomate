# Flujo Power Automate Desktop — "Procesar Solicitudes de Permiso"

Guía completa para construir el flujo en Power Automate Desktop (PAD) sobre
Windows. El flujo **no contiene lógica de negocio**: detecta correos, descarga el
PDF, invoca el motor Python, lee el JSON de respuesta y actúa según `status`.

```
Outlook (bandeja) ──▶ ¿Correo nuevo "Solicitud de Permiso"? ──▶ Guardar PDF adjunto
        ──▶ Ejecutar Python (CLI) ──▶ Parsear JSON ──▶ switch status
              ├─ success           → correo "Permiso procesado correctamente" + PDF resumen → mover correo a "Procesados"
              ├─ validation_error  → correo "Permiso con errores" + PDF de reporte          → mover correo a "Procesados/Errores"
              └─ error             → correo a soporte con el detalle                        → dejar correo en bandeja
```

---

## 1. Prerrequisitos en la máquina Windows

| Componente | Detalle |
|---|---|
| Power Automate Desktop | Incluido en Windows 11 / descarga gratuita de Microsoft |
| Outlook clásico (escritorio) | Sesión iniciada con la cuenta empresarial Office 365 |
| Python 3.12 | `python --version` debe responder en una consola nueva |
| Este proyecto | Clonado, con venv creado y `pip install -r requirements.txt && pip install -e .` |
| Carpetas Outlook | Crear subcarpetas `Procesados` y `Procesados/Errores` en el buzón |

> PAD usa la acción **Outlook** (aplicación de escritorio), no el conector cloud.
> Outlook debe estar **abierto** o PAD lo lanzará.

## 2. Variables del flujo

Definir al inicio (acción **Establecer variable**):

| Variable | Valor de ejemplo | Descripción |
|---|---|---|
| `ProjectRoot` | `C:\repos\mvp_powerAutomate` | Raíz del proyecto clonado |
| `PythonExe` | `%ProjectRoot%\.venv\Scripts\python.exe` | Python del venv (¡no el global!) |
| `AttachmentsDir` | `%ProjectRoot%\inbox_pdfs` | Donde se guardan los PDF descargados |
| `MailFolder` | `Bandeja de entrada` | Carpeta Outlook a monitorear |
| `ProcessedFolder` | `Bandeja de entrada\Procesados` | Destino de correos exitosos |
| `ErrorFolder` | `Bandeja de entrada\Procesados\Errores` | Destino de correos con errores de validación |
| `SubjectFilter` | `Solicitud de Permiso` | Asunto que dispara el proceso |
| `SupportEmail` | `soporte@miempresa.com` | Notificaciones de fallo técnico |

## 3. Acciones del flujo (paso a paso)

### Bloque A — Detección y descarga

1. **Iniciar Outlook** (`Outlook > Launch Outlook`) → produce `OutlookInstance`.
2. **Recuperar mensajes de correo** (`Outlook > Retrieve email messages from Outlook`):
   - Cuenta: la cuenta empresarial.
   - Carpeta: `%MailFolder%`.
   - Recuperar: *Mensajes no leídos*.
   - Filtro asunto: contiene `%SubjectFilter%`.
   - Guardar adjuntos: **Sí**, en `%AttachmentsDir%`.
   - Produce: `RetrievedEmails`.
3. **Por cada** `CurrentMail` **en** `RetrievedEmails` (`Loops > For each`).
4. Dentro del bucle: obtener la ruta del PDF adjunto. `CurrentMail.Attachments`
   contiene las rutas guardadas; tomar la primera que termine en `.pdf`
   (acción **Si** con condición *contiene* `.pdf`) → variable `PdfPath`.

### Bloque B — Invocación del motor Python (el contrato)

5. **Ejecutar aplicación** (`System > Run application`) — *o preferentemente*
   **Ejecutar script de DOS** (`Scripting > Run DOS command`), que captura stdout:

   ```
   Comando:            "%PythonExe%" -m permits.presentation.cli.main process --pdf "%PdfPath%"
   Directorio trabajo: %ProjectRoot%
   Esperar a que termine: Sí
   ```

   Produce: `CommandOutput` (stdout = el JSON del contrato), `CommandErrorOutput`
   (stderr = logs) y `CommandExitCode`.

   > El motor **garantiza** un único JSON por stdout y exit codes estables:
   > `0` = success, `2` = validation_error, `1` = error técnico.

6. **Convertir JSON en objeto personalizado** (`Variables > Convert JSON to custom object`):
   - Entrada: `%CommandOutput%` → produce `Result`.
   - Campos disponibles: `Result.status`, `Result.message`, `Result.output_pdf`,
     `Result.process_id`, `Result.folio`, `Result.errors`.

### Bloque C — Ramificación por status

7. **Switch** sobre `%Result.status%`:

   **Caso `success`:**
   8. **Enviar mensaje de correo** (`Outlook > Send email message through Outlook`):
      - Para: remitente original (`CurrentMail.From`).
      - Asunto: `Permiso procesado correctamente`.
      - Cuerpo: `%Result.message%` + `Folio: %Result.folio%` + `Proceso: %Result.process_id%`.
      - Adjunto: `%Result.output_pdf%`.
   9. **Procesar mensajes de correo** (`Outlook > Process email messages`):
      - Operación: *Mover mensaje*, destino `%ProcessedFolder%`.

   **Caso `validation_error`:**
   10. **Enviar mensaje de correo**:
       - Para: remitente original.
       - Asunto: `Permiso con errores de validación - %Result.folio%`.
       - Cuerpo: `%Result.message%` + detalle de `%Result.errors%`.
       - Adjunto: `%Result.output_pdf%` (PDF con el reporte de errores).
   11. **Mover mensaje** a `%ErrorFolder%`.

   **Caso predeterminado (`error`):**
   12. **Enviar mensaje de correo** a `%SupportEmail%` con `%Result.message%`
       y `%CommandErrorOutput%` (los logs) en el cuerpo.
   13. **No mover el correo** (queda en bandeja para reintento manual).

### Bloque D — Cierre

14. Marcar `CurrentMail` como leído (`Process email messages > Mark as read`).
15. Fin del bucle. (Opcional) **Cerrar Outlook**.

## 4. Disparador / programación

PAD (versión gratuita) no tiene triggers de correo en tiempo real. Opciones:

- **Programador de tareas de Windows**: ejecutar el flujo cada N minutos
  (`"C:\Program Files (x86)\Power Automate Desktop\PAD.Console.Host.exe" ms-powerautomate://console/flows/run?workflowName=ProcesarPermisos`)
  — o simplemente ejecutar el flujo manualmente para la demo.
- **Power Automate cloud + licencia attended**: trigger "When a new email arrives
  (V3)" que lanza el flujo de escritorio. Documentado como mejora futura.

## 5. Manejo de errores en PAD

Ver [error_handling.md](error_handling.md). Resumen:

- Cada acción crítica (Outlook, Run DOS command, Convert JSON) lleva un bloque
  **On error** que:
  1. registra el fallo en `%ProjectRoot%\logs\pad_errors.txt`
     (acción *Escribir texto en archivo*, append con timestamp),
  2. envía correo a `%SupportEmail%`,
  3. continúa con el siguiente correo (**Continue flow run** → siguiente iteración).
- Si `CommandExitCode` no es 0/1/2 o `CommandOutput` no parsea como JSON →
  tratar como `error` (nunca asumir éxito).

## 6. Prueba del flujo (primera corrida)

1. En Windows, clonar el repo y preparar el venv (ver README).
2. Verificar el motor a mano en una consola:
   ```bat
   cd C:\repos\mvp_powerAutomate
   .venv\Scripts\python.exe -m permits.presentation.cli.main process --pdf sample_data\pdfs\permiso_ejemplo.pdf
   ```
   Debe imprimir JSON `"status": "success"`.
3. Enviarse a sí mismo el correo de prueba: asunto `Solicitud de Permiso`,
   adjuntando `sample_data\pdfs\permiso_ejemplo.pdf`
   (o importar `sample_data\emails\correo_ejemplo.eml` arrastrándolo a Outlook).
4. Ejecutar el flujo en PAD (botón ▶).
5. Verificar:
   - llega el correo "Permiso procesado correctamente" con el PDF resumen adjunto,
   - `data\permisos.xlsx` tiene la fila nueva,
   - el correo original quedó en `Procesados`,
   - `logs\permits.log` registró la corrida.
6. Repetir con `permiso_invalido.pdf`: debe llegar el correo de errores de
   validación y el Excel **no** debe cambiar.

## 7. Capturas

Colocar en [screenshots/](screenshots/) al construir el flujo en Windows:

| Archivo | Contenido |
|---|---|
| `01_variables.png` | Bloque de variables iniciales |
| `02_retrieve_emails.png` | Configuración de la acción Retrieve email messages |
| `03_run_python.png` | Acción Run DOS command con el comando del motor |
| `04_parse_json.png` | Convert JSON to custom object |
| `05_switch_status.png` | Switch por status con sus tres ramas |
| `06_send_email.png` | Acción de envío del correo de éxito |
| `07_flow_overview.png` | Vista completa del flujo |
