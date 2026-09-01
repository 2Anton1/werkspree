"""Gemeinsame Qualitätsprüfung für erzeugte Microsites."""

import re


PLACEHOLDER_MARKERS = (
    "lorem ipsum",
    "max mustermann",
    "musterstraße",
    "hier steht",
    "```",
    "![gelbe seiten",
)


def is_valid_html(document: str, *, minimum_chars: int = 2200) -> bool:
    """Akzeptiert nur vollständige, sichtbare HTML-Dokumente."""
    if not document:
        return False
    lowered = document.lower()
    if len(document) < minimum_chars and 'name="robots" content="noindex,nofollow"' not in lowered:
        return False
    required = ("<html", "</html>", "<head", "</head>", "<body", "</body>")
    if any(marker not in lowered for marker in required):
        return False
    if lowered.count("<style") != lowered.count("</style>"):
        return False
    if lowered.count("<script") != lowered.count("</script>"):
        return False
    if re.search(r"\{\{[a-z0-9_]+\}\}", lowered) or any(marker in lowered for marker in PLACEHOLDER_MARKERS):
        return False
    body = re.search(r"<body[^>]*>([\s\S]*?)</body>", document, re.I)
    if not body or len(re.sub(r"<[^>]+>", " ", body.group(1)).strip()) < 80:
        return False
    return True
