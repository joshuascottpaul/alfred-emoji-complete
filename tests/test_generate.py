import json
import plistlib
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import generate  # noqa: E402

EMOJI_TEST = """\
# group: Smileys & Emotion
1F600                                                  ; fully-qualified     # \U0001F600 E1.0 grinning face
1FAE0                                                  ; fully-qualified     # \U0001FAE0 E14.0 melting face
263A FE0F                                              ; fully-qualified     # ☺️ E0.6 smiling face
263A                                                   ; unqualified         # ☺ E0.6 smiling face
# group: People & Body
1F44B                                                  ; fully-qualified     # \U0001F44B E0.6 waving hand
1F44B 1F3FD                                            ; fully-qualified     # \U0001F44B\U0001F3FD E1.0 waving hand: medium skin tone
"""

GEMOJI = json.dumps([
    {"emoji": "\U0001F600", "aliases": ["grinning"]},
    {"emoji": "☺️", "aliases": ["relaxed", "smiling_face"]},
    {"emoji": "\U0001F44B", "aliases": ["wave"]},
])


class ParseTests(unittest.TestCase):
    def test_only_fully_qualified_and_no_skin_tones_by_default(self):
        got = generate.parse_unicode(EMOJI_TEST, skin_tones=False)
        self.assertEqual([n for _, n in got], ["grinning face", "melting face", "smiling face", "waving hand"])

    def test_skin_tones_opt_in(self):
        got = generate.parse_unicode(EMOJI_TEST, skin_tones=True)
        self.assertIn("waving hand: medium skin tone", [n for _, n in got])


class BuildTests(unittest.TestCase):
    def setUp(self):
        emoji = generate.parse_unicode(EMOJI_TEST, skin_tones=False)
        self.snips = generate.build(emoji, generate.load_gemoji(GEMOJI))

    def test_one_snippet_per_alias_and_fallback_to_official_name(self):
        kws = [s["keyword"] for s in self.snips]
        self.assertEqual(kws, ["grinning", "melting_face", "relaxed", "smiling_face", "wave"])

    def test_snippet_text_is_fully_qualified_emoji(self):
        relaxed = next(s for s in self.snips if s["keyword"] == "relaxed")
        self.assertEqual(relaxed["snippet"], "☺️")

    def test_fallback_keyword_never_collides_with_an_alias(self):
        emoji = [("A", "smiling face"), ("B", "smiling face")]
        snips = generate.build(emoji, {"A": ["smiling_face"]})
        kws = [s["keyword"] for s in snips]
        self.assertEqual(len(kws), len(set(kws)))
        self.assertEqual(kws, ["smiling_face", "smiling_face_2"])

    def test_uids_are_stable_across_builds(self):
        emoji = generate.parse_unicode(EMOJI_TEST, skin_tones=False)
        again = generate.build(emoji, generate.load_gemoji(GEMOJI))
        self.assertEqual([s["uid"] for s in self.snips], [s["uid"] for s in again])


class BundleTests(unittest.TestCase):
    def test_bundle_layout_matches_alfred_format(self):
        emoji = generate.parse_unicode(EMOJI_TEST, skin_tones=False)
        snips = generate.build(emoji, generate.load_gemoji(GEMOJI))
        tmp = Path(self._testMethodName + ".alfredsnippets")
        try:
            generate.write_bundle(snips, tmp)
            with zipfile.ZipFile(tmp) as z:
                names = z.namelist()
                self.assertIn("info.plist", names)
                self.assertEqual(len([n for n in names if n.endswith(".json")]), len(snips))
                self.assertTrue(all("/" not in n for n in names), "files must sit at the zip root")
                plist = plistlib.loads(z.read("info.plist"))
                self.assertEqual(plist, {"snippetkeywordprefix": ":", "snippetkeywordsuffix": ":"})
                body = json.loads(z.read(f"{snips[0]['uid']}.json"))
                self.assertEqual(set(body["alfredsnippet"]), {"snippet", "uid", "name", "keyword"})
        finally:
            tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
