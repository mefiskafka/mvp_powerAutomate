# Manejo de errores en el flujo Power Automate Desktop

Estrategia de resiliencia del orquestador. Complementa a `FLOW.md`.

## Principio

El motor Python **nunca lanza excepciones hacia PAD**: todo desenlace se expresa
en el JSON del contrato (`status`) y en el exit code (0/2/1). Por tanto, los
errores que PAD debe manejar son solo los **suyos**: Outlook no disponible,
adjunto ilegible, Python no encontrado, JSON corrupto.

## Matriz de fallos y respuesta

| # | Fallo | Detección en PAD | Acción |
|---|---|---|---|
| 1 | Outlook no abre / sin sesión | *On error* en `Launch Outlook` | Reintentar 1 vez (espera 30 s); si falla → correo a soporte, terminar flujo |
| 2 | Correo sin adjunto PDF | Condición `Attachments` vacío o sin `.pdf` | Correo al remitente pidiendo el PDF; mover a `Errores`; siguiente iteración |
| 3 | Python no encontrado / venv roto | `CommandExitCode` distinto de 0, 1, 2 o error de la acción | Correo a soporte con `CommandErrorOutput`; NO mover el correo; siguiente iteración |
| 4 | stdout no es JSON | *On error* en `Convert JSON to custom object` | Tratar como `status = error` (rama predeterminada del switch) |
| 5 | `status = error` (fallo técnico del motor: PDF corrupto, Excel bloqueado…) | Rama predeterminada del switch | Correo a soporte con `Result.message`; correo queda en bandeja para reproceso |
| 6 | `status = validation_error` | Rama del switch | **No es un fallo**: flujo de negocio normal (correo de errores al remitente) |
| 7 | Fallo al enviar el correo de salida | *On error* en `Send email` | Registrar en `logs\pad_errors.txt`; reintentar 1 vez; si falla, correo queda sin mover |
| 8 | Excel abierto por un usuario (lock) | Se manifiesta como `status = error` con `persistence_error` en el detalle | Igual que #5; el Runbook documenta cerrar el archivo y reprocesar |

## Reglas transversales

1. **Nunca asumir éxito**: solo la rama `success` mueve el correo a `Procesados`.
2. **Un correo fallido no detiene el lote**: los *On error* terminan en
   *Continue flow run → Go to next repeat*.
3. **Todo fallo deja rastro doble**: `logs\pad_errors.txt` (PAD) y
   `logs\permits.log` (Python).
4. **Idempotencia**: si un correo se reprocesa, el motor genera un nuevo
   `process_id` y una nueva fila; el folio repetido es detectable en el Excel
   (mejora futura: validación de duplicados en el motor).
5. **Timeout**: configurar la acción Run DOS command con timeout de 120 s;
   si expira → tratar como fallo #3.
