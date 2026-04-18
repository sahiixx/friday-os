"""Connector registry — lists external MCPs FRIDAY can delegate to."""

from pathlib import Path


def load_connectors() -> list[dict]:
    """Return registered connectors. Tolerant of missing PyYAML (stdlib-only fallback)."""
    path = Path(__file__).parent / "connectors.yaml"
    if not path.exists():
        return []
    try:
        import yaml
        return (yaml.safe_load(path.read_text("utf-8")) or {}).get("connectors", [])
    except ImportError:
        return _parse_minimal(path.read_text("utf-8"))


def _parse_minimal(text: str) -> list[dict]:
    # WHY: avoid forcing PyYAML dep. Minimal parser for our flat schema.
    out: list[dict] = []
    cur: dict = {}
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        stripped = line.lstrip()
        if stripped.startswith("- name:"):
            if cur:
                out.append(cur)
            cur = {"name": stripped.split(":", 1)[1].strip()}
        elif ":" in stripped and cur:
            key, _, val = stripped.partition(":")
            cur[key.strip()] = val.strip().strip("[]").split(", ") if val.strip().startswith("[") else val.strip()
    if cur:
        out.append(cur)
    return out
