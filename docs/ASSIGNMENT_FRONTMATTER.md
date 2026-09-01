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
| `description` | string | Optional | Used for card descriptions and as an `og:description`/`twitter:description` fallback. |
| `summary` | string | Optional | If omitted, auto-generated from the first ~200 characters of the rendered HTML body (`piggy/caching.py`, `generate_summary_from_mkdocs_html`). Used as a lower-priority `og:description` fallback than `description`. |
| `oinkdata` | object | Optional, via `.oink` only | Not settable from frontmatter itself — only comes from a sibling `.oink` YAML file (see below). Only `oinkdata.summary` is currently read anywhere, as an `og:description` fallback between `description` and `summary`. No `.oink` files currently exist in the content tree. Treat this as a planned/lightly-used feature. |
| `relevant_pages` | list of strings and/or objects | Optional | Paths to other piggybank pages to show as a "Relevante sider" button row under the page title. Each entry is either a plain page path string (e.g. `VG1/IM/Programmering/Generelt - 002 GitHub Desktop/GitHub Desktop Level 1 - Installasjon`, spaces are fine, optionally with a leading `/main/` as already used in in-body links), or an object `{path: ..., title: ...}` to override the button's label instead of using the target page's own title — see example below. Resolved entirely in `templates/partials/parts/relevant_pages.html` against the already-loaded piggymap (exposed to every template as `piggymap`) — no Python changes were needed for this, since the raw list is already available as `content.meta.relevant_pages` from the per-file frontmatter parse. An entry that doesn't resolve to a real page is silently skipped. Since this is read from the rendered file's own frontmatter, a translated assignment can define its own `relevant_pages` list independently of the original. |

### `relevant_pages` title override example

```yaml
relevant_pages:
  - /main/VG1/IM/Programmering/Generelt_-_002_GitHub_Desktop/GitHub_Desktop_Level_1_-_Installasjon
  - path: /main/VG1/IM/Programmering/Generelt_-_003_uv/uv_Level_1_-_Installasjon
    title: uv (pakkehåndterer)
```

## `.oink` sidecar files

A file named `Level N - Title.oink` next to `Level N - Title.md` (YAML
format) is loaded and merged **over** the markdown frontmatter. Any key it
sets overrides the same key from the frontmatter block. It's intended for
metadata that shouldn't live inside the markdown file itself.

## Translations

A translated version of an assignment can be placed at
`translations/<lang-code>/Level N - Title.md` (same filename, sibling
`translations/` folder next to the original). Each translation file has its
own independent frontmatter block, parsed the same way. If a translation has
no `.oink` file of its own but the original does, the original's `.oink` data
is inherited (with `oinkdata` cleared) rather than duplicated per language.
