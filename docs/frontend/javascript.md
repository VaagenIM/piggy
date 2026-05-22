# JavaScript Reference

Piggy's JavaScript is plain browser JavaScript. There is no bundler, transpiler, import graph, or framework. Scripts are loaded directly from templates, mostly as IIFEs that attach a small global only when another script needs to call them.

## Load Order

`templates/partials/head.html` loads scripts in this order:

1. `window.PIGGY_THEMES` inline data from Python
2. theme effect scripts with `defer`
3. `js/preferences.js` synchronously
4. `js/on-load.js` synchronously
5. storage/settings/reader/main scripts with `defer`
6. Lunr and search scripts with `defer`
7. markdown overrides with `defer`

The two synchronous scripts are intentional:

- `preferences.js` defines `window.PiggyPreferences`.
- `on-load.js` immediately calls the preference bootstrap so `<html>` receives theme and reader attributes before deferred scripts run.

## Global APIs

| Global | Defined in | Purpose |
| --- | --- | --- |
| `window.PIGGY_THEMES` | `partials/head.html` | Theme metadata parsed from CSS by Python. |
| `window.PiggyPreferences` | `js/preferences.js` | Preference loading, validation, persistence, presets, and data-attribute application. |
| `window.PiggyStorage` | `js/utils/storage.js` | Safe localStorage/sessionStorage map helpers. |
| `window.PiggySettingsControls` | `js/settings-controls.js` | Dynamic settings control rendering and syncing. |
| `window.PiggySettingsPage` | `js/settings-page.js` | Settings page/inline settings lifecycle. |
| `window.PiggyReaderRuntime` | `js/reader-runtime.js` | Reader behavior, theme effects, ruler, and remembered scroll position. |
| `window.PiggyWebGLBackground` | `js/theme-effects/webgl-background.js` | Shared factory for shader backgrounds. |
| `window.startMatrixAnimation` / `stopMatrixAnimation` | `js/theme-effects/matrix-effect.js` | Matrix canvas effect control. |
| `window.startSpaceAnimation` / `stopSpaceAnimation` | `js/theme-effects/space-effect.js` | Space canvas effect control. |
| `window.startDesertShaderAnimation` / `stopDesertShaderAnimation` | `js/theme-effects/shaders/desert-shader.js` | Desert WebGL effect control. |
| `window.startOceanShaderAnimation` / `stopOceanShaderAnimation` | `js/theme-effects/shaders/ocean-shader.js` | Ocean WebGL effect control. |
| `window.startGoldenShaderAnimation` / `stopGoldenShaderAnimation` | `js/theme-effects/shaders/golden-shader.js` | Golden WebGL effect control. |

Keep globals narrow. If a file does not need to be called by another file, let it initialize itself on `DOMContentLoaded`.

## Events

| Event | Emitted by | Listened to by | Meaning |
| --- | --- | --- | --- |
| `piggy:preferenceschange` | `preferences.js` | settings UI, reader runtime | A preference changed. Detail contains `{ changedKey, preferences }`. |

Preference changes should go through `PiggyPreferences.setPreference()`, `setPreferences()`, or `applyPreset()` so this event is emitted consistently.

## Storage Keys

| Key | Storage | Owner | Meaning |
| --- | --- | --- | --- |
| `piggy.readerPreferences.v1` | localStorage | `preferences.js` | Current preference record, version, and custom preset values. |
| `piggy.settingsSource.v1` | sessionStorage | `settings-page.js` | Page context used when opening inline/direct settings and returning. |
| `piggy.readerScrollPositions.v1` | localStorage | `reader-runtime.js` | Remembered scroll positions per `pathname + search`. |
| `theme` | localStorage legacy | `preferences.js` | Legacy theme key migrated into the current preference model. |
| `fontTheme` | localStorage legacy | `preferences.js` | Legacy reader font key. |
| `monoTheme` | localStorage legacy | `preferences.js` | Legacy code font key. |
| `fontSize` | localStorage legacy | `preferences.js` | Legacy reader font size key. |

Use `PiggyStorage` for new local/session map storage. It catches unavailable storage, JSON parse errors, and write failures.

## File Map

| File | Purpose |
| --- | --- |
| `js/preferences.js` | Preference schema, defaults, validation, migration, presets, persistence, and `<html>` attributes. |
| `js/on-load.js` | Early preference bootstrap. |
| `js/utils/storage.js` | Safe storage helpers exposed as `PiggyStorage`. |
| `js/settings-controls.js` | Builds the settings UI controls dynamically from `PiggyPreferences` options. |
| `js/settings-page.js` | Owns the settings page, inline settings panel, tab switching, reset, close/return behavior, and source context. |
| `js/reader-runtime.js` | Starts/stops theme effects, manages reading ruler, remembered scroll position, and reduced-motion response. |
| `js/main.js` | Main DOM-ready coordinator for settings and reader runtime initialization. |
| `js/components/search.js` | Search overlay, Lunr index creation, query handling, result rendering, keyboard shortcut. |
| `js/components/language-selector.js` | Language dropdown/details behavior, sorting, cookie setting, and navigation. |
| `js/components/level-tooltips.js` | Level tooltip placement, level menu placement, and adaptive button-to-menu switching. |
| `js/card_script.js` | Deterministic tag coloring for card tags, with named presets for common languages. |
| `js/markdown-overrides.js` | Progressive enhancements for markdown details, code titlebars, and language labels. |
| `js/theme-effects/matrix-effect.js` | Canvas matrix/rain effect for the Matrix theme. |
| `js/theme-effects/space-effect.js` | Canvas starfield effect for the Space theme. |
| `js/theme-effects/webgl-background.js` | Generic WebGL full-window background renderer used by shader themes. |
| `js/theme-effects/shaders/desert-shader.js` | Desert fragment shader theme effect. |
| `js/theme-effects/shaders/ocean-shader.js` | Ocean fragment shader theme effect. |
| `js/theme-effects/shaders/golden-shader.js` | Golden fragment shader theme effect. |
| `js/modules/lunr.min.js` | Vendor Lunr search library. |

