# ADR-003 — Contrato único expuesto por CLI y FastAPI

**Estado:** Aceptada · **Fecha:** 2026-07-21

## Contexto

El principio API First exige una frontera formal entre orquestador y motor.
Había que elegir el transporte: ¿solo HTTP (API pura), solo CLI, o ambos?

## Decisión

Un único caso de uso (`ProcessPermitUseCase`) expuesto por **dos adaptadores**
que devuelven exactamente el mismo JSON
`{status, message, process_id, folio, output_pdf, errors}`:

- **CLI** (`python -m permits.presentation.cli.main process --pdf ...`) — lo que
  PAD invoca en producción: sin servicio residente, sin puerto, exit codes
  0/2/1 para ramificar.
- **FastAPI** (`POST /api/v1/permits/process[/upload]`) — demuestra API First,
  habilita orquestadores remotos y da documentación viva (Swagger).

El mapeo resultado→contrato vive en un solo módulo (`adapters/contract.py`).
Un test (`test_cli_and_api_share_contract_shape`) garantiza que ambos canales
no diverjan.

## Alternativas consideradas

| Alternativa | Rechazo |
|---|---|
| Solo FastAPI | Requiere uvicorn corriendo como servicio de Windows: un punto de falla extra para una demo local |
| Solo CLI | Pierde el componente API First del portafolio y la vía de integración remota |

## Consecuencias

- PAD usa la vía robusta (CLI); el API queda listo para escalar el diseño.
- Doble superficie que mantener — mitigado porque ambos son ~30 líneas de
  traducción sin lógica.
