from pathlib import Path
import re

text = Path("schopenhauer_cure_extracted.txt").read_text(encoding="utf-8")

patterns = [
    "foundations flimsy and false",
    "I don't know how to assess",
    "saved from the Schopenhauer cure",
    "wound is healed",
    "little experience with intimacy",
    "anger—which we see",
    "philosophy had healed me",
    "collective wisdom",
    "cure for my condition",
    "I owe my life to the genius",
    "I-thou",
    "Philip shared neither his frightening experiences",
    "living, breathing refutation",
    "failed to cure",
    "extreme discomfort levels in this group",
    "mansion of pure thought",
    "for the first time since entering the group, grinned",
    "What? Tony could not believe his ears",
    "three years later",
    "Philip Slate",
    "profession of philosophy",
    "A monster",
    "visitor to life",
    "pseudosolution",
    "Blessed isolation",
    "No handshake",
    "porcupines",
    "love is alien",
    "social world",
    "predator",
    "unlovable",
    "always the relationship",
    "great world spirits",
    "truth now",
    "new reality",
    "mercy ship",
    "Cancer cures psychoneurosis",
    "wounded healer",
    "know as much as possible",
    "automatic pilot",
    "face-to-face",
    "partner",
    "great deal you can contribute",
    "I could have loved you",
    "left feeling better",
    "sacred",
    "stable, persisting self",
    "more in touch",
]


def page_marker(index: int) -> str:
    start = text.rfind("--- PDF_PAGE ", 0, index)
    end = text.find("---", start + 4)
    if start == -1 or end == -1:
        return "?"
    return text[start:end].strip()


for pattern in patterns:
    print(f"\n### {pattern}")
    match = re.search(re.escape(pattern), text, re.IGNORECASE)
    if not match:
        print("NOT FOUND")
        continue
    start = max(0, match.start() - 750)
    end = min(len(text), match.end() + 950)
    snippet = re.sub(r"\s+", " ", text[start:end])
    print(page_marker(match.start()))
    print(snippet[:2000])
