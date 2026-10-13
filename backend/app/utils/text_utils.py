import re


def clean_text(text: str) -> str:
    """Normalize whitespace and strip non-printable characters."""
    if not text:
        return ""
    text = text.replace("\x00", "").replace("\ufeff", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def truncate_for_prompt(text: str, max_chars: int = 120_000) -> str:
    """Keep prompts within a sane size for the Gemini API."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[...content truncated...]"
