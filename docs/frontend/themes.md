# Themes and Visual Effects

Piggy themes are CSS files with machine-readable metadata. Python parses that metadata, templates expose it as `window.PIGGY_THEMES`, settings render it as theme choices, and CSS applies the selected theme through `data-theme` on `<html>`.

## Main Files

| File | Role |
| --- | --- |
| `piggy/static/css/themes/*.css` | Theme metadata, variables, and theme-specific overrides. |
| `piggy/utils.py` | `get_css_metadata()` and `get_theme_files()` parse theme metadata. |
| `templates/partials/parts/styles.html` | Loads every theme CSS file. |
| `templates/partials/head.html` | Emits `window.PIGGY_THEMES`. |
| `static/js/preferences.js` | Validates selected theme and sets `data-theme`/`data-theme-type`. |
| `static/js/settings-controls.js` | Renders theme selection controls. |
| `static/js/reader-runtime.js` | Starts/stops animated theme effects. |
| `static/js/theme-effects/*` | Canvas and WebGL effect implementations. |

## Current Themes

| File | Theme path | ID | Name | Type | Category |
| --- | --- | ---: | --- | --- | --- |
| `themes/dark.css` | `dark` | 0 | Dark | dark | standard |
| `themes/light.css` | `light` | 1 | Light | light | standard |
| `themes/piggy.css` | `piggy` | 2 | Piggy | light | playful |
| `themes/piggy-dark.css` | `piggy-dark` | 3 | Piggy (Dark) | dark | playful |
| `themes/high-contrast.css` | `high-contrast` | 4 | High Contrast | dark | accessible |
| `themes/readable.css` | `readable` | 5 | Readable | light | accessible |
| `themes/sage.css` | `sage` | 6 | Sage | light | calm |
| `themes/amethyst.css` | `amethyst` | 7 | Amethyst | light | creative |
| `themes/dusk.css` | `dusk` | 8 | Dusk | dark | focus |
| `themes/ember.css` | `ember` | 9 | Ember | dark | focus |
| `themes/synthwave.css` | `synthwave` | 100 | Synthwave | dark | animated |
| `themes/matrix.css` | `matrix` | 101 | Matrix | dark | animated |
| `themes/desert.css` | `desert` | 102 | Desert | light | animated |
| `themes/ocean.css` | `ocean` | 103 | Ocean | dark | animated |
| `themes/space.css` | `space` | 104 | Space | dark | animated |
| `themes/golden.css` | `golden` | 105 | Golden | dark | animated |

Theme IDs control sort order in parsed metadata. Keep IDs unique.

## Metadata Format

Every theme starts with a metadata comment:

```css
/* METADATA
id: 1
name: Light
description: The default light theme.
type: light
category: standard
tags: default, bright
preview.background: #f7f7f7
preview.surface: #ffffff
preview.text: #171717
preview.accent: #78b3d9
preview.border: #7faac6
preview_style: background: linear-gradient(90deg, #ffffff, rgb(240, 240, 240)); color: rgb(23, 23, 23); text-shadow: none;
*/
```

Parsed metadata includes:

| Field | Meaning |
| --- | --- |
| `id` | Numeric sort order and stable theme identity. |
| `name` | Display label in settings. |
| `description` | Short description for settings UI. |
| `type` | Usually `light` or `dark`; copied to `data-theme-type`. |
| `category` | Theme grouping, such as `standard`, `accessible`, `animated`, `focus`. |
| `tags` | Comma-separated searchable/descriptive tags. |
| `preview.background` | Preview swatch background color. |
| `preview.surface` | Preview swatch surface color. |
| `preview.text` | Preview swatch text color. |
| `preview.accent` | Preview swatch accent color. |
| `preview.border` | Preview swatch border color. |
| `preview_style` | Inline CSS preview style for richer cards. |

`get_css_metadata()` reads these blocks and `get_theme_files()` attaches the theme path based on the filename.

## Theme Selector Contract

Every theme defines variables under:

```css
[data-theme="theme-path"] {
  --piggy-main: ...;
}
```

`preferences.js` sets:

```html
<html data-theme="light" data-theme-type="light">
```

Do not apply the main theme class to `body`; all theme CSS expects the `data-theme` attribute on the root element.

## Variable Groups

Themes should define variables for all visible application areas:

