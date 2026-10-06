#!/usr/bin/env python3
"""Build an Alfred snippet pack containing every Unicode emoji.

Data comes from two public sources, fetched fresh and cached under .cache/:
  * Unicode emoji-test.txt: the authoritative emoji list and official names.
  * GitHub gemoji db/emoji.json: familiar shortcodes (:joy:, :+1:).

Each emoji gets one snippet per gemoji alias, or one snippet named after its
official Unicode name when gemoji has no alias. The pack's keyword prefix and
suffix are both ":", so a snippet whose keyword is "joy" expands from ":joy:".

Usage:
  python3 generate.py                      # dist/Emoji Pack Complete.alfredsnippets
  python3 generate.py --skin-tones         # also include skin-tone variants
  python3 generate.py --folder DIR         # also write loose JSON files into DIR
  python3 generate.py --offline            # use .cache/ only, no network
"""
import argparse
import io
import json
import plistlib
import re
import sys
import urllib.request
import uuid
import zipfile
from pathlib import Path

UNICODE_URL = "https://unicode.org/Public/emoji/latest/emoji-test.txt"
GEMOJI_URL = "https://raw.githubusercontent.com/github/gemoji/master/db/emoji.json"
SKIN_TONES = range(0x1F3FB, 0x1F400)
UID_NAMESPACE = uuid.UUID("6f1c2f0e-6a41-4c52-9d0e-5b7a2c8d4e11")
BUNDLE_NAME = "Emoji Pack Complete.alfredsnippets"
CACHE = Path(__file__).parent / ".cache"

TEST_LINE = re.compile(
    r"^([0-9A-F ]+?)\s*;\s*fully-qualified\s*#\s*\S+\s+E[\d.]+\s+(.*)$"
)


def norm(emoji):
    """Strip variation selectors so Unicode and gemoji spellings compare equal."""
    return emoji.replace("️", "")


def fetch(url, filename, offline):
    path = CACHE / filename
    if offline:
        return path.read_text(encoding="utf-8")
    CACHE.mkdir(exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as resp:
        text = resp.read().decode("utf-8")
    path.write_text(text, encoding="utf-8")
    return text


def parse_unicode(text, skin_tones):
    """Return [(emoji, official name)] for every fully-qualified emoji."""
    out = []
    for line in text.splitlines():
        m = TEST_LINE.match(line)
        if not m:
            continue
        cps = [int(x, 16) for x in m.group(1).split()]
        if not skin_tones and any(c in SKIN_TONES for c in cps):
            continue
        out.append(("".join(map(chr, cps)), m.group(2)))
    return out


def load_gemoji(text):
    """Return {normalised emoji: [aliases]}."""
    return {norm(e["emoji"]): list(e.get("aliases", [])) for e in json.loads(text)}


def snake(name):
    name = name.lower().replace("’", "").replace("'", "")
    return re.sub(r"[^a-z0-9]+", "_", name).strip("_")


def build(emoji_list, gemoji):
    """Return a list of snippet dicts with unique keywords."""
    used = set()
    for emoji, _ in emoji_list:
        used.update(gemoji.get(norm(emoji), []))
    snippets = []
    for emoji, name in emoji_list:
        keywords = list(gemoji.get(norm(emoji), []))
        if not keywords:
            kw = base = snake(name)
            n = 2
            while kw in used:
                kw = f"{base}_{n}"
                n += 1
            used.add(kw)
            keywords = [kw]
        for kw in keywords:
            uid = str(uuid.uuid5(UID_NAMESPACE, f"{emoji}|{kw}")).upper()
            snippets.append({
                "snippet": emoji,
                "uid": uid,
                "name": f"{emoji} :{kw}: ({name})",
                "keyword": kw,
            })
    return snippets


def info_plist():
    return plistlib.dumps({"snippetkeywordprefix": ":", "snippetkeywordsuffix": ":"})


def snippet_json(snip):
    return json.dumps({"alfredsnippet": snip}, indent=2, ensure_ascii=False)


def write_bundle(snippets, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("info.plist", info_plist())
        for s in snippets:
            z.writestr(f"{s['uid']}.json", snippet_json(s))
    path.write_bytes(buf.getvalue())


def write_folder(snippets, folder):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "info.plist").write_bytes(info_plist())
    for s in snippets:
        (folder / f"{s['uid']}.json").write_text(snippet_json(s), encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build an Alfred snippet pack containing every Unicode emoji.")
    ap.add_argument("--skin-tones", action="store_true", help="include skin-tone variants")
    ap.add_argument("--folder", type=Path, help="also write loose JSON files here")
    ap.add_argument("--out", type=Path, default=Path("dist") / BUNDLE_NAME)
    ap.add_argument("--offline", action="store_true", help="read .cache/ only")
    args = ap.parse_args(argv)

    unicode_text = fetch(UNICODE_URL, "emoji-test.txt", args.offline)
    gemoji_text = fetch(GEMOJI_URL, "emoji.json", args.offline)
    emoji_list = parse_unicode(unicode_text, args.skin_tones)
    snippets = build(emoji_list, load_gemoji(gemoji_text))

    keywords = [s["keyword"] for s in snippets]
    assert len(keywords) == len(set(keywords)), "duplicate keywords"
    write_bundle(snippets, args.out)
    if args.folder:
        write_folder(snippets, args.folder)
    print(f"{len(emoji_list)} emoji, {len(snippets)} snippets -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
