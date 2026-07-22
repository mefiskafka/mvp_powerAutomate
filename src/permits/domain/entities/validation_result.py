"""Entidad de dominio: ValidationResult.

Resultado estructurado de aplicar las reglas de negocio a un permiso. Transporta
la lista de fallos para poder construir tanto el reporte de errores como el
contrato de salida hacia Power Automate.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """Un fallo de validación individual."""

    campo: str
    regla: str
    detalle: str

    def to_dict(self) -> dict[str, str]:
        return {"campo": self.campo, "regla": self.regla, "detalle": self.detalle}


@dataclass(slots=True)
class ValidationResult:
    """Agregado de fallos de validación. Vacío = válido."""

    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.issues) == 0

    def add(self, campo: str, regla: str, detalle: str) -> None:
        self.issues.append(ValidationIssue(campo=campo, regla=regla, detalle=detalle))

    def to_list(self) -> list[dict[str, str]]:
        return [issue.to_dict() for issue in self.issues]
