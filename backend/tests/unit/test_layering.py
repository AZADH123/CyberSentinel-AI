"""Architecture layering guard: ``domain/`` must be pure Python with no I/O."""

from __future__ import annotations

import ast
import pathlib

FORBIDDEN = {
    "fastapi",
    "sqlalchemy",
    "httpx",
    "pydantic_settings",
    "os.environ",
    "cybersentinel.integrations",
    "cybersentinel.db",
    "cybersentinel.services",
    "cybersentinel.api",
}

DOMAIN_ROOT = pathlib.Path(__file__).resolve().parents[3] / "cybersentinel" / "domain"


def test_domain_layer_has_no_forbidden_imports() -> None:
    offenders: dict[str, list[str]] = {}
    for module in DOMAIN_ROOT.rglob("*.py"):
        tree = ast.parse(module.read_text(encoding="utf-8"), filename=str(module))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                if any(name == banned or name.startswith(banned) for banned in FORBIDDEN):
                    offenders.setdefault(str(module.relative_to(DOMAIN_ROOT.parent)), [])
                    offenders[str(module.relative_to(DOMAIN_ROOT.parent))].append(name)

    assert not offenders, f"domain modules import I/O dependencies: {offenders}"
