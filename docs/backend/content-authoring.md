# Piggybank Content Authoring

Piggybank is the content source. It is not documented lesson-by-lesson here; this document explains how Piggy stores, discovers, and renders content.

## Content Tree Contract

Piggy scans `piggybank/` up to five levels deep. Those levels map to URL/template depth:

```text
piggybank/
  VG2/                         level 1: year
    IT/                        level 2: class/program
      Utvikling/               level 3: subject
        Programmering - X/     level 4: topic
          Name Level 1 - A.md  level 5: assignment/level leaf
```

URLs replace spaces with underscores and remove unsafe characters:

```text
piggybank/VG2/IT/Utvikling/Programmering - Logging
-> /main/VG2/IT/Utvikling/Programmering_-_Logging
```

## Valid Assignment Filenames

Only markdown files matching this regex become assignment leaves:

```text
^.*Level[ _](\d+)[ _]-[ _](.+).md$
```

Valid examples:

```text
Logging Level 1 - Introduksjon til Logging.md
Python 2 Level 2 - Mer komplisert.md
HTML Level_3 - Legg til flere sider.md
```

The number after `Level` becomes `level`. The title is mostly taken from frontmatter or the first `#` heading, not directly from the filename.

Files that do not match the regex are ignored by PIGGYMAP.

## Folder Metadata: `meta.json`

Any content folder may include `meta.json`. If it does not, Piggy creates a default `name` from the folder name.

Common fields:

| Field | Where used | Meaning |
| --- | --- | --- |
| `name` | Cards, headings, breadcrumbs, quick access | Display name. Defaults to folder name with underscores replaced by spaces. |
| `description` | Cards, Open Graph fallback | Short description of a section/topic. |
| `tags` | Cards and authoring metadata | List of tags. Used visually on exercise cards. |
| `difficulty` | Cards/level selector | Numeric difficulty; icons support 1-5. Values above 5 are clamped in card template. `-1` means effectively none. |
| `type` | Subject page grouping, card behavior, back button logic | Usually `exercise`, `assignment`, or `information`. Topics default to `exercise` when missing. |
| `note` | Topic template | Optional note shown on topic pages. |
| `udir_id`, `udir_name`, `udir_link` | Content metadata | Used as curriculum metadata if present. |

Piggy also injects:

| Field | Meaning |
| --- | --- |
| `system_path` | Internal `Path` to the folder. Added automatically. |

## Topic Types

At subject depth, children are split into three sections:

| `meta.type` | Subject page section | Card template | Click behavior |
| --- | --- | --- | --- |
| `information` | `Informasjon` | `card-information.html` | Links directly to first level inside the topic. |
| `assignment` | `Innleveringsoppaver` | `card-assignment.html` | Links to the topic folder. |
| missing or `exercise` | `Ovingsoppgaver` | `card-exercise.html` | Links directly to first level inside the topic. |

Topic folders at topic depth default to `exercise` if `type` is missing.

## Assignment Frontmatter

Markdown assignments may start with YAML frontmatter:

```markdown
---
title: Introduksjon til Logging
description: Learn what logging is and why it matters.
difficulty: 2
tags:
  - Python
  - Logging
thumbnail: media/header
---
```

Piggy reads frontmatter with `yaml.unsafe_load()` and then escapes values with MarkupSafe before putting them in metadata.

Important behavior:

- If frontmatter is missing, `title` falls back to the first markdown heading starting with `# `.
- If there is no heading, it falls back to the filename stem with underscores replaced by spaces.
- If `thumbnail` is missing, it defaults to `media/header`.
- Frontmatter can be augmented or overridden by a same-name `.oink` file, though no `.oink` files were present during this documentation pass.

## `.oink` Sidecar Files

Piggy supports optional YAML sidecars:

```text
Logging Level 1 - Introduksjon til Logging.md
Logging Level 1 - Introduksjon til Logging.oink
```

If the `.oink` file exists and parses to a dict, its values are merged into frontmatter metadata. For translations, if the source assignment has `.oink` data but the translation does not, Piggy copies source `.oink` keys and sets `oinkdata` to `{}`.

## Translations

Translations live beside the source assignment in:

```text
translations/<language-code>/<same markdown filename>
```

Example:

```text
Programmering - Logging/
  Logging Level 1 - Introduksjon til Logging.md
  translations/
    eng/
      Logging Level 1 - Introduksjon til Logging.md
    ukr/
      Logging Level 1 - Introduksjon til Logging.md
```

Rules:

- The translated filename must exactly match the source markdown filename.
- The language code must exist in `piggy/data/language-data.json` for rich display data.
- Missing translations simply do not appear in the language selector.
- In normal Flask mode, selected language is stored in the `lang` cookie and the URL stays on the base path.
- In GitHub Pages mode, language is included in the URL as `/lang/<code>`.

## Language Metadata

`piggy/data/language-data.json` maps language codes to records:

```json
{
  "eng": {
    "name": "English",
    "flag": "...",
    "direction": "ltr",
    "script": "Latin",
    "locale": "en_...",
    "font": "sans-serif",
    "country_code": "..."
  }
}
```

The empty key `""` is the default language. `models.get_languages()` also injects `key` into every record at runtime.

## Media and Attachments

### `media/`

Folder-level visual assets live in `media/`.

Common file:

```text
media/header.webp
```

Requested through:

```text
/img/<content path>/media/header.webp
```

If `media/header.webp` is missing, Piggy generates a fallback image from the content title.

### `attachments/`

Assignment body assets live in `attachments/`.

Markdown typically references them relatively:

```markdown
![Example](attachments/example.webp)
```

Requested through:

```text
/main/<assignment path>/attachments/example.webp
```

If an attachment is missing, Piggy returns the placeholder image at `static/img/placeholders/100x100.png`.

## Thumbnails

Card thumbnails come from metadata:

- Folder cards use `<media_abspath>/<item>/media/header.webp?title=<name>`.
- Level cards use `data.meta.thumbnail` when present.
- Missing media headers fall back to generated thumbnails.
- `/api/generate_thumbnail/<text>` can generate deterministic title cards directly.

## Adding New Content

Use this checklist for a new topic:

1. Create the topic folder under the correct year/class/subject folder.
2. Add `meta.json` with at least `name`, `description`, and optionally `type`, `tags`, `difficulty`, `note`.
3. Add `media/header.webp` if you want a real visual instead of generated fallback.
4. Add one or more markdown files matching `... Level <number> - <title>.md`.
5. Add YAML frontmatter with at least `title`.
6. Put images/files referenced by markdown into `attachments/`.
7. For translations, add files under `translations/<code>/` with the exact same filename.
8. Run the app with `USE_CACHE=0` while editing.
9. Visit the parent subject, topic, and each level page to confirm cards, level selector, language selector, media, and metadata.

## Adding a New Year/Class/Subject

1. Create a folder in the appropriate location.
2. Add `meta.json` with `name` and `description`.
3. Add `media/header.webp` where a card or quick access thumbnail needs it.
4. Add children recursively until there is at least one valid assignment markdown leaf.
5. Restart the app if caching/import-time PIGGYMAP generation is active.

## Common Pitfalls

- A markdown file with no `Level <number> -` pattern will not appear.
- A translated file with a different filename will not be recognized.
- Content path changes alter URLs because URLs are derived from folders and filenames.
- Missing `media/header.webp` is not fatal, but will produce generated art.
- Missing attachments render as the placeholder image, which can hide broken authoring until someone checks the page.
- When `USE_CACHE=1`, changes can appear stale until restart or cache invalidation.

