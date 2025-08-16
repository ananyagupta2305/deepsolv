# competitor.py
import re

# Hardcoded mapping for demo (in prod, use Google Search API or SerpAPI)
# competitor.py
COMPETITOR_MAP = {
    "colourpop.com": ["jeffreestarcosmetics.com", "morphebrushes.com"],
    "fashionnova.com": ["prettylittlething.com", "boohoo.com"],
    "gymshark.com": ["lululemon.com", "nike.com"],
    "cupshe.com": ["swimoutlet.com", "vikinis.com"],
}

def get_competitors(website: str) -> list:
    domain = website.split("//")[-1].split("/")[0].lower()
    for key, competitors in COMPETITOR_MAP.items():
        if key in domain:
            return competitors
    return []