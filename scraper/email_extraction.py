"""Reine, ohne Netzwerk testbare Parsing-Funktionen für die Lead-Pipeline:
E-Mail-Extraktion und Website-Auflösung aus gescraptem Seiteninhalt
(Markdown/Text). firecrawl-Aufrufe bleiben in pipeline.py, damit diese Logik
ohne Firecrawl-Credits getestet werden kann.
"""

import re
from urllib.parse import urljoin, urlparse

GENERIC_BLOCKLIST = ["example", "spam", "meinungsmeister", "webmaster@", "sentry.io", "wixpress.com"]

# z.B. "info [at] firma.de", "info(at)firma.de", "info at firma dot de"
_OBFUSCATED_PATTERN = re.compile(
    r"([\w.\-]+)\s*[\[\(]?\s*(?:@|at)\s*[\]\)]?\s*([\w.\-]+)\s*[\[\(]?\s*dot\s*[\]\)]?\s*(de|com|net|org|info|eu)\b",
    re.IGNORECASE,
)

_MAILTO_PATTERN = re.compile(r'mailto:([\w.\-+]+@[\w.\-]+\.\w{2,})', re.IGNORECASE)
_PLAIN_EMAIL_PATTERN = re.compile(r'[\w.\-]+@[\w.\-]+\.\w{2,}')


def _is_blocked(email):
    e = email.lower()
    return any(x in e for x in GENERIC_BLOCKLIST)


def find_emails_in_text(text):
    """Findet E-Mail-Adressen in Text/Markdown, in Prioritätsreihenfolge:
    1. mailto:-Links (höchste Verlässlichkeit)
    2. normale Klartext-Adressen
    3. deobfuskierte Adressen ("info [at] firma.de")
    Gibt eine Liste eindeutiger, nicht geblockter Adressen zurück, in dieser
    Prioritätsreihenfolge.
    """
    if not text:
        return []

    found = []
    seen = set()

    for pattern in (_MAILTO_PATTERN, _PLAIN_EMAIL_PATTERN):
        for m in pattern.findall(text):
            email = m.strip().rstrip('.,;')
            key = email.lower()
            if key not in seen and not _is_blocked(email):
                seen.add(key)
                found.append(email)

    for m in _OBFUSCATED_PATTERN.finditer(text):
        local, domain, tld = m.groups()
        email = f"{local}@{domain}.{tld}"
        key = email.lower()
        if key not in seen and not _is_blocked(email):
            seen.add(key)
            found.append(email)

    return found


def best_email(text):
    """Gibt die wahrscheinlichste E-Mail-Adresse aus einem Text zurück, oder ''."""
    emails = find_emails_in_text(text)
    return emails[0] if emails else ""


# Reihenfolge nach Trefferwahrscheinlichkeit: Startseite zuerst (viele kleine
# Websites zeigen die Adresse direkt im Footer), dann die klassischen
# Rechtsseiten, dann zwei zusätzliche gängige Pfad-Varianten.
EMAIL_SEARCH_PATHS = [
    "",  # Startseite
    "/impressum",
    "/Impressum",
    "/kontakt",
    "/Kontakt",
    "/impressum.html",
    "/ueber-uns",
]

CONTACT_LINK_HINTS = (
    "impressum", "kontakt", "contact", "about", "ueber-uns", "über-uns",
    "datenschutz", "legal",
)


def contact_links_from_homepage(homepage_html, homepage_url, max_links=8):
    """Find likely contact/legal links on a company's homepage.

    Only same-host HTTP(S) links whose URL or visible label contains a contact
    hint are returned. This improves coverage for sites with localized or
    non-standard paths without guessing an email address or crawling broadly.
    """
    if not homepage_html or not homepage_url:
        return []
    try:
        origin = urlparse(homepage_url)
        host = origin.netloc.lower().removeprefix("www.")
    except Exception:
        return []

    candidates = []
    seen = set()
    for href, label in re.findall(
        r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
        homepage_html, flags=re.IGNORECASE | re.DOTALL,
    ):
        absolute = urljoin(homepage_url, href).split("#", 1)[0].rstrip("/")
        parsed = urlparse(absolute)
        target_host = parsed.netloc.lower().removeprefix("www.")
        haystack = f"{parsed.path} {parsed.query} {re.sub(r'<[^>]+>', ' ', label)}".lower()
        if (parsed.scheme not in ("http", "https") or target_host != host or
                not any(hint in haystack for hint in CONTACT_LINK_HINTS) or
                absolute in seen):
            continue
        seen.add(absolute)
        candidates.append(absolute)
        if len(candidates) >= max_links:
            break
    return candidates

_GSBIZ_LINK_PATTERN = re.compile(r'\]\((https?://(?:www\.)?gelbeseiten\.de/gsbiz/[^)\s]+)\)', re.IGNORECASE)
_PROFILE_WEBSITE_PATTERN = re.compile(r'\[(?:Website|Webseite)\]\((https?://[^\s")]+)', re.IGNORECASE)


def find_gelbeseiten_profile_url(details_text):
    """Findet den Link zur GelbeSeiten-Profilseite eines Listings innerhalb
    des Detail-Textblocks (das schliessende `](...)` des Bild+Name-Links)."""
    if not details_text:
        return ""
    m = _GSBIZ_LINK_PATTERN.search(details_text)
    return m.group(1) if m else ""


def is_real_company_website(url):
    """False für leer/None und für alles auf gelbeseiten.de -- eine
    GelbeSeiten-URL ist niemals die echte Website eines Unternehmens und darf
    nie an find_email()/guess_domain_email() weitergereicht werden (sonst
    wird faelschlich z.B. info@gelbeseiten.de "gefunden")."""
    if not url:
        return False
    return 'gelbeseiten.de' not in url.lower()


def find_real_website_on_profile_page(profile_markdown):
    """Findet die echte externe Firmen-Website auf einer gescrapten
    GelbeSeiten-Profilseite. Der "Webseite"-Button der Kategorie-Uebersichtsseite
    hat keinen statischen Link (JS-gesteuert) -- auf der Profilseite des
    einzelnen Unternehmens steht der echte Link aber als normaler
    Markdown-Link "[Website](https://...)"."""
    if not profile_markdown:
        return ""
    m = _PROFILE_WEBSITE_PATTERN.search(profile_markdown)
    return m.group(1).rstrip('/') if m else ""