| Group | Used by |
| --- | --- |
| Core page colors | Shell, body, background overlay. |
| Text colors | Body text, headings, cards, nav, markdown. |
| Shadows and glows | Focus states, card elevation, animated themes. |
| Cards | Base cards and exercise cards. |
| Assignment cards | Assignment-specific card gradients and overlays. |
| Information cards | Information-specific card gradients and overlays. |
| Navbar and buttons | Header controls, buttons, icon buttons. |
| Thumbnails | Thumbnail fallback and overlays. |
| Breadcrumbs | Breadcrumb surface and link colors. |
| Menus and tooltips | Settings, language, and level dropdowns. |
| Links | App links and markdown links. |
| Level containers | Level selector and level menu styling. |
| Info boxes/admonitions | Markdown notes, warnings, tips, examples. |
| Logo | Theme-specific logo colors and shadows. |
| Markdown headings | `h1` through `h6` colors/backgrounds. |
| Tables | Markdown table headers, borders, rows. |
| Code | Code backgrounds, borders, titlebars, token colors. |
| Keyboard keys | `<kbd>` and `.keys` styling. |

If a new component needs theme-specific color, add a variable to the contract and update every theme. Avoid leaving one theme with hard-coded fallback colors while the others use variables.

## Animated Themes

Animated themes are a mix of CSS animation and JavaScript canvas/WebGL effects.

| Theme | Effect type | Owner |
| --- | --- | --- |
| `synthwave` | CSS animation and theme-specific effects in the CSS file | `themes/synthwave.css` and shared keyframes. |
| `matrix` | Canvas animation | `theme-effects/matrix-effect.js`. |
| `space` | Canvas animation | `theme-effects/space-effect.js`. |
| `desert` | WebGL shader | `theme-effects/shaders/desert-shader.js`. |
| `ocean` | WebGL shader | `theme-effects/shaders/ocean-shader.js`. |
| `golden` | WebGL shader | `theme-effects/shaders/golden-shader.js`. |

`reader-runtime.js` starts an effect based on `preferences.theme` and first stops all known effects. This prevents two canvas/WebGL backgrounds from running at the same time.

## Effect Suppression

Theme effects are suppressed when:

- `hideDecorations` is `on`
- `reduceMotion` is `reduce`
- `reduceMotion` is `system` and the OS reports `prefers-reduced-motion: reduce`

CSS animations should also include reduced-motion handling. JavaScript effects must expose a stop function so `reader-runtime.js` can halt them.

## WebGL Background Factory

`theme-effects/webgl-background.js` provides `PiggyWebGLBackground.create()`.

Shader files pass:

- `canvasId`
- `fragmentShaderSource`
- optional `vertexShaderSource`
- optional overlay selector
- clear color
- dummy texture color

The factory:

1. creates or reuses a canvas inside `.background-overlay`
2. initializes WebGL
3. compiles shaders
4. links a program
5. sets up a full-screen triangle pair
6. updates `iTime` and `iResolution`
7. renders with `requestAnimationFrame`
8. exposes `start()` and `stop()`

## Adding a Standard Theme

1. Create `piggy/static/css/themes/<path>.css`.
2. Add a metadata block with a unique `id`.
3. Set `type` to `light` or `dark`.
4. Choose an appropriate `category`.
5. Add preview fields and `preview_style`.
6. Add `[data-theme="<path>"]` with the full variable contract.
7. Add any theme-specific component or markdown overrides below the variables.
8. Restart the app if theme metadata is cached.
9. Open settings and confirm the theme appears in the selector.
10. Check card grids, assignment pages, search overlay, settings UI, code blocks, tables, and print-like readability.

## Adding an Animated Theme

For a CSS-only animated theme:

1. Follow the standard theme steps.
2. Put theme-specific animation selectors in the theme file.
3. Put reusable keyframes in `css/animations/keyframes.css` if they are shared.
4. Respect `prefers-reduced-motion` and `data-reader-reduce-motion`.

For a JavaScript effect theme:

1. Follow the standard theme steps.
2. Add a canvas or shader script under `static/js/theme-effects/`.
3. Expose `window.start<Name>Animation` and `window.stop<Name>Animation`.
4. Add script tags in `partials/head.html`.
5. Add start/stop cases in `reader-runtime.js`.
6. Confirm effects stop when switching themes or enabling reduced motion.

## Theme Development Checklist

Before finishing a theme:

1. Confirm metadata parses and appears in `window.PIGGY_THEMES`.
2. Confirm the selector matches the filename path.
3. Confirm both `data-theme` and `data-theme-type` are correct.
4. Check all card types.
5. Check markdown headings, code, admonitions, tables, math, and keyboard keys.
6. Check settings UI, search overlay, level menu, language menu, and breadcrumbs.
7. Check focus states and text contrast.
8. Check reduced-motion behavior.
9. Check generated thumbnails and missing-media fallbacks against the theme.

