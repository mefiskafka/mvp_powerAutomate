"""Adaptador de entrada CLI — punto de invocación que usa Power Automate Desktop.

Power Automate ejecuta:

    python -m permits.presentation.cli.main process --pdf "<ruta_al_pdf>"

y lee de STDOUT un único JSON con el contrato ``{status, message, output_pdf,
process_id, folio, errors}``. El código de salida (0/1/2) permite además ramificar
el flujo sin parsear texto. Los logs se emiten por STDERR para no contaminar el
JSON de STDOUT.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from permits.adapters.contract import to_exit_code, to_response
from permits.application.dto.process_request import ProcessRequest
from permits.config.container import Container
from permits.domain.entities.process_result import ProcessResult, ProcessStatus


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="permits",
        description="Motor de procesamiento de permisos (RPA API First).",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    process = sub.add_parser("process", help="Procesa un permiso desde un PDF.")
    process.add_argument("--pdf", required=True, help="Ruta al PDF de la solicitud de permiso.")
    return parser


def _emit(result: ProcessResult) -> int:
    response = to_response(result)
    # ensure_ascii=False para conservar acentos; STDOUT solo lleva el JSON.
    print(json.dumps(response.model_dump(), ensure_ascii=False, indent=2))
    return to_exit_code(result)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    container = Container()
    container.setup_logging()

    if args.command == "process":
        use_case = container.process_permit_use_case()
        try:
            result = use_case.execute(ProcessRequest(pdf_path=Path(args.pdf)))
        except Exception as exc:  # red de seguridad: nunca romper el contrato
            result = ProcessResult(
                status=ProcessStatus.ERROR,
                message=f"Error inesperado: {exc}",
                process_id="ERROR",
                errors=[{"campo": "sistema", "regla": "inesperado", "detalle": str(exc)}],
            )
        return _emit(result)

    return 1


if __name__ == "__main__":
    sys.exit(main())
