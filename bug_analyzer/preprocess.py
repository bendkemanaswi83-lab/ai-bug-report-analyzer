import re

_WS = re.compile(r"[ \t]+")
_BLANKS = re.compile(r"\n{3,}")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_IP = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")
_TOKEN = re.compile(r"\b(?:sk|pk|api|key|token)[-_][A-Za-z0-9_\-]{12,}\b", re.I)

MAX_CHARS = 8000


def redact_pii(text: str) -> str:
    """Mask emails, IPs and API-key-like tokens before sending text to an LLM."""
    text = _EMAIL.sub("[EMAIL]", text)
    text = _IP.sub("[IP]", text)
    return _TOKEN.sub("[SECRET]", text)


def clean_report(text: str) -> str:
    """Normalize whitespace, redact sensitive data and truncate very long logs."""
    text = text.replace("\r\n", "\n")
    text = _WS.sub(" ", text)
    text = _BLANKS.sub("\n\n", text).strip()
    text = redact_pii(text)
    if len(text) > MAX_CHARS:
        half = MAX_CHARS // 2
        text = text[:half] + "\n...[truncated]...\n" + text[-half:]
    return text
