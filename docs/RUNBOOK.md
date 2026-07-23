# Runbook — Operación del sistema

Procedimientos operativos: instalar, ejecutar, actualizar, diagnosticar y
recuperar. Público objetivo: operador técnico / soporte.

---

## 1. Instalación

### 1.1 Windows (entorno productivo con PAD)

```bat
:: 1. Clonar
git clone <url-del-repo> C:\repos\mvp_powerAutomate
cd C:\repos\mvp_powerAutomate

:: 2. Entorno virtual
python -m venv .venv
.venv\Scripts\activate

:: 3. Dependencias + paquete
pip install -r requirements.txt
pip install -e .

:: 4. Configuración
copy .env.example .env
:: editar .env si se requieren rutas distintas

:: 5. Insumos de ejemplo y smoke test
python scripts\generate_sample_pdf.py
python -m permits.presentation.cli.main process --pdf sample_data\pdfs\permiso_ejemplo.pdf
```

El smoke test debe imprimir JSON con `"status": "success"`.

Después: construir el flujo PAD según [power_automate/FLOW.md](../power_automate/FLOW.md).

### 1.2 Linux/macOS (desarrollo)

Igual, con `source .venv/bin/activate` y rutas con `/`.

### 1.3 Docker (alternativa encapsulada)

Requiere Docker + Docker Compose (en Windows: Docker Desktop).

```bash
git clone <url-del-repo> && cd mvp_powerAutomate
docker compose up -d                  # API en http://localhost:8000/docs
docker compose run --rm cli process --pdf sample_data/pdfs/permiso_ejemplo.pdf
docker compose --profile test run --rm tests
docker compose down                   # detener (los datos persisten en el host)
```

- Puerto ocupado: `PERMITS_API_PORT=8010 docker compose up -d`.
- Excel, logs y PDFs generados quedan en `data/`, `logs/` y `sample_data/`
  del host (volúmenes).
- PAD consume `http://localhost:8000/api/v1/permits/process/upload` (multipart)
  o `/process` con ruta bajo los volúmenes montados.

### 1.4 (Opcional) WeasyPrint en Windows

Solo si se quiere el renderer de alta calidad:

1. Instalar GTK3 runtime: <https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases>
2. `pip install weasyprint`
3. En `config.yaml`: `pdf.renderer: "weasyprint"`
4. Verificar: `python -c "import weasyprint; print(weasyprint.__version__)"`

Si falla, volver a `pdf.renderer: "fpdf2"` — el sistema funciona igual.

## 2. Ejecución

| Escenario | Comando |
|---|---|
| Proceso completo (lo que invoca PAD) | `python -m permits.presentation.cli.main process --pdf <ruta.pdf>` |
| Demo end-to-end | `scripts\run_sample.ps1` / `./scripts/run_sample.sh` |
| API HTTP | `scripts\run_api.ps1` / `./scripts/run_api.sh` → `http://127.0.0.1:8000/docs` |
| Flujo completo con Outlook | Ejecutar el flujo "ProcesarPermisos" en PAD (▶) |
| Tests | `pytest` |

## 3. Actualización

```bat
cd C:\repos\mvp_powerAutomate
.venv\Scripts\activate
git pull
pip install -r requirements.txt
pip install -e .
pytest              :: verificar antes de operar
```

Revisar `CHANGELOG.md` por cambios de contrato o configuración. Si cambió
`config.yaml`, comparar con el propio y fusionar (el `.env` local no se toca).

## 4. Revisión de logs

| Log | Ubicación | Contenido |
|---|---|---|
| Motor Python (día actual) | `logs/permits.log` | INFO/WARNING/ERROR/DEBUG de cada corrida |
| Motor Python (histórico) | `logs/permits.log.YYYY-MM-DD` | 30 días de retención |
| Errores del flujo PAD | `logs/pad_errors.txt` | Fallos del orquestador |

Búsquedas útiles (PowerShell):

```powershell
Select-String -Path logs\permits.log -Pattern "ERROR"
Select-String -Path logs\permits.log -Pattern "20260721-1200"   # por process_id
```

Cada corrida se rastrea por su `process_id` (aparece en el JSON, en el nombre
del PDF generado y en los logs).

## 5. Recuperación de errores

### 5.1 `status = error` con `persistence_error` (Excel bloqueado)
1. Cerrar `data/permisos.xlsx` en todas las máquinas/usuarios.
2. Reejecutar el comando con el mismo PDF (el correo sigue en bandeja).

### 5.2 `status = error` con `extraction_error` (PDF ilegible)
1. Abrir el PDF manualmente: ¿es un escaneo (imagen)? → fuera de alcance del MVP,
   registrar el permiso a mano y mover el correo.
2. ¿Formato de etiquetas distinto? → ver formato esperado en
   [MANUAL_OPERATIVO.md](MANUAL_OPERATIVO.md#5-formato-del-pdf-de-entrada).

### 5.3 El JSON no llega a PAD / stdout vacío
1. Ejecutar el mismo comando a mano en una consola y observar stderr.
2. Causas típicas: venv sin activar en la acción PAD (usar la ruta absoluta a
   `.venv\Scripts\python.exe`), directorio de trabajo incorrecto (debe ser la
   raíz del proyecto).

### 5.4 Fila incorrecta en el Excel
El motor solo agrega filas (append). Corregir manualmente la fila y conservar el
`process_id` en Observaciones para auditoría.

### 5.5 Reprocesar un correo
Mover el correo de `Procesados` a la bandeja y marcarlo como no leído; la
siguiente ejecución del flujo lo tomará. Se generará un nuevo `process_id`
(y una fila adicional si es válido — eliminar la duplicada si no se desea).

## 6. Reinicio del proceso

1. Cerrar PAD y Outlook.
2. Verificar que no queden procesos Python colgados
   (`tasklist | findstr python`; `taskkill /PID <pid> /F` si es necesario).
3. Abrir Outlook y esperar sincronización del buzón.
4. Ejecutar el smoke test de la sección 1.1 (paso 5).
5. Ejecutar el flujo PAD normalmente.

## 7. Checklist de salud

- [ ] `pytest` verde
- [ ] Smoke test CLI devuelve `success`
- [ ] `GET /health` responde `{"status": "ok"}` (si se usa el API)
- [ ] `logs/permits.log` del día existe y crece
- [ ] `data/permisos.xlsx` abre y tiene encabezados correctos
- [ ] Carpetas Outlook `Procesados` y `Procesados/Errores` existen
