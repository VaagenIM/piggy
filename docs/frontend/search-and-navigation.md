# Search and Navigation

Search and navigation are split between backend data, Jinja markup, CSS, and small JavaScript components. The backend decides what exists; templates render structural links; JavaScript improves interaction and responsiveness.

## Search Overview

Search is client-side Lunr search over backend-generated JSON.

Flow:

```text
piggy/search.py
  -> /api/search-data
  -> static/js/components/search.js
  -> Lunr index in browser
  -> search overlay results linking to /main/...
```

Main files:

| File/template | Role |
| --- | --- |
| `piggy/search.py` | Builds flat search documents from `PIGGYMAP` and rendered/cleaned markdown. |
| `piggy/api.py` | Exposes `/api/search-data`. |
| `templates/partials/search.html` | Search overlay markup. |
| `static/js/modules/lunr.min.js` | Vendor search library. |
| `static/js/components/search.js` | Search overlay behavior, index creation, query logic, result rendering. |
| `static/css/components/search.css` | Search UI styling. |

## Search Data

The endpoint:

```text
GET /api/search-data
```

returns a list of search documents. Each document is keyed by an `id` that maps back to `/main/<id>`.

The browser index uses:

| Field | Boost | Meaning |
| --- | ---: | --- |
| `title` | 10 | Assignment/topic title. |
| `content` | 2 | Searchable content excerpt/body field. |
| `body` | 1 | Additional body text. |

The backend strips or reduces noisy markdown syntax before exposing data, so search is based on human-readable content instead of raw markdown tokens.

## Search Overlay DOM Contract

`components/search.js` expects these elements:

| Element id/class | Meaning |
| --- | --- |
| `#search-button` | Button that opens the overlay. |
| `#search-overlay` | Full-screen search overlay. |
| `#search-overlay-input` | Search input. |
| `#search-overlay-close` | Close button. |
| `#search-results` | Result list container. |
| `.search-result-*` | Classes used for rendered results and styled by `search.css`. |

If any required element is missing, the script exits safely.

## Search Interaction

Keyboard behavior:

- `Ctrl+K` or `Cmd+K` toggles search.
- `Escape` closes search when open.

Mouse behavior:

- clicking the search button opens search.
- clicking the close button closes search.
- clicking outside the search panel closes search.

Index behavior:

- The script fetches `/api/search-data` eagerly in the background.
- If the user types before the index is ready, the overlay shows a loading message.
- When the index finishes building, the current query reruns.

## Query Construction

For each typed term, `components/search.js` builds both fuzzy and prefix matches:

```text
term~1 term*
```

for terms up to 5 characters, and:

```text
term~2 term*
```

for longer terms.

Special Lunr characters are stripped from terms before this query is built. If the constructed query fails, the script falls back to a raw Lunr search, then to no results.

Only the top 20 results are rendered.

## Result Rendering

Each result can include:

- linked breadcrumb trail
- title
- snippet
- highlighted query matches with `<mark>`

The script escapes result HTML before rendering. Breadcrumb labels are decoded from entities and URL-ish underscores are displayed as spaces.

## Main Navigation

Primary navigation is rendered by:

| File | Role |
| --- | --- |
| `templates/partials/header/navigation.html` | Header/nav structure, settings/search buttons, level controls, and language selector placement. |
| `templates/partials/header/breadcrumbs.html` | Breadcrumb trail. |
| `templates/partials/parts/back_button.html` | Contextual back button. |
| `static/css/components/navigation.css` | Nav layout and controls. |
| `static/css/components/breadcrumbs.css` | Breadcrumb styling. |
| `static/css/components/buttons.css` | Shared button styling. |

Backend helpers provide route context such as the current PIGGYMAP path, parent links, and assignment metadata. Templates use that context to decide which controls are visible.

## Breadcrumbs

Breadcrumbs are derived from the current content path. Folder names are normalized for URLs, while display labels come from PIGGYMAP metadata when possible.

Important behavior:

