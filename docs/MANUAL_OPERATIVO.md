# Manual Operativo

Guía para el usuario operador: cómo usar el flujo de Power Automate y cómo
ajustar la configuración del día a día **sin tocar código**.

---

## 1. Uso normal del flujo Power Automate

1. Abrir **Outlook** (sesión empresarial iniciada).
2. Abrir **Power Automate Desktop** y localizar el flujo **ProcesarPermisos**.
3. Pulsar **▶ Ejecutar**. El flujo:
   - toma los correos no leídos con asunto "Solicitud de Permiso",
   - procesa cada PDF adjunto,
   - responde al remitente con el resultado y el PDF,
   - archiva los correos en `Procesados` (o `Procesados/Errores`).
4. Al terminar, revisar el Excel `data\permisos.xlsx` si se desea confirmar.

**Interpretación de los correos de salida:**

| Correo recibido por el remitente | Significado |
|---|---|
| "Permiso procesado correctamente" + PDF resumen | Registrado en el Excel |
| "Permiso con errores de validación" + PDF de errores | NO registrado; corregir el PDF y reenviar |
| (a soporte) alerta técnica | Fallo del sistema; el correo original sigue en bandeja |

## 2. Cambiar la carpeta de Outlook que se monitorea

1. Abrir el flujo en PAD (doble clic → editor).
2. En el bloque de variables iniciales, editar **`MailFolder`**
   (p. ej. `Bandeja de entrada\Permisos`).
3. Si también cambian los destinos, editar **`ProcessedFolder`** y **`ErrorFolder`**.
4. Guardar el flujo. Las carpetas deben existir previamente en Outlook
   (crear con clic derecho → *Nueva carpeta*).

## 3. Modificar el Excel

### 3.1 Cambiar la ubicación del archivo
Editar `config.yaml`:

```yaml
paths:
  excel_file: "C:/rutas/compartidas/permisos.xlsx"   # o relativa al proyecto
```

(También vía `.env`: `PERMITS_PATHS__EXCEL_FILE=...` — tiene prioridad.)

### 3.2 Cambiar el nombre de la hoja
```yaml
excel:
  sheet_name: "Permisos2026"
```

### 3.3 Sobre las columnas
Las 10 columnas están definidas en `config.yaml → excel.headers`. **No reordenar
ni eliminar columnas** sin acompañarlo de un cambio en el código
(`ExcelPermitRepository` escribe las filas en ese orden). Agregar columnas al
final del Excel a mano es seguro (quedarán vacías en filas nuevas).

### 3.4 Consultar el Excel
Abrir en modo **solo lectura** mientras el flujo pueda estar corriendo: si el
archivo está bloqueado para escritura, el procesamiento fallará con
`persistence_error` (recuperación: [RUNBOOK §5.1](RUNBOOK.md#51-status--error-con-persistence_error-excel-bloqueado)).

## 4. Cambiar rutas (PDFs, logs, salidas)

Todas las rutas viven en `config.yaml` (o `.env`):

| Qué | Clave | Default |
|---|---|---|
| Excel maestro | `paths.excel_file` | `data/permisos.xlsx` |
| PDFs resumen generados | `paths.output_dir` | `sample_data/expected_output` |
| Logs | `paths.logs_dir` | `logs` |
| Carpeta de descarga de adjuntos | Variable **`AttachmentsDir`** en el flujo PAD | `%ProjectRoot%\inbox_pdfs` |

Tras cambiar rutas, ejecutar el smoke test del [RUNBOOK §1.1](RUNBOOK.md#11-windows-entorno-productivo-con-pad).

## 5. Formato del PDF de entrada

El PDF debe contener texto (no imagen escaneada) con etiquetas `Etiqueta: valor`:

```
Solicitud de Permiso
Folio: PER-001245
Empresa: Spin
Fecha Inicio: 2026-01-10
Fecha Fin: 2026-01-15
Vehiculo: Si
Placas: ABC123
Personas con permiso:
- Juan Perez
- Maria Lopez
```

Tolerancias: fechas en `AAAA-MM-DD`, `DD/MM/AAAA` o `DD-MM-AAAA`; "Vehículo"
con o sin acento; `Si/Sí/true/1/x/yes` como afirmativo; personas como viñetas
(`-`, `•`, `*`) o en línea separadas por comas.

## 6. Cambiar el motor de PDF resumen

En `config.yaml`:

```yaml
pdf:
  renderer: "fpdf2"        # portable (default)
  # renderer: "weasyprint" # alta calidad; requiere GTK (RUNBOOK §1.3)
```

## 7. Preguntas frecuentes

**¿Puedo ejecutar el proceso sin Outlook/PAD?**
Sí: `python -m permits.presentation.cli.main process --pdf <ruta>` hace todo
menos el correo (extraer, validar, Excel, PDF).

**¿Dónde veo por qué se rechazó un permiso?**
En el PDF de reporte adjunto al correo de error, y en `logs/permits.log`
(buscar el `process_id`).

**¿Cómo agrego otro asunto de correo válido?**
Variable `SubjectFilter` del flujo PAD.
