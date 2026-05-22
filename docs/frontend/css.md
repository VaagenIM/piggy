# CSS Reference

Piggy's CSS is static, layered by `piggy/static/css/main.css`, and driven heavily by CSS custom properties. There is no CSS build step. The important rule for development is: `main.css` controls structural import order, while theme CSS files are loaded separately from the template.

## Load Order

`templates/partials/parts/styles.html` loads CSS in this order:

1. `piggy/static/css/main.css`
2. every parsed file in `piggy/static/css/themes/`
3. `piggy/static/css/components/settings-late.css`
4. Google Fonts stylesheet
5. `piggy/static/css/fonts/imports.css`

`settings-late.css` is loaded after themes so that the settings preview can make final spacing adjustments without fighting earlier selectors.

## Main Import Order

`piggy/static/css/main.css` imports project CSS in this exact order:

```css
@import "./base/root.css";
@import "./base/reset.css";
@import "./base/elements.css";
@import "./base/utilities.css";
@import "./base/text-effects.css";
@import "./base/print_overrides.css";

@import "./fonts/font-themes.css";
@import "./fonts/monospace-themes.css";
@import "./fonts/font-size-themes.css";
@import "./preferences/reader-preferences.css";

@import "./layout/page-shell.css";
@import "./layout/site-header.css";
@import "./layout/titles.css";

@import "./components/navigation.css";
@import "./components/breadcrumbs.css";
@import "./components/logo.css";
@import "./components/buttons.css";
@import "./components/search.css";
@import "./components/settings-menu.css";
@import "./components/level-select.css";
@import "./components/language-selector.css";
@import "./components/scroll-to-top.css";
@import "./components/quick-access.css";
@import "./components/assignment-meta.css";
@import "./components/assignment-page.css";
@import "./components/error-page.css";

@import "./components/card-grid.css";
@import "./components/assignment-grid.css";
@import "./components/information-grid.css";

@import "./components/cards/base-card.css";
@import "./components/cards/thumbnails.css";
@import "./components/cards/tags.css";
@import "./components/cards/difficulty.css";
@import "./components/cards/assignment-card.css";
@import "./components/cards/information-card.css";

@import "./markdown/markdown-material-compat.css";
@import "./markdown/markdown-base.css";
@import "./markdown/markdown-code.css";
@import "./markdown/markdown-code-palettes.css";
@import "./markdown/markdown-code-tokens.css";
@import "./markdown/markdown-admonitions.css";
@import "./markdown/markdown-tabs.css";
@import "./markdown/markdown-math.css";
@import "./markdown/markdown-keys.css";
@import "./markdown/markdown-tables.css";

@import "./vendor/katex.css";
@import "./vendor/glightbox.css";

@import "./animations/keyframes.css";
@import "./animations/loader.css";
```

Keep this order in mind when debugging specificity. Base tokens come first, components come before markdown, and vendor CSS is intentionally late because rendered markdown can contain KaTeX and GLightbox markup.

## Base Files

| File | Purpose |
| --- | --- |
| `css/base/root.css` | Root-level custom properties and common global tokens used before themes take over. |
| `css/base/reset.css` | Normalizes browser defaults for predictable layout and typography. |
| `css/base/elements.css` | Baseline styling for ordinary HTML elements. |
| `css/base/utilities.css` | Reusable utility classes used across templates. |
| `css/base/text-effects.css` | Shared text effect helpers used by headings and themed surfaces. |
| `css/base/print.css` | Source print stylesheet. It is not imported directly by `main.css`. |
| `css/base/print_overrides.css` | Generated file imported by `main.css`; produced by `startup_tasks()` from `print.css` and the light theme. |

`print_overrides.css` is generated and ignored by git. If it changes unexpectedly, check `generate_print_css()` in `piggy/utils.py` before editing the generated file by hand.

## Font Files

| File | Purpose |
| --- | --- |
| `css/fonts/imports.css` | Local `@font-face` declarations for static fonts. Loaded from `styles.html`, not imported by `main.css`. |
| `css/fonts/font-themes.css` | Reader font families selected by `data-reader-font` and legacy `data-font-theme`. |
| `css/fonts/monospace-themes.css` | Code font families selected by `data-code-font` and legacy `data-mono-theme`. |
| `css/fonts/font-size-themes.css` | Reader and optional UI font-size scales selected by preference attributes. |

