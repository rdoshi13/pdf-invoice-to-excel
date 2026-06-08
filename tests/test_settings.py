from pathlib import Path

import pytest

from src.settings import DEFAULT_OUTPUT_FILE, SettingsError, load_settings, parse_participants


def test_parse_participants_trims_comma_separated_names():
    assert parse_participants(" Alice, Bob ,Charlie ,, ") == ["Alice", "Bob", "Charlie"]


def test_load_settings_reads_env_file(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("PARTICIPANTS=Alice, Bob,Charlie\nOUTPUT_FILE=output/custom.xlsx\n", encoding="utf-8")

    settings = load_settings(env_path)

    assert settings.participants == ["Alice", "Bob", "Charlie"]
    assert settings.output_file == Path("output/custom.xlsx")


def test_load_settings_defaults_output_file(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("PARTICIPANTS=Alice\n", encoding="utf-8")

    settings = load_settings(env_path)

    assert settings.output_file == DEFAULT_OUTPUT_FILE


def test_load_settings_rejects_missing_participants(tmp_path):
    with pytest.raises(SettingsError, match="Add at least one participant"):
        load_settings(tmp_path / ".env")


def test_load_settings_rejects_duplicate_participants(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("PARTICIPANTS=Alice,bob,ALICE\n", encoding="utf-8")

    with pytest.raises(SettingsError, match="unique"):
        load_settings(env_path)


def test_cli_overrides_env_values(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("PARTICIPANTS=Alice,Bob\nOUTPUT_FILE=output/from-env.xlsx\n", encoding="utf-8")

    settings = load_settings(env_path, participants_override=["Dana", "Eli"], output_override=Path("output/from-cli.xlsx"))

    assert settings.participants == ["Dana", "Eli"]
    assert settings.output_file == Path("output/from-cli.xlsx")
