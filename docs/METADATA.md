# `meta.json` reference

Every folder in the `piggybank/` content tree can contain a `meta.json` file
describing that folder - its display name, a description, tags, and a few
other display hints. A sibling `meta.oink` JSON file can provide additional
metadata under `oinkdata`, including the folder UUID used for shortlinks.
This document lists every property `meta.json` supports.

For metadata on individual assignment files (`Level N - Title.md`), see
[ASSIGNMENT_FRONTMATTER.md](ASSIGNMENT_FRONTMATTER.md) instead - that's a
separate mechanism (YAML frontmatter + optional `.oink` sidecar), not
`meta.json`.

There is no full schema validation for `meta.json`. It's loaded with
`json.load()` (`piggy/piggybank.py`, `load_meta_json`), and the whole content
tree (`PIGGYMAP`) is built once at app startup. A missing `meta.json` is
treated as `{}` (no error), but invalid JSON syntax will crash the app on
startup. Unknown topic `type` values produce a startup warning and otherwise
fall back to the existing module presentation; other unknown/extra keys are
ignored. A typo'd key name (e.g. `discription`) therefore still does nothing.

## Folder hierarchy

`meta.json` can appear at any of the first four levels of the content tree:

```
piggybank/piggybank/
└── VG1/                          ← Year
    └── IM/                       ← Class
        └── Programmering/        ← Subject
            └── Web - Web 1/      ← Topic
                └── Level 1 - ....md   ← Assignment (no meta.json here - see ASSIGNMENT_FRONTMATTER.md)
```

| Level | Example folder | Purpose |
|---|---|---|
| Year | `VG1`, `VG2` | School year |
| Class | `IM`, `IT` | Study program |
| Subject | `Programmering`, `Utvikling` | Subject/course |
| Topic | `Web - Web 1` | A group of related assignments/levels |

## Property reference

| Property | Type | Required | Meaning |
|---|---|---|---|
| `name` | string | Optional | Display name for the folder. If omitted, falls back to the folder name with underscores replaced by spaces (`piggy/piggybank.py:20-21`). |
| `description` | string | Optional | Free-text description. Used as card description text and as the `og:description`/`twitter:description` fallback (`piggy/templates/partials/parts/og-tags.html:39`). |
| `tags` | array of strings | Optional, topic-level | Keyword list rendered as pill badges on cards (`piggy/templates/objects/card.html:81-87`) and used for client-side search filtering. Only meaningful on topic folders in practice. |
| `difficulty` | integer | Optional | Only actually rendered (as a 1–5 icon, clamped at 5) for assignment *levels* under a topic - see `piggy/templates/objects/card.html:65-72`. When set directly on a folder's own `meta.json` it is **not rendered anywhere** (see [Known quirks](#known-quirks--unused-fields)). `-1` is used throughout existing content as an "unset" placeholder. |
| `type` | string (enum) | Optional | One of `"assignment"`, `"exercise"` (default), `"information"`, `"extra"`. Groups a **topic** on the subject page; topics default to `"exercise"` at build time. `"extra"` currently shares the module presentation. It also sets the level-selector label ("Tema"/"Oppgave"/"Level"). Unknown values warn and fall back. |
| `note` | string | Optional, topic-level only | Freeform note rendered as an info callout at the top of the topic page (`piggy/templates/assignments/4-topic.html:9-13`). |
| `level_name` | string | Optional, topic-level only | Overrides the default type-based label used in the level selector (e.g. `"Del"` instead of "Level" - `piggy/templates/partials/header/level-selector.html:7-8`). |
| `sibling_links` | boolean | Optional, topic-level only | `false` hides previous/next level navigation. With multiple pages, cards link to the topic overview instead of a sibling page. |

> **Do not author `system_path` manually.** It's injected into the in-memory
> metadata at build time (`piggy/piggybank.py:166`) to point at the folder's
> real path on disk, and is used to resolve thumbnail/API URLs. It never
> comes from `meta.json` itself.

## Per-level guide

### Year (e.g. `VG1/meta.json`)

Typically just a `description`. `name` is rarely set since the folder name
(`VG1`) is already the display name.

```json
{
  "description": "Første året på videregående."
}
```

### Class (e.g. `VG2/IT/meta.json`)

`name` and `description`.

```json
{
  "name": "IT",
  "description": "Informasjonsteknologi"
}
```

### Subject (e.g. `VG1/IM/Programmering/meta.json`)

`name` and `description`. The topic folders beneath this folder default to
`type: "exercise"` if they do not specify a type.

```json
{
  "name": "Programmering",
  "description": "Programmeringsfaget til 1IM"
}
```

### Topic (e.g. `VG1/IM/Programmering/Web - Web 1/meta.json`)

The richest level - this is where `tags`, `note`, and `level_name` actually
matter, and where `type` controls which section (Informasjon /
Innleveringsoppgaver / Øvingsoppgaver) the topic's children are grouped into
on the subject page.

```json
{
  "name": "Web 1",
  "description": "Første uke med webutvikling!",
  "tags": ["HTML", "CSS", "Web"],
  "difficulty": -1,
  "level_name": "Del"
}
```

An "information" topic (grouped under "Informasjon" instead of modules):

```json
{
  "name": "Kompetansemål Utvikling",
  "description": "her kan du finne kompetansemålene i faget utvikling.",
  "tags": ["Kompetansemål", "Utvikling"],
  "difficulty": -1,
  "type": "information"
}
```

## Known quirks / unused fields

- **Folder-level `difficulty` is not rendered anywhere.** Many `meta.json`
  files (mostly topics) set `difficulty` - usually `-1`, sometimes a small
  integer - but no template reads a folder's own `meta.difficulty`; only the
  `difficulty` on individual assignment levels is displayed. Setting it on a
  folder's `meta.json` currently has no visible effect.
- **`special_condition`** is checked in
  `piggy/templates/objects/card-level.html:12` (`'card-special-condition' if
  'special_condition' in data else ''`) but nothing in the codebase ever sets
  this key - it's dead/unimplemented. Don't rely on it.
- **`extra` and unknown `type` values** do not have a dedicated subject-page
  section and currently share the module presentation. Unknown values also
  produce a warning so a typo is not silent.
