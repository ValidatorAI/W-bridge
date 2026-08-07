import html
import re

def str_to_bool(value: str) -> bool:
    return value.lower() in {"true", "1", "yes"}

def _strip_html(raw_html: str) -> str:
	no_tags = re.sub(r"<[^>]*>", "", raw_html)
	decoded = html.unescape(no_tags)
	return re.sub(r"\s+", " ", decoded).strip()