The settings model in `preferences.js` owns the list of selectable fonts. When adding a font, update the settings options, load the font through Google Fonts or `imports.css`, and add the matching CSS selector.

## Reader Preference CSS

| File | Purpose |
| --- | --- |
| `css/preferences/reader-preferences.css` | Applies reader preferences from `data-reader-*` attributes on `<html>`. |

This file owns the CSS side of:

- reader preset hooks
- contrast modes
- line height
- letter spacing
- word spacing
- paragraph spacing
- reader width
- reduced motion
- focus mode
- reading ruler
- hidden decorations

The values are applied by `preferences.js` before most scripts run. CSS should read the attributes; JavaScript should not duplicate layout rules unless the behavior is interactive, such as the reading ruler position.

## Layout Files

| File | Purpose |
| --- | --- |
| `css/layout/page-shell.css` | Page background, `.main-container`, `.background-overlay`, `.content-wrapper`, and main page framing. |
| `css/layout/site-header.css` | Header and navbar layout. |
| `css/layout/titles.css` | Title treatment for folder and assignment pages. |
| `css/layout/responsive.css` | Present but not imported by `main.css`; currently reserved for future responsive rules. |

The layout CSS assumes `templates/layout.html` as the outer structure:

```html
body.main-container
  .background-overlay
  .content-wrapper
    header.site-header
    main
    footer
```

## Component Files

| File | Purpose |
| --- | --- |
| `css/components/navigation.css` | Main navigation, navbar controls, settings/search actions, and top-level nav affordances. |
| `css/components/breadcrumbs.css` | Breadcrumb bar and breadcrumb links rendered by `partials/header/breadcrumbs.html`. |
| `css/components/logo.css` | Piggy logo styling. |
| `css/components/buttons.css` | Shared button and icon-button styling. |
| `css/components/search.css` | Search overlay, input, result list, highlighted snippets, and empty/loading messages. |
| `css/components/settings-menu.css` | Settings page and inline settings UI. This is one of the largest component files. |
| `css/components/settings-late.css` | Late-loaded settings preview adjustment. |
| `css/components/level-select.css` | Level buttons, level dropdown menu, thumbnails, tooltips, and adaptive level controls. |
| `css/components/language-selector.css` | Language selector trigger/dropdown/details styling. |
| `css/components/scroll-to-top.css` | Scroll-to-top component styling. |
| `css/components/quick-access.css` | Quick-access cards on the root page. |
| `css/components/assignment-meta.css` | Assignment metadata blocks such as tags, curriculum links, and metadata layout. |
| `css/components/assignment-page.css` | Assignment page layout around TurtleConverter markdown output. |
| `css/components/error-page.css` | Error page layout and theme-specific error artwork placement. |
| `css/components/card-grid.css` | Shared responsive card grid behavior. |
| `css/components/assignment-grid.css` | Assignment grid variations. |
| `css/components/information-grid.css` | Information grid variations. |

Component selectors are tied to template classes. Before renaming a class in a template, search both `piggy/static/css` and `piggy/static/js`, because behavior and styling often meet on the same class.

## Card CSS

| File | Purpose |
| --- | --- |
| `css/components/cards/base-card.css` | Shared card container, hover, focus, text, and link styling. |
| `css/components/cards/thumbnails.css` | Card thumbnail images, overlays, fallback behavior, and thumbnail sizing. |
| `css/components/cards/tags.css` | Tag chip styling. Tag colors are enhanced by `card_script.js`. |
| `css/components/cards/difficulty.css` | Difficulty indicators used by cards and metadata. |
| `css/components/cards/assignment-card.css` | Assignment-specific card colors and layout. |
| `css/components/cards/information-card.css` | Information-card-specific colors and layout. |

Card variables come from themes. The template family in `templates/objects/` chooses markup, while this CSS family chooses the shared look and the type-specific variations.

## Markdown CSS

Rendered assignment content is generated by TurtleConverter and has Material/MkDocs-like classes. Piggy's markdown CSS adapts that output to the site.

| File | Purpose |
| --- | --- |
| `css/markdown/markdown-material-compat.css` | Compatibility styles for Material/MkDocs generated classes. |
| `css/markdown/markdown-base.css` | General `.md-content` typography, spacing, headings, links, lists, media, and content width. |
| `css/markdown/markdown-code.css` | Code blocks, inline code, code titlebars, and code block layout. |
| `css/markdown/markdown-code-palettes.css` | Code block palette variables. |
| `css/markdown/markdown-code-tokens.css` | Syntax token colors. |
| `css/markdown/markdown-admonitions.css` | Admonition/details styling for notes, tips, warnings, examples, and related blocks. |
| `css/markdown/markdown-tabs.css` | Tabbed markdown block styling. |
| `css/markdown/markdown-math.css` | Math block and inline math styling around KaTeX output. |
| `css/markdown/markdown-keys.css` | Keyboard key markup styling. |
| `css/markdown/markdown-tables.css` | Markdown table layout, borders, and responsive handling. |

