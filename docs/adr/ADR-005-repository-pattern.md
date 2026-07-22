# ADR-005 — Repository Pattern para la persistencia

**Estado:** Aceptada · **Fecha:** 2026-07-21

## Contexto

La persistencia elegida (Excel, ADR-004) es explícitamente provisional: el
documento de alcance anticipa una migración a base de datos cuando el volumen lo
justifique. Acoplar el caso de uso a openpyxl haría esa migración invasiva.

## Decisión

Definir el puerto `PermitRepository` (ABC) en `domain/ports/` con la única
operación que el negocio necesita hoy (`save`), e implementarlo en
`infrastructure/persistence/excel_permit_repository.py`. El caso de uso recibe
el repositorio por constructor y desconoce su tecnología.

## Consecuencias

- Los tests del caso de uso usan `InMemoryRepository` (en `tests/conftest.py`):
  rápidos, sin archivos temporales, y verifican el comportamiento clave
  ("un permiso inválido NO llama a save").
- Migrar a SQLite/PostgreSQL = crear `SqlPermitRepository` y cambiar una línea
  en `config/container.py`. Cero cambios en dominio/aplicación.
- Interfaz mínima deliberada: no se especulan métodos (`find_by_folio`,
  `list_all`) que nadie consume aún (YAGNI); se agregarán cuando exista el caso
  de uso que los requiera (p. ej. detección de folios duplicados).
