# Settings and Preferences

Piggy's settings system is a reader-preference layer over server-rendered pages. Preferences are stored in the browser, applied as attributes on `<html>`, and consumed by CSS and small JavaScript enhancements.

## Main Files

| File/template | Role |
| --- | --- |
| `static/js/preferences.js` | Preference schema, defaults, presets, persistence, migrations, and attributes. |
| `static/js/on-load.js` | Early bootstrap that applies preferences before deferred scripts run. |
| `static/js/settings-controls.js` | Dynamic settings controls. |
| `static/js/settings-page.js` | Settings page and inline settings lifecycle. |
| `static/js/reader-runtime.js` | Runtime features affected by preferences. |
| `static/css/preferences/reader-preferences.css` | CSS behavior for reader preferences. |
| `static/css/components/settings-menu.css` | Settings UI styling. |
| `static/css/components/settings-late.css` | Late settings preview adjustments. |
| `templates/settings.html` | Direct settings page. |
| `templates/partials/parts/settings_content.html` | Shared settings page content. |

## Preference Store

Current storage:

```text
localStorage["piggy.readerPreferences.v1"]
```

Current store version:

```text
9
```

Stored shape:

```json
{
  "version": 9,
  "values": {
    "readerPreset": "balanced",
    "theme": "light"
  },
  "customValues": null
}
```

The exact `values` object contains all current preference keys after bootstrap. `customValues` preserves the user's custom mix when they switch away from and back to the Custom preset.

Legacy keys still read during migration:

| Legacy key | Current key |
| --- | --- |
| `theme` | `theme` |
| `fontTheme` | `readerFont` |
| `monoTheme` | `codeFont` |
| `fontSize` | `readerFontSize` |

## Preference Keys

| Key | Default | Attribute | Meaning |
| --- | --- | --- | --- |
| `readerPreset` | `default` | `data-reader-preset` | Named preset currently active. |
| `theme` | system preferred theme | `data-theme` | Current visual theme. Also sets `data-theme-type`. |
| `contrast` | `standard` | `data-reader-contrast` | Standard, soft, or strong contrast handling. |
| `readerFont` | `default` | `data-reader-font` and `data-font-theme` | Main content font. |
| `codeFont` | `default` | `data-code-font` and `data-mono-theme` | Code font. |
| `readerFontSize` | `default` | `data-reader-font-size` and `data-font-size` | Content font-size scale. |
| `fontSizeAffectsUi` | `off` | `data-reader-font-size-affects-ui` | Whether font-size preference also scales UI. |
| `readerLineHeight` | `original` | `data-reader-line-height` | Content line-height scale. |
| `readerLetterSpacing` | `default` | `data-reader-letter-spacing` | Content letter spacing. |
| `readerWordSpacing` | `default` | `data-reader-word-spacing` | Content word spacing. |
| `readerParagraphSpacing` | `original` | `data-reader-paragraph-spacing` | Paragraph spacing scale. |
| `readerWidth` | `full` | `data-reader-width` | Markdown reading width. |
| `reduceMotion` | `system` | `data-reader-reduce-motion` | System, quiet, or animated motion behavior. |
| `focusMode` | `off` | `data-reader-focus-mode` | Reduces surrounding page distractions. |
| `readingRuler` | `off` | `data-reader-ruler` | Enables pointer-following reading ruler. |
| `hideDecorations` | `off` | `data-reader-hide-decorations` | Hides visual decorations and animated effects. |
| `rememberPosition` | `off` | `data-reader-remember-position` | Saves/restores scroll position per page. |

`hideDecorations` is synchronized from `reduceMotion`: when `reduceMotion` is `reduce`, `hideDecorations` becomes `on`; otherwise it becomes `off`.

## Option Values

| Key | Values |
| --- | --- |
| `readerPreset` | `default`, `balanced`, `dyslexia`, `lowVision`, `projector`, `lowGlare`, `focus`, `compact`, `randomized`, `custom` |
| `contrast` | `standard`, `soft`, `strong` |
| `readerFont` | `default`, `atkinson`, `lexend`, `lexia`, `open-dyslexic`, `nunito`, `lato`, `quicksand`, `arial`, `verdana`, `bitter`, `georgia` |
| `codeFont` | `default`, `atkinson-mono`, `fira-code`, `roboto-mono`, `jetbrains-mono`, `dm-mono`, `ubuntu-mono`, `kode-mono`, `lucida`, `courier` |
| `readerFontSize` | `xx-small`, `x-small`, `small`, `default`, `large`, `x-large`, `xx-large`, `xxx-large` |
| `fontSizeAffectsUi` | `off`, `on` |
| `readerLineHeight` | `original`, `compact`, `comfortable`, `spacious`, `extra` |
| `readerLetterSpacing` | `default`, `wide`, `extra` |
| `readerWordSpacing` | `default`, `wide`, `extra` |
| `readerParagraphSpacing` | `original`, `compact`, `comfortable`, `spacious`, `extra` |
| `readerWidth` | `narrow`, `medium`, `wide`, `full` |
| `reduceMotion` | `system`, `reduce`, `allow` |
| `focusMode` | `off`, `on` |
| `readingRuler` | `off`, `on` |
| `hideDecorations` | `off`, `on` |
| `rememberPosition` | `off`, `on` |

