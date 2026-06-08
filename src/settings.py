from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_OUTPUT_FILE = Path("output/walmart_orders.xlsx")


class SettingsError(ValueError):
    pass


@dataclass
class AppSettings:
    participants: list[str]
    output_file: Path = DEFAULT_OUTPUT_FILE


def load_env_values(env_path: Path) -> dict[str, str]:
    if not env_path.exists():
        return {}

    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    return values


def load_settings(env_path: Path, participants_override: list[str] | None = None, output_override: Path | None = None) -> AppSettings:
    values = load_env_values(env_path)
    participants = participants_override or parse_participants(values.get("PARTICIPANTS", ""))
    output_file = output_override or Path(values.get("OUTPUT_FILE", DEFAULT_OUTPUT_FILE))

    return AppSettings(
        participants=validate_participants(participants),
        output_file=output_file,
    )


def parse_participants(raw_value: str) -> list[str]:
    return [name.strip() for name in raw_value.split(",") if name.strip()]


def validate_participants(participants: list[str]) -> list[str]:
    cleaned = [participant.strip() for participant in participants if participant.strip()]
    if not cleaned:
        raise SettingsError("Add at least one participant in .env, for example: PARTICIPANTS=Alice,Bob,Charlie")

    seen: set[str] = set()
    duplicates: list[str] = []
    for participant in cleaned:
        key = participant.casefold()
        if key in seen:
            duplicates.append(participant)
        seen.add(key)

    if duplicates:
        raise SettingsError(f"Participant names must be unique: {', '.join(duplicates)}")

    return cleaned
