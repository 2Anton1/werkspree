"""Create branded copies of the four Klarraum workshop documents.

The originals are never modified. Each output receives the selected Signal
mark directly before its first title; this is robust across the source files.
"""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor
from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "dokumente" / "originale"
OUTPUT = ROOT / "dokumente" / "gebrandete"
CONCEPT = ROOT / "assets" / "logo-signal-concept.png"
LOGO = ROOT / "assets" / "logo-signal-header.png"


def prepare_logo() -> None:
    """Crop the selected transparent concept to a compact header-ready PNG."""
    image = Image.open(CONCEPT).convert("RGBA")
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        background = Image.new("RGBA", image.size, (0, 0, 0, 255))
        bbox = ImageChops.difference(image, background).getbbox()
    if bbox is None:
        raise ValueError("Selected logo concept has no visible content.")
    image.crop(bbox).save(LOGO)


def add_header(document: Document, mark_after_title: bool = False) -> None:
    # Some supplied templates suppress first-page headers. Clear inherited
    # headers and place the brand in the title itself instead.
    for section in document.sections:
        header = section.header
        header.is_linked_to_previous = False
        header.paragraphs[0].clear()

    title = document.paragraphs[0]
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    title.paragraph_format.left_indent = Cm(0.2)
    logo_run = title.add_run()
    logo_run.add_picture(str(LOGO), width=Cm(0.52))
    if mark_after_title:
        spacer = title.add_run("  ")
        title._p.remove(logo_run._r)
        title._p.remove(spacer._r)
        title._p.append(spacer._r)
        title._p.append(logo_run._r)
    else:
        spacer = title.add_run("  ")
        title._p.remove(logo_run._r)
        title._p.remove(spacer._r)
        title._p.insert(0, spacer._r)
        title._p.insert(0, logo_run._r)


def main() -> None:
    prepare_logo()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for source in sorted(SOURCE.glob("*.docx")):
        document = Document(source)
        add_header(document, mark_after_title="Schulungsleitfaden" in source.name)
        target = OUTPUT / f"Klarraum_Gesundheit_{source.name}"
        document.save(target)
        print(target)


if __name__ == "__main__":
    main()
