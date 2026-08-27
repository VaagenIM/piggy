# Piggyvisor — content model & authoring app design

## Problem

Adding a new assignment to piggybank today requires: cloning the repo, running Obsidian, knowing an undocumented three-source metadata scheme (YAML frontmatter + `.oink` sidecar + folder `meta.json`), and hand-crafting a filename that matches a strict, silently-failing regex. There's no schema validation — a mistake just renders a blank page with a console warning nobody sees.

Beyond the mechanics, the deeper issue: content is *physically* coupled to *curriculum placement*. A piece of content only exists at exactly one path in the `VG/Program/Subject/Topic` tree, so the same material can't be reused across two classes/subjects without literally copying files.

## Concept: decouple content from placement

Two kinds of things, instead of one nested tree:

- **Mikromodul** — a self-contained unit of content with its own Levels/Deler (structurally like today's "topic" folder: a name, description, and a numbered sequence of Level files). Lives in its own flat namespace, not nested under a class or subject.
- **Makromodul** — a curriculum-facing entry under Klasse → Fag. Holds *no content itself* — just metadata plus an ordered list of pointers to one or more Mikromoduler.

```
Klasse
 └─ Fag
     └─ Makromodul  →  pointers to →  Mikromodul(er)
                                        └─ Level 1, Level 2, ...
```

The same Mikromodul (e.g. "Python 1") can be pointed to by multiple Makromoduler across different Fag/Klasse — real many-to-many reuse, not just a naming/organizational split.

## Example data layout

Proposed for a brand new, separate content repo (fully decoupled from `VaagenIM/piggybank`'s history and conventions — this is a clean slate, not a migration):

```
mikromoduler/                      # flat registry, one folder per unit
├── python-1/
│   ├── mikromodul.json            # {id, name, description, tags}
│   ├── Level 1 - Intro.md         # same "Level N - Title.md" convention as today's piggybank
│   └── Level 2 - ....md
└── css-1/
    └── ...

klasse/                            # curriculum tree — pointers only, no content
└── VG1/
    └── IM/
        └── makromoduler/
            └── web-basics.json    # {name, description, mikromoduler: ["python-1", "css-1"]}
```

Notes:
- A Mikromodul's `id` is its folder slug (kebab-case, unique across the flat registry) — the identifier a Makromodul references.
- A Makromodul's `mikromoduler` field is a plain ordered array of ids for v1 — no per-placement override (custom title/order-within-parent) yet. Start simple; add overrides only if real usage shows a need.
- `mikromodul.json` is the *single* metadata source per unit — no frontmatter/`.oink`/`meta.json` three-way merge like legacy piggybank. This directly addresses the "convoluted" complaint that started this whole effort.
- Level files keep today's Markdown dialect (mkdocs-material via `turtleconverter`: `> [!TYPE]` callouts, `=== "tab"` blocks) — no new syntax for authors to learn.

## Piggyvisor

A **standalone app** — its own repo, own dependencies, own running process. Not a route bolted onto piggy. Its job: let someone author Mikromoduler and Makromoduler through a web form, without ever needing git, a local clone, or Obsidian. Markdown knowledge is an acceptable prerequisite; tooling is not.

**v1 capabilities:**
1. **Create a Mikromodul** — name/description/tags + one or more Levels, each authored as Markdown with a live preview.
2. **Create/edit a Makromodul** — pick a Klasse/Fag, name it, attach existing Mikromoduler by searching/selecting from the flat registry.
3. **Submit** — produces a pull request against the content repo.

**Mechanics carried over from earlier design work (repo-agnostic, just retargeted):**
- *Live preview*: render Level Markdown through `turtleconverter.mdfile_to_sections` — the exact same renderer piggy itself uses in production — so a preview looks like the real thing, not a generic Markdown-only approximation. Piggyvisor needs its own preview shell (it doesn't inherit piggy's `layout.html`/static assets), but can lean on turtleconverter's own bundled default template/styles rather than reimplementing piggy's CSS.
- *Submission*: GitHub's Git Data API (blobs → tree → commit → branch → PR) — one atomic commit per submission, no local git clone living inside a multi-worker process. When no GitHub token/repo is configured yet (early local development), submission can fall back to committing directly to a local branch of a local content repo, so the full authoring flow is testable before any real GitHub repo exists.
- *Filename/level safety*: the `Level N - Title.md` convention is generated and validated server-side (auto-suggested next level number, filename checked against the same regex before anything is written) — the fragile hand-authored filename is exactly what caused piggybank's silent failures, so this must not be free text.

## Relationship to piggy

This is explicitly a **prototype alongside**, not a migration:
- Piggy's live site keeps serving the existing `VG/Program/Subject/Topic` tree from `piggybank`, completely untouched.
- Piggy needs **zero code changes** for Piggyvisor v1 to exist and work.
- Actually *rendering* Makromodul/Mikromodul content on the live piggy site is a separate, later phase (Phase 2) — deferred until the data model is validated here. It's a materially harder problem: a Mikromodul reachable via multiple curriculum paths breaks piggy's current assumption that URL path mirrors physical folder location (`generate_piggymap()`, the wildcard routes, and the LRU cache keys in `piggy/app.py`/`piggy/caching.py` all currently assume a 1:1 mapping).

## Explicitly deferred

- Phase 2: piggy rendering Makromodul/Mikromodul content on the live site (routing, cache-key redesign).
- Migrating existing piggybank content into the new model.
- Per-placement Makromodul overrides (custom order/title per pointer).
- Auth/permissions for who can use Piggyvisor.
- Abuse mitigation on a public submit endpoint (honeypot/rate-limiting) — not a blocker for a first prototype.

## Open questions

- Exact slug/id rules for Mikromoduler — uniqueness enforcement, and what happens on rename once a Mikromodul is already referenced by one or more Makromoduler.
- Where the real content repo eventually lives (org/account, name) — a real-world action requiring explicit go-ahead, not something to scaffold silently.
- Whether Piggyvisor needs auth from day one, or v1 is trusted/internal-only.
- Whether "Fag" needs its own metadata (description, ordering of Makromoduler within it) or is purely a path segment for v1.

## Suggested next step

Scaffold Piggyvisor locally (own project folder, own local content repo, no remote yet) and build the full v1 flow — Mikromodul creation, Makromodul creation, live preview, and submission (against a local branch until a real content repo exists) — so the model can actually be used and judged before deciding on repo names, hosting, or Phase 2 integration work.