These values are validated in `preferences.js`. Unknown values fall back to the setting default or theme fallback.

## System Theme Selection

The default theme is a function:

1. If the system prefers more contrast and `high-contrast` exists, use `high-contrast`.
2. Else if the system prefers dark mode and `dark` exists, use `dark`.
3. Else if `light` exists, use `light`.
4. Else use the first known theme path.
5. Else use `dark`.

Known themes come from `window.PIGGY_THEMES`, which is parsed by Python from CSS metadata.

## Presets

| Preset | Main behavior |
| --- | --- |
| `default` | Original site feel, full width, original spacing, system theme. |
| `balanced` | Comfortable line and paragraph spacing, medium reading width. |
| `dyslexia` | Readable/sage theme fallback, Atkinson fonts, larger text, spacious spacing, ruler on, reduced motion. |
| `lowVision` | High-contrast/dark theme fallback, Verdana, very large text, strong contrast, reduced motion. |
| `projector` | Light/readable theme fallback, large classroom-display text, spacious spacing, reduced motion. |
| `lowGlare` | Dark/dusk theme fallback, soft contrast, comfortable spacing, reduced motion. |
| `focus` | Dusk/dark theme fallback, narrow width, focus mode on, reduced motion. |
| `compact` | Smaller text, compact line and paragraph spacing, full width. |
| `randomized` | Randomizes theme, fonts, font size, spacing, and reader width. |
| `custom` | The user's current manual mix. |

When a user changes a preset-controlled value directly, the active preset becomes `custom` unless the caller passes `keepPreset`.

## Applying Preferences

`PiggyPreferences.bootstrap()`:

1. builds default values
2. reads legacy values
3. reads the current stored record
4. migrates older versions
5. normalizes every key
6. refreshes preset values when needed
7. synchronizes effect preferences
8. applies attributes to `document.documentElement`
9. persists the refreshed record

After bootstrap, CSS can style based on attributes without waiting for the rest of the JavaScript.

## Settings UI Modes

Settings can appear in two modes:

| Mode | Entry | Template behavior |
| --- | --- | --- |
| Direct page | `/settings` | `templates/settings.html` renders a standalone settings page. |
| Inline | normal content page | `layout.html` includes `#settings-inline-host`, and `settings-page.js` renders settings without leaving the page. |

The shared body of the settings UI comes from `partials/parts/settings_content.html`. The JavaScript fills dynamic controls into `[data-settings-render]`.

## Settings Source Context

`settings-page.js` uses session storage:

```text
sessionStorage["piggy.settingsSource.v1"]
```

It stores enough source context to return from `/settings` or close inline settings cleanly:

- source page key
- scroll position
- capture timestamp
- source URL

This is why settings can be opened from an assignment page and then return without losing the user's place when remembered position is enabled.

## Reader Runtime Features

Preferences that need JavaScript behavior are handled by `reader-runtime.js`.

| Preference | Runtime behavior |
| --- | --- |
| `theme` | Starts/stops active animated theme effect. |
| `reduceMotion` | Suppresses animations when set to `reduce`, or when system reduction is active and value is `system`. |
| `hideDecorations` | Suppresses decorative theme effects. |
| `readingRuler` | Shows a ruler following pointer/touch position inside markdown content. |
| `rememberPosition` | Saves/restores scroll position using `piggy.readerScrollPositions.v1`. |

CSS handles the rest through data attributes.

## Adding a Preference

1. Add the key to `SETTINGS` in `preferences.js`.
2. Add option metadata to `VALUE_OPTIONS` if the setting is enumerated.
3. Add values to relevant presets.
4. Decide whether it belongs in `PREFERENCE_VALUE_KEYS`.
5. Add control rendering support in `settings-controls.js` if existing control types are not enough.
6. Add CSS selectors in `reader-preferences.css` or the owning component file.
7. Add runtime behavior in `reader-runtime.js` only if CSS cannot do it.
8. Update templates if a new static container/hook is needed.
9. Update this documentation.

