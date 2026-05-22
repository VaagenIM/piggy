# Templates

Piggy uses Jinja templates. The hierarchy is intentionally server-rendered: Flask provides PIGGYMAP segments and metadata, and templates choose card types, navigation state, metadata tags, and page structure.

## Template Inheritance

```text
layout.html
  index.html
  settings.html
  error.html
  assignments/_assignments_base.html
    assignments/0-assignments_root.html
    assignments/1-year_level.html
    assignments/2-class_name.html
    assignments/3-subject.html
    assignments/4-topic.html
  assignments/5-assignment.html
```

`assignments/tconvert_assignment_base.html` extends `turtleconvert.html`, which is provided by TurtleConverter rather than this repository.

## Base Layout

### `templates/layout.html`

The shell for nearly every page.

Blocks:

| Block | Purpose |
| --- | --- |
| `head` | Defaults to `partials/head.html`. |
| `extra_head` | Empty extension point. |
| `header` | Optional page-level header content below navigation. |
| `base` | Main page content. |
| `footer` | Optional footer content. |

Important structure:

- Adds `.background-overlay` for static/animated theme backgrounds.
- Includes `partials/header/navigation.html`.
- Wraps page content in `[data-reader-page-content]` so inline settings can hide it.
- Includes a hidden inline settings host on non-settings pages.
- Adds `#reader-ruler`.
- Includes search overlay and post scripts.
- Includes devtools only when `debug` is true.

### `templates/index.html`

Home page. Extends layout and renders `quick_access(piggymap)` if there is content.

### `templates/settings.html`

Direct settings route. Extends layout and includes `partials/parts/settings_content.html`.

### `templates/error.html`

Themed error page. Shows status/message and a 404 image. Inline JavaScript switches image source for selected themes when `data-theme` changes.

## Assignment Templates

### `templates/assignments/_assignments_base.html`

Base for folder/card pages.

Behavior:

- Extends `layout.html`.
- Defaults `card_type` to `objects/card-basic.html`.
- Renders a `.page-title`.
- Loops over `segment.items()` and includes the selected card template.
- Includes `static/js/card_script.js` so tag colors are applied.

### `templates/assignments/0-assignments_root.html`

Root assignment browser. Uses basic cards and hardcodes title to `Oppgavebanken Piggy`.

### `templates/assignments/1-year_level.html`

Year-level page. Uses basic cards and title `meta.name`.

### `templates/assignments/2-class_name.html`

Class/program page. Uses basic cards and title `meta.name`.

### `templates/assignments/3-subject.html`

Subject page. Overrides the base grid to split child topics into:

- `information`: `objects/card-information.html`
- `assignment`: `objects/card-assignment.html`
- exercises/default: `objects/card-exercise.html`

Uses the `list_difference` filter to derive exercises after removing assignments and information.

### `templates/assignments/4-topic.html`

Topic page. Uses `objects/card-level.html` and optionally displays `meta.note` with `img/icons/info.svg` via `include_svg()`.

### `templates/assignments/5-assignment.html`

Final markdown assignment page.

Behavior:

- Extends layout directly.
- Adds `content.head` to the HTML head.
- Shows `content.heading` as `.assignment-heading`.
- Renders `content.body | safe`.

### `templates/assignments/tconvert_assignment_base.html`

TurtleConverter template adapter. Extends `turtleconvert.html` and intentionally empties the `styles` block so Piggy's CSS owns visual styling.

## Card Templates

### `templates/objects/card.html`

Core card macro.

Parameters:

| Parameter | Meaning |
| --- | --- |
| `overlay_text` | Text for thumbnail overlay. |
| `difficulty` | Difficulty icon number. |
| `tags` | Tags rendered as `.tag-box`. |
| `level_count` | Number shown in level count badge if greater than 1. |
| `extra_classes` | Added to card anchor. |
| `abspath` | Parent URL. |
| `item` | URL suffix. |
| `title` | Card title. |
| `description` | Description block. |
| `thumbnail` | Thumbnail image URL. |
| `thumbnail_alt` | Thumbnail alt text. |
| `show_*` flags | Toggle title, levels, difficulty, overlay, tags, description, thumbnail. |

The macro keeps the anchor lean: visual differences are driven by `extra_classes` and the `show_*` flags.