When TurtleConverter output changes, start with `markdown-material-compat.css` if the class names changed, then adjust the more specific markdown files.

## Vendor CSS

| File | Purpose |
| --- | --- |
| `css/vendor/katex.css` | Third-party KaTeX styling for math output. |
| `css/vendor/glightbox.css` | Third-party GLightbox styling for image/lightbox behavior. |

Do not refactor vendor CSS as if it were project-owned. If a project-level adjustment is needed, place it in a project markdown/component file after confirming the selector scope.

## Animation CSS

| File | Purpose |
| --- | --- |
| `css/animations/keyframes.css` | Shared keyframes, including transition and animated-theme support. |
| `css/animations/loader.css` | Loading animation styles. |

Reduced-motion handling is split between CSS and JavaScript. CSS should use `prefers-reduced-motion` and `data-reader-reduce-motion`; JavaScript should stop canvas/WebGL effects through `reader-runtime.js`.

## Theme CSS

Theme files live in `piggy/static/css/themes/` and are loaded individually by `styles.html`. They are documented in detail in [Themes and Visual Effects](themes.md).

Every theme file should:

- start with a `/* METADATA ... */` block
- define a `[data-theme="<theme-path>"]` selector
- set the theme variable contract used by layout, cards, markdown, buttons, nav, and settings
- include only theme-specific overrides after the variables

## Custom Property Contract

Themes define the visual contract consumed across the rest of the CSS. The exact variables vary slightly by theme, but the meaningful groups are:

| Group | Examples | Used by |
| --- | --- | --- |
| Core colors | `--piggy-main`, `--piggy-light`, `--piggy-neutral`, `--piggy-dark` | Page shell and base surfaces. |
| Text | `--piggy-text-main`, `--piggy-text-light`, `--piggy-text-dark`, `--piggy-shadow-text` | Body text, cards, nav, headings. |
| Shadows | `--piggy-shadow-box`, `--piggy-shadow-glow` | Cards, buttons, panels, focus states. |
| Cards | `--piggy-card-start`, `--piggy-card-end`, `--piggy-card-border`, `--piggy-text-card` | Base cards and grid cards. |
| Assignment cards | `--piggy-assignment-card-*`, `--piggy-assignment-overlay`, `--piggy-assignment-accent` | Assignment card variants. |
| Information cards | `--piggy-information-card-*`, `--piggy-information-overlay`, `--piggy-information-accent` | Information card variants. |
| Navigation | `--piggy-navbar-*`, `--piggy-text-navbar`, `--piggy-nav-button` | Header and navigation controls. |
| Buttons | `--piggy-button`, `--piggy-button-hover`, `--piggy-button-active`, `--piggy-text-button`, `--piggy-button-border` | Buttons and icon buttons. |
| Breadcrumbs | `--piggy-breadcrumb-*` | Breadcrumb bar. |
| Menus/tooltips | `--piggy-menu-*`, `--piggy-tooltip-*` | Settings, level, language, and tooltip surfaces. |
| Links | `--piggy-link-*` | Markdown and app links. |
| Markdown headings | `--piggy-h1-*` through heading variables | Assignment content headings. |
| Tables | `--piggy-table-*` | Markdown tables. |
| Code | `--piggy-code-*` and token variables | Code blocks and inline code. |
| Admonitions | `--piggy-admonition-*` plus type variants | Notes, warnings, examples, tips. |
| Keys | `--piggy-key-*` | Keyboard shortcut markup. |

When a component needs a new color, prefer extending the theme contract instead of hard-coding a color in the component. That keeps all themes coherent.

## Development Checklist

When changing CSS:

1. Find the owning file by component or markdown area.
2. Check whether the value should come from an existing theme variable.
3. If adding a new variable, add a fallback or update every theme.
4. Confirm data-attribute selectors match `preferences.js`.
5. Check assignment pages and card grids, because they share many variables.
6. Check print behavior if the change affects markdown content or page layout.

