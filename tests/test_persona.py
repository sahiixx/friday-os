"""Tests for persona composition from ~/.openjarvis/."""

from unittest.mock import patch

from friday.core.memory import persona


class TestPersonaLoad:
    def test_composes_soul_user_memory_sections(self, tmp_path):
        soul = tmp_path / "SOUL.md"
        user = tmp_path / "USER.md"
        mem = tmp_path / "MEMORY.md"
        soul.write_text("# FRIDAY\nTest persona", encoding="utf-8")
        user.write_text("Name: Tester", encoding="utf-8")
        mem.write_text("Prior note", encoding="utf-8")

        with patch.object(persona, "SOUL_PATH", soul), \
             patch.object(persona, "USER_PATH", user), \
             patch.object(persona, "MEMORY_PATH", mem):
            result = persona.load()

        assert "# SOUL" in result
        assert "# USER" in result
        assert "# MEMORY" in result
        assert "Test persona" in result
        assert "Name: Tester" in result
        assert "Prior note" in result

    def test_falls_back_to_defaults_when_missing(self, tmp_path):
        missing = tmp_path / "nope.md"

        with patch.object(persona, "SOUL_PATH", missing), \
             patch.object(persona, "USER_PATH", missing), \
             patch.object(persona, "MEMORY_PATH", missing):
            result = persona.load()

        assert "FRIDAY" in result
        assert persona.DEFAULT_SOUL in result
        assert persona.DEFAULT_USER in result