### `templates/objects/card-basic.html`

Generic folder card. Uses `data.meta.name`, `data.meta.description`, and `<item>/media/header.webp`.

### `templates/objects/card-exercise.html`

Exercise topic card. Links directly to the first level inside the topic:

```jinja
item ~ "/" ~ (data.data.keys()|list)[0]
```

Shows thumbnail, level count, difficulty, tags, overlay, and description.

### `templates/objects/card-information.html`

Information topic card. Also links to the first child level, but hides thumbnail, levels, difficulty, overlay, and tags. Uses information-specific card classes.

### `templates/objects/card-assignment.html`

Assignment topic card. Links to the topic folder rather than a first child level. Shows description, hides level/difficulty/overlay/tags, and uses assignment-specific layout classes.

### `templates/objects/card-level.html`

Level card for an individual assignment markdown file.

Uses:

- `data.meta.title`
- `data.meta.description`
- `data.meta.thumbnail` if present
- generated thumbnail fallback if not
- `data.meta.difficulty`
- special class when `special_condition` exists

## Head Partials

### `templates/partials/head.html`

Includes common head, styles, `window.PIGGY_THEMES`, and the main script tags.

Script order matters:

1. Theme effect scripts.
2. `preferences.js`.
3. `on-load.js`.
4. Deferred storage/settings/reader/search/markdown scripts.

### `templates/partials/common_head.html`

Sets charset, viewport, color-scheme, and includes title, icon, and Open Graph tags.

### `templates/partials/parts/styles.html`

Loads:

- `css/main.css`
- every theme CSS file from `themes`
- `css/components/settings-late.css`
- Google Fonts
- local font imports

### `templates/partials/parts/title.html`

Title priority:

1. `meta.name`
2. `content.heading`
3. `error.code` and `error.name`
4. default `Piggy`

### `templates/partials/parts/icon.html`

Favicon link to `img/icons/piggy_icon-128.png`.

### `templates/partials/parts/og-tags.html`

Builds Open Graph/Twitter tags.

Description priority:

1. Translation `description`
2. Translation `oinkdata.summary`
3. Translation `summary`
4. Base `meta.description`
5. Base `meta.oinkdata.summary`
6. Base `meta.summary`

Image priority:

1. Absolute `meta.thumbnail` when no `media_abspath`.
2. `media_abspath + meta.thumbnail`.
3. Generated thumbnail for level pages.
4. Section header image.
5. Static Piggy icon fallback.

## Header and Navigation Partials

### `templates/partials/header/navigation.html`

Main nav. Includes:

- logo
- back button
- level selector on assignment pages
- search button
- language selector on assignment pages
- settings button

It conditionally loads language/level JavaScript only when `current_language` and `supported_languages` are present.

### `templates/partials/header/logo.html`

Piggy home link with icon and text.

### `templates/partials/header/back-button.html`

Computes parent route and label from `request.path`, `meta`, and assignment type.

Special behavior:

- Removes trailing `/lang/<lang>` when present.
- Hides on shallow routes.
- On final content pages for non-assignment topics, goes back two levels so exercise/information pages return to subject/topic context more naturally.

### `templates/partials/header/breadcrumbs.html`

Builds breadcrumb list from request path.

Special behavior:

- Removes trailing `/lang/<lang>`.
- Can hide the final topic slug for information/exercise leaf pages.
- Uses metadata labels where possible.

### `templates/partials/header/level-selector.html`

Displays sibling levels for an assignment topic.

Behavior:

- Reads `levels_data` from `meta`.
- Uses label `Oppgave`, `Tema`, or `Level` depending on topic type.
- Sorts levels by numeric level.
- Uses translated metadata when the current language has a translation.
- Renders both button-strip and dropdown-menu markup; JavaScript chooses when to switch.

### `templates/partials/header/level-tooltip.html`

Tooltip content for a level button. May include difficulty icon and translated/default level title.

### `templates/partials/header/language-selector.html`

Language dropdown. In normal mode, links carry `data-language-option` and JavaScript writes the `lang` cookie. In GitHub Pages mode, links include `/lang/<code>`.

## Settings Partials

### `templates/partials/parts/settings.html`

Settings/back navigation button. On normal pages it links to `/settings?return_to=<current path>`. On the settings page or when inline settings is active, JavaScript turns it into a back button.

