# ADR-004 — Excel como persistencia del MVP

**Estado:** Aceptada · **Fecha:** 2026-07-21

## Contexto

El MVP necesita registrar los permisos procesados. Los consumidores del registro
son personas de operación que ya trabajan con Excel; no existe infraestructura
de base de datos ni DBA en el alcance.

## Decisión

Persistir en un libro Excel (`data/permisos.xlsx`, hoja `Permisos`, 10 columnas
definidas en `config.yaml`) mediante **openpyxl**, detrás del puerto
`PermitRepository`.

## Alternativas consideradas

| Alternativa | Rechazo |
|---|---|
| SQLite | Gratis y simple, pero los operadores no lo consultan directamente; exigiría una vista/consulta adicional |
| SQL Server / PostgreSQL | Sobredimensionado para el MVP; requisitos de instalación y permisos |
| CSV | Sin tipos ni hoja formateada; peor UX para operación |

## Consecuencias

**Positivas** — entregable inmediatamente útil para el negocio; cero
infraestructura; auditable a simple vista.

**Negativas y mitigaciones**
- *Bloqueo de archivo si alguien lo abre en modo edición* → `PersistenceError`
  controlado + procedimiento en RUNBOOK §5.1.
- *Sin transacciones ni concurrencia* → aceptable: un solo flujo escribe.
- *Escala limitada* → el Repository Pattern (ADR-005) reduce la migración a BD a
  una clase nueva + una línea del contenedor DI.
