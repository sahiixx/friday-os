"""FRIDAY OS Widget Definitions

MCP Apps SDK widget manifests for ambient surfaces.
"""

from pathlib import Path
import json

__all__ = ["load_widget", "list_widgets"]

_WIDGET_DIR = Path(__file__).parent


def load_widget(name: str) -> dict:
    """Load widget manifest by name."""
    path = _WIDGET_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Widget '{name}' not found")
    return json.loads(path.read_text())


def list_widgets() -> list[str]:
    """List available widget names."""
    return [p.stem for p in _WIDGET_DIR.glob("*.json")]
