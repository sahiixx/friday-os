from pathlib import Path

RUNTIME_DIR = Path.home() / ".openjarvis"
SOUL_PATH = RUNTIME_DIR / "SOUL.md"
USER_PATH = RUNTIME_DIR / "USER.md"
MEMORY_PATH = RUNTIME_DIR / "MEMORY.md"

DEFAULT_SOUL = "You are FRIDAY, a calm, concise, voice-first personal AI."
DEFAULT_USER = "The user has not yet provided a USER.md."
DEFAULT_MEMORY = "No prior memory yet."


def _read(path: Path, default: str) -> str:
    try:
        return path.read_text(encoding="utf-8").strip() or default
    except FileNotFoundError:
        return default


def load() -> str:
    """Compose the system prompt from the live ~/.openjarvis/ runtime.

    Reads SOUL/USER/MEMORY markdown verbatim. Missing files fall back to
    conservative defaults so the import works on a machine without the
    OpenJarvis runtime installed.
    """
    soul = _read(SOUL_PATH, DEFAULT_SOUL)
    user = _read(USER_PATH, DEFAULT_USER)
    memory = _read(MEMORY_PATH, DEFAULT_MEMORY)
    return "\n\n".join([
        f"# SOUL\n{soul}",
        f"# USER\n{user}",
        f"# MEMORY\n{memory}",
    ])
