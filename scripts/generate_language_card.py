#!/usr/bin/env python3
"""Genere languages.svg a partir des langages des depots publics.

Aucune dependance externe, aucun service tiers a l'affichage : le SVG est
commite dans le depot, donc il ne peut pas tomber en panne.

Usage : GITHUB_TOKEN=... python scripts/generate_language_card.py
"""
import json
import os
import sys
import urllib.error
import urllib.request

USER = os.environ.get("GITHUB_USER", "Rayan-Madi")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.environ.get("OUTPUT", "languages.svg")

TOP_N = 5
MIN_SHARE = 0.02  # ignore ce qui pese moins de 2 %, sinon la legende se remplit de bruit

# Couleurs Linguist, lisibles sur fond clair comme sur fond sombre.
COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "CSS": "#663399",
    "HTML": "#e34c26",
    "PHP": "#4F5D95",
    "Java": "#b07219",
    "PowerShell": "#012456",
    "Shell": "#89e051",
    "C": "#888888",
    "COBOL": "#005ca5",
    "Dockerfile": "#384d54",
    "Batchfile": "#C1F12E",
}
FALLBACK = "#8b949e"


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", f"{USER}-language-card")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def collect():
    """Somme les octets par langage sur tous les depots publics non forkes."""
    totals = {}
    page = 1
    while True:
        repos = api(f"/users/{USER}/repos?per_page=100&type=owner&page={page}")
        if not repos:
            break
        for repo in repos:
            if repo.get("fork") or repo.get("archived"):
                continue
            try:
                langs = api(f"/repos/{USER}/{repo['name']}/languages")
            except urllib.error.HTTPError:
                continue
            for lang, size in langs.items():
                totals[lang] = totals.get(lang, 0) + size
        page += 1
    return totals


def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(totals):
    grand = sum(totals.values())
    if not grand:
        raise SystemExit("Aucun langage detecte.")

    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    kept = [(l, s) for l, s in ranked if s / grand >= MIN_SHARE][:TOP_N]
    shown = sum(s for _, s in kept)

    width, bar_y, bar_h, radius = 480, 46, 10, 5
    rows = (len(kept) + 1) // 2
    height = bar_y + bar_h + 20 + rows * 21

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Langages les plus utilises">',
        '<style>'
        '.t{font:600 15px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;fill:#8b949e}'
        '.s{font:400 11px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;fill:#8b949e}'
        '.l{font:400 12px -apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif;fill:#8b949e}'
        '</style>',
        '<text x="0" y="16" class="t">Most used languages</text>',
        '<text x="0" y="32" class="s">Across public repositories, by bytes of code</text>',
        f'<clipPath id="r"><rect x="0" y="{bar_y}" width="{width}" height="{bar_h}" '
        f'rx="{radius}"/></clipPath>',
        f'<g clip-path="url(#r)">',
    ]

    x = 0.0
    for lang, size in kept:
        seg = width * size / shown
        parts.append(
            f'<rect x="{x:.2f}" y="{bar_y}" width="{seg:.2f}" height="{bar_h}" '
            f'fill="{COLORS.get(lang, FALLBACK)}"/>'
        )
        x += seg
    parts.append("</g>")

    for i, (lang, size) in enumerate(kept):
        col, row = i % 2, i // 2
        lx = col * (width // 2)
        ly = bar_y + bar_h + 26 + row * 21
        pct = 100 * size / grand
        parts.append(
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" '
            f'fill="{COLORS.get(lang, FALLBACK)}"/>'
        )
        parts.append(
            f'<text x="{lx + 17}" y="{ly}" class="l">{escape(lang)} {pct:.1f}%</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main():
    totals = collect()
    svg = render(totals)
    previous = ""
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as fh:
            previous = fh.read()
    if svg == previous:
        print("Inchange.")
        return
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"Ecrit {OUT}")


if __name__ == "__main__":
    sys.exit(main())