## Application Boot

The normal page boot looks like this:

1. Python renders `window.PIGGY_THEMES`.
2. `preferences.js` defines the preference API.
3. `on-load.js` calls `PiggyPreferences.bootstrap()`.
4. Bootstrap reads defaults, legacy values, and current storage.
5. Bootstrap writes data attributes such as `data-theme`, `data-reader-font`, and `data-reader-width`.
6. Deferred files load.
7. `main.js` initializes settings behavior and reader runtime.
8. Independent component files initialize themselves when the DOM is ready.

This ordering reduces visible theme flashes and lets CSS respond before interactive behavior starts.

## `preferences.js`

This is the foundation for most frontend state.

Responsibilities:

- define the preference store key and version
- define valid options
- define default values
- read legacy keys
- migrate stored records
- normalize unknown values
- apply values to `<html>` attributes
- emit `piggy:preferenceschange`
- expose presets and helper methods

Public API:

| Method/property | Meaning |
| --- | --- |
| `bootstrap()` | Loads, applies, persists, and returns preferences. |
| `getPreferences()` | Returns the current preference object, bootstrapping if needed. |
| `setPreference(key, value, options)` | Changes one preference and emits an event. |
| `setPreferences(values, options)` | Changes multiple preferences and emits one event. |
| `applyPreset(presetId)` | Applies a named, custom, or randomized preset. |
| `getSetting(key)` | Returns setting metadata. |
| `getOptions(key)` | Returns option metadata for a setting. |
| `getThemeType(themePath)` | Looks up a theme's type from `PIGGY_THEMES`. |
| `getSystemPreferredTheme()` | Chooses high-contrast, dark, light, or fallback based on system preferences and available themes. |
| `settings` | The complete setting schema. |
| `presets` | Named preset definitions. |
| `storeKey` / `storeVersion` | Current persistence metadata. |

Changing a preference almost always means updating:

- `preferences.js`
- `settings-controls.js`
- `css/preferences/reader-preferences.css`
- any relevant component/theme CSS
- this documentation

## Settings Scripts

`settings-controls.js` renders controls from the preference/options data. It owns:

- theme cards
- preset cards
- segmented controls
- select/menu-style controls
- toggle controls
- reset-related UI state
- control synchronization after preference changes

`settings-page.js` owns settings page behavior. It supports both:

- direct page mode through `/settings`
- inline mode inside normal pages through `#settings-inline-host`

It tracks the source page so a direct settings visit can return to the page that opened settings. It also closes inline settings with Escape and keeps the source page scroll state coherent.

## Reader Runtime

`reader-runtime.js` handles behavior that is not purely CSS:

- starts the active animated theme effect
- stops all other theme effects before starting a new one
- suppresses effects when reduced motion or hidden decorations are active
- adds a short page transition on theme changes
- tracks the reading ruler inside markdown content
- remembers/restores scroll position when enabled
- responds to system reduced-motion changes

Animated theme switching happens through the current preference object, not by reading classes directly.

## Search Script

`components/search.js` is self-initializing and depends on:

- DOM elements from `partials/search.html`
- `window.lunr` from `modules/lunr.min.js`
- `/api/search-data` from the backend

It eagerly fetches the index in the background. The UI can open before the index is ready; in that case it displays a loading result and reruns the query after the index builds.

See [Search and Navigation](search-and-navigation.md) for query details.

## Markdown Overrides

`markdown-overrides.js` enhances rendered markdown after TurtleConverter has produced HTML.

It owns:

- animated expand/collapse for `details`
- reduced-motion-aware details behavior
- code block titlebars
- language labels for common code block languages

The code titlebar behavior is designed around classes/flags such as `.show-language`, `.show-code-language`, and data flags that do not opt out.

## Theme Effects

Theme effects render into `.background-overlay`.

Canvas effects:

- `matrix-effect.js`
- `space-effect.js`

WebGL shader effects:

- `desert-shader.js`
- `ocean-shader.js`
- `golden-shader.js`

`webgl-background.js` creates a canvas, compiles shaders, feeds uniforms such as `iTime` and `iResolution`, and exposes `start()`/`stop()` through the shader-specific files.

## Vendor JavaScript

`js/modules/lunr.min.js` is third-party/vendor code. Do not style or refactor it like project code. If Lunr behavior needs to change, prefer changing `components/search.js` around the library.

## Development Checklist

When adding frontend behavior:

1. Check whether a template already provides the required DOM hooks.
2. Prefer `data-*` hooks for behavior that should survive class styling changes.
3. If behavior depends on settings, use `PiggyPreferences` and listen for `piggy:preferenceschange`.
4. If it stores data, use a namespaced `piggy.*.v1` key and `PiggyStorage` where useful.
5. Respect reduced motion for animation, transitions, scrolling, and generated effects.
6. Keep initialization safe when markup is missing; many scripts run on every page.

