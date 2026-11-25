#!/usr/bin/env python3
"""Draw a one-image summary of the world news of 26 November 2026.

Running ``python3 main.py`` regenerates ``news-2026-11-26.png``
deterministically: no network access, no randomness, no wall-clock time,
system DejaVu fonts with a built-in fallback. The PNG is written to the
directory named by MAKEFUN_OUTPUT_DIR when that variable is set (the
grader's /output), otherwise next to this script.

The stories were compiled from wire reporting dated 26 November 2026
(see README.md for the full source list for every panel).
"""

import os

from PIL import Image, ImageDraw, ImageFont

# --------------------------------------------------------------------------
# Canvas and palette
# --------------------------------------------------------------------------
WIDTH, HEIGHT = 1600, 1200
MARGIN = 48

BG = (10, 14, 22)            # near-black navy
PANEL_BG = (20, 27, 40)      # card background
PANEL_EDGE = (43, 54, 74)    # card border
INK = (238, 242, 247)        # headline white
BODY = (178, 190, 205)       # summary grey-blue
MUTED = (120, 134, 152)      # footer / kicker grey
GOLD = (240, 193, 75)        # header accent

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
F_SANS = os.path.join(FONT_DIR, "DejaVuSans.ttf")
F_BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")


def load_font(path, size):
    """Load a TrueType font, falling back to PIL's built-in font."""
    try:
        return ImageFont.truetype(path, size)
    except (OSError, IOError):
        return ImageFont.load_default(size=size)


def font(path, size):
    return load_font(path, size)


# --------------------------------------------------------------------------
# The day's stories: (category, accent colour, headline, summary, source tag)
# --------------------------------------------------------------------------
FEATURED = (
    "MARKETS — TOP STORY",
    (248, 113, 113),
    "Nasdaq plunges 4% as AI rout rattles Wall Street",
    "Chip stocks led a broad sell-off — Nvidia fell about 8.7% and the "
    "Nasdaq 100 briefly sat 20% below its record high — as doubts over "
    "the debt-fuelled AI boom met fresh US tariffs. The Nasdaq and S&P 500 "
    "are on track for their worst November since 2008.",
    "Reuters · AP",
)

STORIES = [
    (
        "TRADE",
        (251, 191, 36),
        "US unveils sweeping new tariffs on 14 partners",
        "Washington's Section 301 probe into \"excess capacity\" paves the "
        "way for fresh duties on China, the EU and others — China faces a "
        "20% levy on top of roughly 25% already in place.",
        "Reuters · WSJ",
    ),
    (
        "WAR",
        (248, 113, 113),
        "Russia's own figures show nearly 500,000 war dead",
        "Leaked Rosstat mortality data analysed by the BBC puts Russian "
        "military deaths in Ukraine at at least 490,334 since February "
        "2022 — past 700,000 once the missing are counted.",
        "BBC · The Guardian",
    ),
    (
        "EGYPT",
        (251, 146, 60),
        "Fuel tanker fire kills at least 31 on Cairo Ring Road",
        "A fuel tanker overturned above Tunnel 10 in Giza's Al-Warraq "
        "district and exploded, engulfing nearby traffic. At least 31 "
        "people were killed and over 20 injured.",
        "AP · Reuters",
    ),
    (
        "ISRAEL",
        (167, 139, 250),
        "Judges urge dropping Netanyahu bribery case",
        "Jerusalem District Court judges recommended prosecutors drop the "
        "bribery charge in Case 4000 and reconsider Case 2000 — a major "
        "boost for the prime minister, though no charge has been "
        "dismissed yet.",
        "Reuters · CNN",
    ),
    (
        "SPACE",
        (56, 189, 248),
        "Hera reveals stadium-sized crater on Dimorphos",
        "ESA's Hera mission showed the asteroid moonlet flattened by "
        "NASA's 2022 DART impact into a crater spanning its whole width — "
        "and left tumbling chaotically, ringed by hundreds of small "
        "boulders.",
        "ESA · Sky & Telescope",
    ),
    (
        "COLOMBIA",
        (74, 222, 128),
        "20 hostages freed as police storm Cartagena supermarket",
        "Security forces ended a 17-hour siege at an Éxito store in La "
        "Castellana, freeing the 20 remaining hostages and killing one "
        "gunman. Ten others had been released the day before.",
        "AP",
    ),
]

FOOTER = ("Sources: Reuters · AP · BBC · The Guardian · CNN · ESA · WSJ"
          "   |   Compiled from reporting dated 26 November 2026")


