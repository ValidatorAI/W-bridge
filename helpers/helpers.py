def str_to_bool(value: str) -> bool:
    return value.lower() in {"true", "1", "yes"}

def _strip_command_occurrence(raw_content: str, command: str) -> str:
	stripped = raw_content.replace(command, "", 1).strip()
	return stripped or raw_content.strip()