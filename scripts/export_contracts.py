"""Export recall_radar/contracts.py to contracts/schema/recall_radar.schema.json.

Owner: A. Run via `make contracts`. Output is deterministic (sorted keys) so CI can diff it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pydantic.json_schema import models_json_schema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recall_radar.contracts import CONTRACT_VERSION, EXPORTED_MODELS  # noqa: E402


def main() -> None:
    _, schema = models_json_schema(
        [(m, "serialization") for m in EXPORTED_MODELS],
        title="RecallRadarContracts",
        description=f"Recall Radar contracts v{CONTRACT_VERSION}. Generated; do not edit.",
    )
    schema["$id"] = f"recall-radar/contracts/{CONTRACT_VERSION}"
    out = ROOT / "contracts" / "schema" / "recall_radar.schema.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
    print(f"wrote {out.relative_to(ROOT)} (contract v{CONTRACT_VERSION}, {len(schema['$defs'])} defs)")


if __name__ == "__main__":
    main()