# --------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------
def wrap(draw, text, fnt, max_width):
    """Greedy word wrap measured with PIL so nothing overflows its panel."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = word if not current else current + " " + word
        if draw.textlength(trial, font=fnt) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_lines(draw, xy, lines, fnt, fill, leading):
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += leading
    return y


def fit_body(draw, text, max_width, start_y, max_bottom, sizes=(22, 21, 20, 19)):
    """Wrap ``text`` at the largest size whose lines end above ``max_bottom``.

    Returns (lines, font, leading, end_y). This is the overflow guard: a
    panel can never spill into the source tag pinned at its bottom edge.
    """
    for size in sizes:
        fnt = font(F_SANS, size)
        leading = size + 7
        lines = wrap(draw, text, fnt, max_width)
        end_y = start_y + leading * len(lines)
        if end_y <= max_bottom:
            return lines, fnt, leading, end_y
    raise ValueError("summary does not fit its panel at any size")


# --------------------------------------------------------------------------
# Panels
# --------------------------------------------------------------------------
def panel(draw, box, accent, radius=18):
    draw.rounded_rectangle(box, radius=radius, fill=PANEL_BG,
                           outline=PANEL_EDGE, width=2)
    x0, y0, x1, _ = box
    # accent bar along the top edge of the card
    draw.rounded_rectangle([x0, y0, x1, y0 + 10], radius=radius, fill=accent)
    draw.rectangle([x0, y0 + 5, x1, y0 + 10], fill=accent)


def story_card(draw, box, category, accent, headline, summary, source):
    panel(draw, box, accent)
    x0, y0, x1, y1 = box
    pad = 26
    inner_w = (x1 - x0) - 2 * pad
    source_y = y1 - 40
    y = y0 + 30
    draw.text((x0 + pad, y), category, font=font(F_BOLD, 21), fill=accent)
    y += 36
    head_lines = wrap(draw, headline, font(F_BOLD, 27), inner_w)
    y = draw_lines(draw, (x0 + pad, y), head_lines, font(F_BOLD, 27), INK, 34)
    y += 8
    lines, fnt, leading, _ = fit_body(draw, summary, inner_w, y, source_y - 12,
                                      sizes=(20, 19, 18))
    draw_lines(draw, (x0 + pad, y), lines, fnt, BODY, leading)
    draw.text((x0 + pad, source_y), source.upper(),
              font=font(F_BOLD, 16), fill=MUTED)


def featured_card(draw, box, category, accent, headline, summary, source):
    panel(draw, box, accent)
    x0, y0, x1, y1 = box
    pad = 34
    inner_w = (x1 - x0) - 2 * pad
    source_y = y1 - 44
    y = y0 + 30
    draw.text((x0 + pad, y), category, font=font(F_BOLD, 24), fill=accent)
    y += 40
    head_lines = wrap(draw, headline, font(F_BOLD, 46), inner_w)
    y = draw_lines(draw, (x0 + pad, y), head_lines, font(F_BOLD, 46), INK, 56)
    y += 8
    lines, fnt, leading, _ = fit_body(draw, summary, inner_w, y,
                                      source_y - 12, sizes=(25, 24, 23, 22))
    draw_lines(draw, (x0 + pad, y), lines, fnt, BODY, leading)
    draw.text((x0 + pad, source_y), source.upper(),
              font=font(F_BOLD, 17), fill=MUTED)


# --------------------------------------------------------------------------
# Page composition
# --------------------------------------------------------------------------
OUTPUT_NAME = "news-2026-11-26.png"


def output_path():
    """Where the PNG goes: MAKEFUN_OUTPUT_DIR in the grader, else here."""
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if out_dir:
        return os.path.join(out_dir, OUTPUT_NAME)
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, OUTPUT_NAME)


def main():
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    content_w = WIDTH - 2 * MARGIN

    # Header -------------------------------------------------------------
    y = 30
    draw.text((MARGIN, y), "WORLD NEWS · ONE IMAGE",
              font=font(F_BOLD, 26), fill=GOLD)
    date_text = "THURSDAY, 26 NOVEMBER 2026"
    draw.text((WIDTH - MARGIN - draw.textlength(date_text, font=font(F_BOLD, 26)), y),
              date_text, font=font(F_BOLD, 26), fill=MUTED)
    y += 40
    draw.text((MARGIN, y), "The World on 26 November",
              font=font(F_BOLD, 62), fill=INK)
    y += 78
    draw.text((MARGIN, y),
              "The day's biggest stories — markets, trade, war, space and more — in a single frame.",
              font=font(F_SANS, 26), fill=BODY)
    y += 34
    draw.rectangle([MARGIN, y, WIDTH - MARGIN, y + 3], fill=GOLD)
    y += 8

    # Featured story ------------------------------------------------------
    featured_h = 280
    featured_card(draw, [MARGIN, y, WIDTH - MARGIN, y + featured_h], *FEATURED)
    y += featured_h + 12

    # Grid: two rows of three --------------------------------------------
    gap = 12
    card_w = (content_w - 2 * gap) // 3
    card_h = 330
    for row in range(2):
        for col in range(3):
            story = STORIES[row * 3 + col]
            x0 = MARGIN + col * (card_w + gap)
            story_card(draw, [x0, y, x0 + card_w, y + card_h], *story)
        y += card_h + gap

    # Footer ---------------------------------------------------------------
    draw.text((MARGIN, HEIGHT - 36), FOOTER, font=font(F_SANS, 18), fill=MUTED)

    path = output_path()
    img.save(path)
    print("wrote", path, img.size)


if __name__ == "__main__":
    main()
