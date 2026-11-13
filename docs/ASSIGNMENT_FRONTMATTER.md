# Assignment frontmatter reference

Individual assignment files (`Level N - Title.md`, matched by
`ASSIGNMENT_FILENAME_REGEX` in `piggy/__init__.py`) carry their own metadata
as a YAML frontmatter block at the top of the file, optionally extended by a
sibling `.oink` file. This is a separate mechanism from folder-level
`meta.json` — see [METADATA.md](METADATA.md) for that.

```markdown
---
title: Min Oppgave
difficulty: 3
thumbnail: media/01_header
description: En kort beskrivelse av oppgaven.
---

# Min Oppgave

Oppgavetekst her...
```

There is no schema validation. Frontmatter is parsed with `yaml.unsafe_load`
(`piggy/piggybank.py`, `get_frontmatter_from_file`); invalid YAML is caught
and logged, and the file falls back to an empty frontmatter dict plus a
derived title.

## Property reference

| Property | Type | Required | Meaning |
|---|---|---|---|
| `title` | string | Effectively required | Display title. If omitted, falls back to the first `# heading` in the file, then to the filename. |
| `difficulty` | integer (1–5 in practice) | Optional | Drives the difficulty icon (`static/img/difficulties/1.png`…`5.png`); values `>5` are clamped to 5, values `<=0` hide the icon. |
| `thumbnail` | string (relative path, no extension) | Optional | Defaults to `media/header` if omitted. Resolved to a full image URL at render time. |
| `thumbnail_title` | string | Optional | Text drawn on the generated fallback thumbnail (used when no thumbnail image exists). Defaults to `title`, so set this to keep the page title and the thumbnail text separate. |
| `description` | string | Optional | Used for card descriptions and as an `og:description`/`twitter:description` fallback. |
| `summary` | string | Optional | If omitted, auto-generated from the first ~200 characters of the rendered HTML body (`piggy/caching.py`, `generate_summary_from_mkdocs_html`). Used as a lower-priority `og:description` fallback than `description`. |
| `oinkdata` | object | Optional, via `.oink` only | Not settable from frontmatter itself — only comes from a sibling `.oink` JSON file (see below). Only `oinkdata.summary` is currently read anywhere, as an `og:description` fallback between `description` and `summary`. |
| `relevant_pages` | list of strings | Optional | Other pages to show as a "Relevante sider" button row under the page title. Each entry is a `[[wikilink]]` to another assignment file (resolved by turtleconverter just like links in the body; add `\|Label` to set the button text, otherwise the file name is shown) or a quoted markdown link `"[Label](/main/...)"` (unquoted, YAML reads the `[...]` as a list). Entries that don't end up as a link are skipped. Translations always show the list of their original document, see [Translations](#translations). |

### `relevant_pages` example

```yaml
relevant_pages:
  - [[GitHub Desktop Level 1 - Installasjon|GitHub Desktop]]
  - [[uv Level 1 - Installasjon|📦️ uv (pakkehåndterer)]]
  - "[Python 2](/main/VG1/IM/Konseptutvikling_og_Programmering/Programmering_-_Python_02)"
```

### Shortlinks in `relevant_pages`

A shortlink copied with the "Kopier lenke" button can be pasted as an entry
on its own, and the button is titled after the page it points to. As a
markdown link it keeps its own label. Either way the button links straight to
the page instead of going through the `/s/` redirect (`piggy/shortlinks.py`).
The `https://piggy.iktim.no/s/<code>`, `/s/<code>` and `s/<code>` forms all work;
an unknown code on its own is skipped.

```yaml
relevant_pages:
  - https://piggy.iktim.no/s/KDFJtPht
  - "[YFF-prosjektene](s/KDFJtPht)"
```

## `.oink` sidecar files

A file named `Level N - Title.oink` next to `Level N - Title.md` (JSON
format) is loaded and merged **over** the markdown frontmatter. Any key it
sets overrides the same key from the frontmatter block. It's intended for
metadata that shouldn't live inside the markdown file itself.

The `uuid` key is used as the assignment's shortlink identity. If it is
missing, a deterministic UUID is generated from the normalized path.

The `referenced_by` key is written by the piggybank pipeline and lists the
pages whose `relevant_pages` link to this page, grouped by their folder. It
is shown as a "Brukt i" row under the page title: one button per other
folder, linking to that folder's first public referencing page
(`piggy/piggybank.py`, `get_referenced_by`). Translations show the row of
their original document.

## Translations

A translated version of an assignment can be placed at
`translations/<lang-code>/Level N - Title.md` (same filename, sibling
`translations/` folder next to the original). Each translation file has its
own independent frontmatter block, parsed the same way. If a translation has
no `.oink` file of its own but the original does, the original's `.oink` data
is inherited (with `oinkdata` cleared) rather than duplicated per language.

`relevant_pages` is the exception to the independent frontmatter: turtletranslate
never translates it, and a translation can lag behind its original, so a
translated page always renders the original document's `relevant_pages`
(`piggy/caching.py`, `inherit_frontmatter_entry`), whatever its own file says.