### `templates/partials/parts/settings_content.html`

Complete settings UI markup. It provides:

- Header with reset and return actions.
- Preview card.
- Tab buttons: Main, Text, Focus, Support.
- Render targets using `data-settings-render`.
- Static explanation copy for remembered position.

The actual controls are generated by `settings-controls.js`.

### `templates/partials/parts/settings/search-button.html`

Search icon button. Opens the search overlay via JavaScript.

## Other Partials and Macros

### `templates/partials/parts/search_overlay.html`

Search dialog included once in `layout.html`. Contains input, close button, and result list.

### `templates/partials/parts/quick_access.html`

Macro `quick_access(tree)` renders the home quick-access view from PIGGYMAP. It groups by year and study direction and links to subject pages with header thumbnails.

### `templates/partials/parts/scroll_to_top.html`

Scroll-to-top button and inline script. Shows after `window.scrollY > 150` and respects `data-reader-reduce-motion` plus system reduced-motion preferences.

### `templates/partials/parts/icon.html`, `title.html`, `styles.html`, `og-tags.html`

Documented under Head Partials.

### `templates/partials/post_scripts.html`

Includes the scroll-to-top partial and sets `data-md-color-scheme="slate"` on the body for Material compatibility.

### `templates/macros/include.html`

Provides `include_svg(svg, class='', style='')`, which loads an SVG file through Jinja and injects optional `class` and `style` attributes into its root `<svg>`.

### `templates/partials/devtools/_devtools.html`

Includes debug variable logging.

### `templates/partials/devtools/log_variables.html`

Debug-only console logging for paths, route prefixes, metadata, request data, language data, and PIGGYMAP.

## Complete Template File Reference

| File | Purpose |
| --- | --- |
| `layout.html` | Global page shell. |
| `index.html` | Home quick access page. |
| `settings.html` | Direct settings page route. |
| `error.html` | Error page. |
| `assignments/_assignments_base.html` | Base card-grid page. |
| `assignments/0-assignments_root.html` | Root assignment grid. |
| `assignments/1-year_level.html` | Year grid. |
| `assignments/2-class_name.html` | Class/program grid. |
| `assignments/3-subject.html` | Subject grid split by content type. |
| `assignments/4-topic.html` | Topic levels grid and optional note. |
| `assignments/5-assignment.html` | Rendered markdown assignment page. |
| `assignments/tconvert_assignment_base.html` | TurtleConverter adapter. |
| `objects/card.html` | Card macro. |
| `objects/card-basic.html` | Basic folder card. |
| `objects/card-exercise.html` | Exercise topic card. |
| `objects/card-information.html` | Information topic card. |
| `objects/card-assignment.html` | Assignment topic card. |
| `objects/card-level.html` | Assignment level card. |
| `partials/head.html` | CSS/JS head loader. |
| `partials/common_head.html` | Common meta/title/icon/OG includes. |
| `partials/post_scripts.html` | Scroll-to-top and Material compatibility script. |
| `partials/header/navigation.html` | Main nav. |
| `partials/header/logo.html` | Home logo. |
| `partials/header/back-button.html` | Back button. |
| `partials/header/breadcrumbs.html` | Breadcrumbs. |
| `partials/header/level-selector.html` | Assignment level selector. |
| `partials/header/level-tooltip.html` | Level tooltip content. |
| `partials/header/language-selector.html` | Language selector. |
| `partials/parts/styles.html` | Stylesheets and fonts. |
| `partials/parts/title.html` | `<title>` generation. |
| `partials/parts/icon.html` | Favicon. |
| `partials/parts/og-tags.html` | Open Graph/Twitter metadata. |
| `partials/parts/settings.html` | Settings/back button. |
| `partials/parts/settings_content.html` | Settings page UI. |
| `partials/parts/search_overlay.html` | Search modal. |
| `partials/parts/quick_access.html` | Home quick access macro. |
| `partials/parts/scroll_to_top.html` | Scroll-to-top button/script. |
| `partials/parts/settings/search-button.html` | Search nav button. |
| `partials/devtools/_devtools.html` | Debug devtools include. |
| `partials/devtools/log_variables.html` | Debug console logging. |
| `macros/include.html` | SVG include macro. |