- Breadcrumbs link to `/main/...` folder routes.
- Assignment leaves usually show the current assignment/level context after folder breadcrumbs.
- Search results render their own breadcrumb links from document metadata or document id fallback.

## Back Button

`partials/parts/back_button.html` is used where pages need a contextual return path. Topic `meta.type` affects behavior:

- information and exercise topics often link directly to the first level
- assignment topics link to the topic folder
- assignment pages link back to the nearest meaningful parent

When changing topic navigation, inspect both backend route selection and card template link behavior.

## Level Navigation

Assignment topics can have multiple markdown files with different `Level <number>` values. Templates render level controls so users can move between them.

Main files:

| File/template | Role |
| --- | --- |
| `templates/partials/header/navigation.html` | Renders level buttons/dropdown in the navbar area. |
| `templates/partials/nav/level_item.html` | Individual level link/button item. |
| `static/js/components/level-tooltips.js` | Tooltip placement, dropdown placement, adaptive button/menu switching. |
| `static/css/components/level-select.css` | Level selector, thumbnails, tooltips, and dropdown styles. |

## Level Tooltip Behavior

`level-tooltips.js`:

- positions tooltips relative to the hovered/focused level trigger
- clamps tooltip position within the viewport
- flips from bottom to top placement if needed
- keeps arrow position aligned with the trigger
- updates on resize, scroll, orientation change, visual viewport movement, and image load
- sets `aria-describedby` for tooltip accessibility

The tooltip script is defensive: if no `.level-select .nav-tooltip` elements exist, it exits.

## Adaptive Level Menus

The navbar can show level controls as buttons or as a menu. `level-tooltips.js` measures available width and toggles:

```text
.level-selector--menu
```

when buttons no longer fit. The menu version uses a `<details>`-style dropdown and updates its top, left, width, and max-height through CSS custom properties.

The level menu and language menu close each other so dropdowns do not overlap.

## Language Selection

Language selection is rendered on assignment pages when translations are available.

Main files:

| File/template | Role |
| --- | --- |
| `templates/partials/nav/language_selector.html` | Language selector markup. |
| `static/js/components/language-selector.js` | Sorting, dropdown/details behavior, cookie setting, and navigation. |
| `static/css/components/language-selector.css` | Selector styling. |
| `piggy/data/language-data.json` | Language metadata. |
| `piggy/models.py` | Loads language records and injects `key`. |

Preferred language sort order:

```text
default, nno, eng, ukr, then all others alphabetically by code
```

The default language uses the empty language key `""`.

## Language Routing

Normal Flask mode:

- language is stored in the `lang` cookie
- links can point to the same assignment path
- selecting the current URL reloads the page after changing the cookie

GitHub Pages/static mode:

- language is represented in the URL as `/lang/<code>`
- templates and route helpers account for the static output path shape

Backend content rules for translations are documented in [Content Authoring](../backend/content-authoring.md).

## Card Navigation

Cards are rendered through `templates/objects/` and styled by card CSS.

Navigation behavior depends on the depth and metadata:

- year/class/subject folder cards link to the folder route
- `exercise` and `information` topic cards often link to the first assignment level
- `assignment` topic cards link to the topic folder
- assignment-level cards link to the assignment route

`card_script.js` enhances tag colors after render. It does not decide URLs.

## Quick Access

The root page can render quick-access content through:

| File | Role |
| --- | --- |
| `templates/quick_access.html` | Root quick-access structure. |
| `static/css/components/quick-access.css` | Quick-access layout and styling. |

Quick access uses the same content metadata concepts as cards: names, descriptions, routes, and media thumbnails.

## Development Checklist

When changing navigation/search:

1. Confirm whether the change belongs in PIGGYMAP generation, route lookup, template link logic, or JavaScript enhancement.
2. Keep `/main`, `/img`, and `/api` prefixes separate.
3. Search for the class/id/data hook in CSS and JS before renaming it.
4. Test both assignment pages and folder/card-grid pages.
5. Test with long level names, many levels, and small viewport widths.
6. Test with and without translations.
7. Test `Ctrl+K` search after backend search data changes.

