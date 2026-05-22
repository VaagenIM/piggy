# Frontend Overview

Piggy's frontend is server-rendered HTML with static CSS and browser JavaScript. There is no bundler and no frontend framework. The backend sends Jinja-rendered pages; CSS variables and JavaScript modules turn those pages into a themeable, searchable, reader-friendly interface.

## Frontend Responsibilities

- Render navigable card grids and assignment pages.
- Provide search overlay and client-side Lunr search.
- Provide settings UI and reader preferences.
- Apply themes, fonts, font sizes, contrast modes, motion preferences, focus mode, reading ruler, and remembered scroll position.
- Enhance TurtleConverter/MkDocs-style markdown output.
- Provide language selection and level navigation.
- Render optional animated theme backgrounds.

## High-Level Page Structure

Every normal page extends `templates/layout.html`.

```html
html
  head
    partials/head.html
      partials/common_head.html
      partials/parts/styles.html
      script tags
  body.main-container
    .background-overlay
    .content-wrapper
      header.site-header
        partials/header/navigation.html
      main
        [data-reader-page-content]
          page block content
        #settings-inline-host
      footer
    #reader-ruler
    #search-overlay
    partials/post_scripts.html
```

## Asset Load Order

`partials/head.html` controls the main frontend load order.

1. `partials/common_head.html`
2. `css/main.css`
3. every parsed theme CSS file
4. `css/components/settings-late.css`
5. Google font stylesheet and local font imports
6. `window.PIGGY_THEMES = ...`
7. theme effect scripts
8. `preferences.js` synchronously
9. `on-load.js` synchronously
10. storage/settings/reader/search/markdown scripts with `defer`

The synchronous preference bootstrap is deliberate. It applies `data-theme` and reader attributes before the deferred runtime initializes, reducing theme flash.

## CSS Architecture

`css/main.css` imports project CSS in layers:

1. base/reset/global elements
2. fonts and reader preferences
3. layout
4. components
5. cards/grids
6. markdown compatibility and overrides
7. vendor CSS
8. animations

Theme files are loaded separately by `partials/parts/styles.html`, not through `main.css`.

## JavaScript Architecture

Most JavaScript files are IIFEs or standalone initializers that expose a small global when they need cross-module coordination.

Important globals:

| Global | Defined in | Purpose |
| --- | --- | --- |
| `window.PIGGY_THEMES` | `partials/head.html` | Theme metadata parsed from CSS by Python. |
| `window.PiggyPreferences` | `preferences.js` | Preference storage, defaults, validation, attributes, presets. |
| `window.PiggySettingsControls` | `settings-controls.js` | Dynamic settings control rendering/updating. |
| `window.PiggySettingsPage` | `settings-page.js` | Settings page/inline settings lifecycle. |
| `window.PiggyStorage` | `utils/storage.js` | Safe local/session storage helpers. |
| `window.PiggyReaderRuntime` | `reader-runtime.js` | Theme effects, reading ruler, remembered scroll position. |
| `window.PiggyWebGLBackground` | `theme-effects/webgl-background.js` | Factory for shader-based background effects. |

Important document event:

| Event | Detail | Meaning |
| --- | --- | --- |
| `piggy:preferenceschange` | `{ changedKey, preferences }` | Emitted after preference changes; settings UI and reader runtime listen to it. |

## Data Attributes

Frontend behavior is coordinated heavily through `data-*`.

On `<html>`:

- `data-theme`
- `data-theme-type`
- `data-reader-preset`
- `data-reader-contrast`
- `data-reader-font`
- `data-font-theme`
- `data-code-font`
- `data-mono-theme`
- `data-reader-font-size`
- `data-font-size`
- `data-reader-font-size-affects-ui`
- `data-reader-line-height`
- `data-reader-letter-spacing`
- `data-reader-word-spacing`
- `data-reader-paragraph-spacing`
- `data-reader-width`
- `data-reader-reduce-motion`
- `data-reader-focus-mode`
- `data-reader-ruler`
- `data-reader-hide-decorations`
- `data-reader-remember-position`

In templates:

- `data-reader-page-content`: main page content that is hidden when inline settings opens.
- `data-settings-host`: inline settings host.
- `data-settings-inline`: settings page mode.
- `data-settings-render`: target for generated settings controls.
- `data-language-select`: language selector root.
- `data-language-option`: language value to store in cookie.
- `data-level-count`: level selector metadata.

## Frontend Development Tips

- For template structure, start at [Templates](templates.md).
- For a class/variable styling question, check [CSS Reference](css.md) and `css/main.css` import order.
- For behavior, check [JavaScript Reference](javascript.md) and load order.
- For settings changes, update `preferences.js`, `settings-controls.js`, settings templates, and CSS data-attribute selectors together.
- For theme changes, update a theme CSS file metadata block and variable contract; Python will parse metadata automatically.
- For markdown-rendered content, remember the source HTML comes from TurtleConverter and Material/MkDocs conventions, then Piggy CSS/JS overrides it.

