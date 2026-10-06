# Alfred Emoji Pack (Complete)

Every Unicode emoji as an [Alfred](https://www.alfredapp.com/) snippet, typed the way Slack does it: `:joy:` becomes 😂.

- **1,923 emoji** (Unicode 18.0, base emoji without skin-tone variants), **1,966 snippets**. Emoji with several familiar shortcodes get one snippet per shortcode, so `:+1:` and `:thumbsup:` both give 👍.
- Shortcodes are the standard [gemoji](https://github.com/github/gemoji) ones. Emoji that gemoji doesn't cover yet (newer Unicode releases) use their official Unicode name in snake case, for example `:melting_face:`.
- Rebuilt from the Unicode and gemoji data by one script, so a new Unicode release is one command.

## Install

1. Download `Emoji Pack Complete.alfredsnippets` from the [latest release](../../releases/latest) (or from `dist/`).
2. Double-click it. Alfred imports it as the collection **Emoji Pack Complete**.
3. In Alfred Preferences, Features, Snippets, turn on "Automatically expand snippets by keyword" if you want `:joy:` to expand as you type. Otherwise open the snippet viewer and search for `joy`.

Needs the Alfred Powerpack. If you already have another emoji collection that uses the `:` prefix, remove it first so the same keyword doesn't appear twice.

## Rebuild

```sh
python3 generate.py              # writes dist/Emoji Pack Complete.alfredsnippets
python3 generate.py --skin-tones # also include skin-tone variants (about 4,000 more snippets)
python3 generate.py --offline    # reuse the cached source files in .cache/
python3 -m unittest discover -s tests
```

Standard library only, no dependencies. It downloads Unicode's `emoji-test.txt` and gemoji's `db/emoji.json`, then writes the bundle. Snippet ids are derived from the emoji and keyword, so rebuilding gives byte-stable files and clean diffs.

Each snippet is named like `😂 :joy: (face with tears of joy)`, so Alfred's "Name or Keyword" matching finds an emoji by its official name as well as its shortcode.

## Credits and licences

- Idea: [Joel Califa's Alfred Emoji Pack](https://www.joelcalifa.com/blog/alfred-emoji-snippet-pack/) showed how well Slack-style `:shortcodes:` work as Alfred snippets. This project uses none of that pack's code or data.
- Emoji list and official names: Unicode `emoji-test.txt`, © Unicode, Inc., used under the [Unicode License v3](https://www.unicode.org/license.txt).
- Shortcodes: [github/gemoji](https://github.com/github/gemoji), MIT licence, © GitHub, Inc.
- This repo's script and the generated pack: [MIT](LICENSE).
