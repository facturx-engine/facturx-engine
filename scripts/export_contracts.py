#!/usr/bin/env python3
"""Export checked-in OpenAPI and strict serialization JSON Schema artifacts."""

import json
from pathlib import Path
from typing import Union

from pydantic import TypeAdapter

from app.main import app
from app.schemas.integration import (
    SerializationFailureResponse,
    SerializationResponse,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    serialization_contract = TypeAdapter(
        Union[SerializationResponse, SerializationFailureResponse]
    ).json_schema()
    serialization_contract["$id"] = (
        "https://facturx-engine.github.io/facturx-engine/schemas/serialize-response.v2.schema.json"
    )
    serialization_contract["title"] = "Factur-X Engine strict serialization contract v2"

    _write_json(
        PROJECT_ROOT / "docs" / "schemas" / "serialize-response.v2.schema.json",
        serialization_contract,
    )
    _write_json(PROJECT_ROOT / "docs" / "openapi.json", app.openapi())


if __name__ == "__main__":
    main()
