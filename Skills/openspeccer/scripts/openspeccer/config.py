"""The project's `openspec/config.yaml`: the context, artifact rules and operation guidance OpenSpec
puts in front of agents. Warnings mirror what the OpenSpec CLI ignores, so a silently dropped
setting shows up here."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .schemas import SchemaCatalog
from .yamlish import YamlError, loads

CONTEXT_LIMIT = 50 * 1024  # OpenSpec's MAX_CONTEXT_SIZE; a larger context is dropped
OPERATIONS = ("apply", "archive")
_KNOWN = {"schema", "context", "rules", "operations"}


def config_path(openspec_dir: Path) -> Path | None:
    for name in ("config.yaml", "config.yml"):
        p = openspec_dir / name
        if p.is_file():
            return p
    return None


def project_config(openspec_dir: Path, catalog: SchemaCatalog) -> dict[str, Any]:
    out: dict[str, Any] = {
        "path": None,
        "raw": "",
        "error": None,
        "schema": None,
        "context": "",
        "context_bytes": 0,
        "context_limit": CONTEXT_LIMIT,
        "rules": {},
        "unknown_rules": [],
        "operations": {},
        "other": {},
        "warnings": [],
    }
    path = config_path(openspec_dir)
    if path is None:
        return out
    out["path"] = path.relative_to(openspec_dir.parent).as_posix()
    try:
        out["raw"] = path.read_text(encoding="utf-8")
        data = loads(out["raw"])
    except (OSError, UnicodeDecodeError, YamlError) as e:
        out["error"] = str(e)
        return out
    if not isinstance(data, dict):
        out["error"] = "config is not a mapping"
        return out
    warn = out["warnings"].append

    out["schema"] = str(data["schema"]) if data.get("schema") else None
    context = data.get("context")
    if isinstance(context, str):
        out["context"] = context
        out["context_bytes"] = len(context.encode())
        if out["context_bytes"] > CONTEXT_LIMIT:
            size = out["context_bytes"] // 1024
            warn(f"context is {size}KB, over OpenSpec's 50KB limit, so agents never see it")

    rules = data.get("rules")
    if isinstance(rules, dict):
        out["rules"] = {str(k): [str(r) for r in v] for k, v in rules.items() if isinstance(v, list)}
        out["unknown_rules"] = _unknown_artifacts(list(out["rules"]), catalog)
        for k in out["unknown_rules"]:
            warn(f"rules.{k} matches no artifact in any schema")

    ops = data.get("operations")
    if isinstance(ops, dict):
        for op, body in ops.items():
            if op not in OPERATIONS:
                names = ", ".join(OPERATIONS)
                warn(f"operations.{op} is not an OpenSpec operation ({names}), so it is ignored")
            elif isinstance(body, dict) and isinstance(body.get("guidance"), list):
                out["operations"][op] = [str(g) for g in body["guidance"] if g]

    out["other"] = {k: v for k, v in data.items() if k not in _KNOWN}
    return out


def _unknown_artifacts(keys: list[str], catalog: SchemaCatalog) -> list[str]:
    """Rule keys naming no artifact of any schema. Rules apply across schemas, so a key is only
    unknown when it matches none. Without the CLI, built-in schemas are missing, so nothing is flagged."""
    listed, degraded = catalog.summaries()
    if degraded:
        return []
    known = {str(a) for s in listed for a in s.get("artifacts") or []}
    return [k for k in keys if k not in known]
