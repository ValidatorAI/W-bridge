import re


def str_to_bool(value: str) -> bool:
    return value.lower() in {"true", "1", "yes"}


def _strip_command_occurrence(raw_content: str, command: str) -> str:
    normalized = raw_content or ""
    pattern = re.compile(rf"(?i)\s*{re.escape(command)}\b")
    return pattern.sub("", normalized).strip()