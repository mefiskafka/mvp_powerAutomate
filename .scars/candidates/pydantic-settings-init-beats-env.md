---
id: 0
type: landmine
title: pydantic-settings: los kwargs del constructor (YAML) pisan a las env vars salvo que se reordene settings_customise_sources
severity: medium
confidence: 0.9
created: 2026-07-22
authors: ["claude-code"]
anchors:
  - path: src/permits/config/settings.py
  - pattern: "Settings\\(\\*\\*"
violation: "return \\(init_settings"
expires:
  condition: "dejar de cargar config.yaml pasándolo como kwargs a Settings()"
  review_after: 2027-07-22
status: candidate
---

En `get_settings()` el config.yaml se carga y se pasa como kwargs:
`Settings(**base)`. La precedencia por defecto de pydantic-settings v2 es
init > env > dotenv, así que los valores del YAML **silenciaban** cualquier
`PERMITS_*` del entorno o del `.env` — lo contrario de la precedencia
documentada (.env > config.yaml). Se detectó porque los tests del API
(tests/integration/test_api.py) seteaban `PERMITS_PATHS__OUTPUT_DIR` hacia un
tmp_path y aun así escribían PDFs reales en sample_data/expected_output/.

Arreglo aplicado: `Settings.settings_customise_sources` reordena a
(env, dotenv, init, secrets). Si se toca la carga de configuración, NO volver
al orden por defecto mientras el YAML entre por kwargs; cualquier regresión se
manifiesta como "mis variables de entorno no hacen nada" y como tests que
contaminan sample_data/.
