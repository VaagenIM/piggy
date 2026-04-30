(function () {
  const STORE_KEY = "piggy.readerPreferences.v1";
  const STORE_VERSION = 3;
  const LEGACY_KEYS = {
    theme: "theme",
    readerFont: "fontTheme",
    codeFont: "monoTheme",
    readerFontSize: "fontSize",
  };

  const FONT_OPTIONS = [
    {
      value: "default",
      label: "Noto Sans",
      detail: "Original site font",
      sample: "Clear textbook text",
    },
    {
      value: "atkinson",
      label: "Atkinson Hyperlegible",
      detail: "Readable letter shapes",
      sample: "Clear textbook text",
    },
    {
      value: "lexend",
      label: "Lexend",
      detail: "Spacious reader",
      sample: "Clear textbook text",
    },
    {
      value: "lexia",
      label: "Lexia",
      detail: "Dyslexia friendly",
      sample: "Clear textbook text",
    },
    {
      value: "open-dyslexic",
      label: "OpenDyslexic",
      detail: "Dyslexia friendly",
      sample: "Clear textbook text",
    },
    {
      value: "nunito",
      label: "Nunito",
      detail: "Rounded sans",
      sample: "Clear textbook text",
    },
    {
      value: "lato",
      label: "Lato",
      detail: "Humanist sans",
      sample: "Clear textbook text",
    },
    {
      value: "quicksand",
      label: "Quicksand",
      detail: "Soft rounded",
      sample: "Clear textbook text",
    },
    {
      value: "arial",
      label: "Arial",
      detail: "System",
      sample: "Clear textbook text",
    },
    {
      value: "verdana",
      label: "Verdana",
      detail: "Wide",
      sample: "Clear textbook text",
    },
    {
      value: "bitter",
      label: "Bitter",
      detail: "Serif",
      sample: "Clear textbook text",
    },
    {
      value: "georgia",
      label: "Georgia",
      detail: "Serif",
      sample: "Clear textbook text",
    },
  ];

  const CODE_FONT_OPTIONS = [
    { value: "default", label: "Cascadia Code", detail: "Default" },
    {
      value: "atkinson-mono",
      label: "Atkinson Hyperlegible Mono",
      detail: "Readable symbols",
    },
    { value: "fira-code", label: "Fira Code", detail: "Ligatures" },
    { value: "roboto-mono", label: "Roboto Mono", detail: "Clean" },
    { value: "jetbrains-mono", label: "JetBrains Mono", detail: "Developer" },
    { value: "dm-mono", label: "DM Mono", detail: "Light" },
    { value: "ubuntu-mono", label: "Ubuntu Mono", detail: "Classic" },
    { value: "kode-mono", label: "Kode Mono", detail: "Technical" },
    { value: "lucida", label: "Lucida Console", detail: "System" },
    { value: "courier", label: "Courier New", detail: "System" },
  ];

  const VALUE_OPTIONS = {
    readerPreset: [
      {
        value: "default",
        label: "Default",
        detail: "Close to the original site",
      },
      {
        value: "balanced",
        label: "Balanced",
        detail: "Comfortable modern reader",
      },
      {
        value: "dyslexia",
        label: "Dyslexia friendly",
        detail: "More space and a calmer shape",
      },
      {
        value: "lowVision",
        label: "Low vision",
        detail: "Large text and strong contrast",
      },
      {
        value: "lowGlare",
        label: "Low glare",
        detail: "Softer colors and less motion",
      },
      {
        value: "focus",
        label: "Focus",
        detail: "Quiet page, narrow measure",
      },
      {
        value: "compact",
        label: "Compact",
        detail: "More text on screen",
      },
      {
        value: "custom",
        label: "Custom",
        detail: "Your current mix",
      },
    ],
    contrast: [
      { value: "standard", label: "Standard" },
      { value: "soft", label: "Soft" },
      { value: "strong", label: "Strong" },
    ],
    readerFont: FONT_OPTIONS,
    codeFont: CODE_FONT_OPTIONS,
    readerFontSize: [
      { value: "xx-small", label: "Tiny" },
      { value: "x-small", label: "Smaller" },
      { value: "small", label: "Small" },
      { value: "default", label: "Normal" },
      { value: "large", label: "Large" },
      { value: "x-large", label: "Larger" },
      { value: "xx-large", label: "Massive" },
      { value: "xxx-large", label: "Gigantic" },
    ],
    readerLineHeight: [
      { value: "original", label: "Original" },
      { value: "compact", label: "Compact" },
      { value: "comfortable", label: "Comfortable" },
      { value: "spacious", label: "Spacious" },
      { value: "extra", label: "Extra" },
    ],
    readerLetterSpacing: [
      { value: "default", label: "Default" },
      { value: "wide", label: "Wide" },
      { value: "extra", label: "Extra" },
    ],
    readerWordSpacing: [
      { value: "default", label: "Default" },
      { value: "wide", label: "Wide" },
      { value: "extra", label: "Extra" },
    ],
    readerParagraphSpacing: [
      { value: "original", label: "Original" },
      { value: "compact", label: "Compact" },
      { value: "comfortable", label: "Comfortable" },
      { value: "spacious", label: "Spacious" },
      { value: "extra", label: "Extra" },
    ],
    readerWidth: [
      { value: "narrow", label: "Narrow" },
      { value: "medium", label: "Medium" },
      { value: "wide", label: "Wide" },
      { value: "full", label: "Full" },
    ],
    reduceMotion: [
      { value: "system", label: "System" },
      { value: "reduce", label: "Reduced" },
      { value: "allow", label: "Animated" },
    ],
    focusMode: [
      { value: "off", label: "Off" },
      { value: "on", label: "On" },
    ],
    readingRuler: [
      { value: "off", label: "Off" },
      { value: "on", label: "On" },
    ],
    hideDecorations: [
      { value: "off", label: "Off" },
      { value: "on", label: "On" },
    ],
    rememberPosition: [
      { value: "off", label: "Off" },
      { value: "on", label: "On" },
    ],
  };

  const SETTINGS = {
    readerPreset: {
      defaultValue: "default",
      attribute: "data-reader-preset",
      options: VALUE_OPTIONS.readerPreset,
    },
    theme: {
      defaultValue: getSystemPreferredTheme,
      attribute: "data-theme",
      legacyKey: LEGACY_KEYS.theme,
      afterApply(value) {
        document.documentElement.setAttribute(
          "data-theme-type",
          getThemeType(value),
        );
      },
      normalize(value) {
        return isKnownTheme(value) ? value : getSystemPreferredTheme();
      },
    },
    contrast: {
      defaultValue: "standard",
      attribute: "data-reader-contrast",
      options: VALUE_OPTIONS.contrast,
    },
    readerFont: {
      defaultValue: "default",
      attribute: "data-reader-font",
      compatibilityAttributes: ["data-font-theme"],
      legacyKey: LEGACY_KEYS.readerFont,
      options: VALUE_OPTIONS.readerFont,
    },
    codeFont: {
      defaultValue: "default",
      attribute: "data-code-font",
      compatibilityAttributes: ["data-mono-theme"],
      legacyKey: LEGACY_KEYS.codeFont,
      options: VALUE_OPTIONS.codeFont,
    },
    readerFontSize: {
      defaultValue: "default",
      attribute: "data-reader-font-size",
      compatibilityAttributes: ["data-font-size"],
      legacyKey: LEGACY_KEYS.readerFontSize,
      options: VALUE_OPTIONS.readerFontSize,
    },
    readerLineHeight: {
      defaultValue: "original",
      attribute: "data-reader-line-height",
      options: VALUE_OPTIONS.readerLineHeight,
    },
    readerLetterSpacing: {
      defaultValue: "default",
      attribute: "data-reader-letter-spacing",
      options: VALUE_OPTIONS.readerLetterSpacing,
    },
    readerWordSpacing: {
      defaultValue: "default",
      attribute: "data-reader-word-spacing",
      options: VALUE_OPTIONS.readerWordSpacing,
    },
    readerParagraphSpacing: {
      defaultValue: "original",
      attribute: "data-reader-paragraph-spacing",
      options: VALUE_OPTIONS.readerParagraphSpacing,
    },
    readerWidth: {
      defaultValue: "full",
      attribute: "data-reader-width",
      options: VALUE_OPTIONS.readerWidth,
    },
    reduceMotion: {
      defaultValue: "system",
      attribute: "data-reader-reduce-motion",
      options: VALUE_OPTIONS.reduceMotion,
    },
    focusMode: {
      defaultValue: "off",
      attribute: "data-reader-focus-mode",
      options: VALUE_OPTIONS.focusMode,
    },
    readingRuler: {
      defaultValue: "off",
      attribute: "data-reader-ruler",
      options: VALUE_OPTIONS.readingRuler,
    },
    hideDecorations: {
      defaultValue: "off",
      attribute: "data-reader-hide-decorations",
      options: VALUE_OPTIONS.hideDecorations,
    },
    rememberPosition: {
      defaultValue: "off",
      attribute: "data-reader-remember-position",
      options: VALUE_OPTIONS.rememberPosition,
    },
  };

  const PRESETS = {
    default: {
      label: "Default",
      values: {
        theme: getSystemPreferredTheme,
        contrast: "standard",
        readerFont: "default",
        codeFont: "default",
        readerFontSize: "default",
        readerLineHeight: "original",
        readerLetterSpacing: "default",
        readerWordSpacing: "default",
        readerParagraphSpacing: "original",
        readerWidth: "full",
        reduceMotion: "system",
        focusMode: "off",
        readingRuler: "off",
        hideDecorations: "off",
      },
    },
    balanced: {
      label: "Balanced",
      values: {
        theme: getSystemPreferredTheme,
        contrast: "standard",
        readerFont: "default",
        codeFont: "default",
        readerFontSize: "default",
        readerLineHeight: "comfortable",
        readerLetterSpacing: "default",
        readerWordSpacing: "default",
        readerParagraphSpacing: "comfortable",
        readerWidth: "medium",
        reduceMotion: "system",
        focusMode: "off",
        readingRuler: "off",
        hideDecorations: "off",
      },
    },
    dyslexia: {
      label: "Dyslexia friendly",
      values: {
        theme: preferTheme("readable", "sage"),
        contrast: "soft",
        readerFont: "atkinson",
        codeFont: "atkinson-mono",
        readerFontSize: "large",
        readerLineHeight: "spacious",
        readerLetterSpacing: "wide",
        readerWordSpacing: "wide",
        readerParagraphSpacing: "spacious",
        readerWidth: "medium",
        reduceMotion: "reduce",
        focusMode: "off",
        readingRuler: "on",
        hideDecorations: "on",
      },
    },
    lowVision: {
      label: "Low vision",
      values: {
        theme: preferTheme("high-contrast", "dark"),
        contrast: "strong",
        readerFont: "verdana",
        codeFont: "atkinson-mono",
        readerFontSize: "xx-large",
        readerLineHeight: "spacious",
        readerLetterSpacing: "wide",
        readerWordSpacing: "wide",
        readerParagraphSpacing: "spacious",
        readerWidth: "wide",
        reduceMotion: "reduce",
        focusMode: "off",
        readingRuler: "off",
        hideDecorations: "on",
      },
    },
    lowGlare: {
      label: "Low glare",
      values: {
        theme: preferTheme("sage", "dark"),
        contrast: "soft",
        readerFont: "default",
        codeFont: "default",
        readerFontSize: "default",
        readerLineHeight: "comfortable",
        readerLetterSpacing: "default",
        readerWordSpacing: "default",
        readerParagraphSpacing: "comfortable",
        readerWidth: "medium",
        reduceMotion: "reduce",
        focusMode: "off",
        readingRuler: "off",
        hideDecorations: "on",
      },
    },
    focus: {
      label: "Focus",
      values: {
        theme: preferTheme("dusk", "dark"),
        contrast: "standard",
        readerFont: "default",
        codeFont: "default",
        readerFontSize: "default",
        readerLineHeight: "comfortable",
        readerLetterSpacing: "default",
        readerWordSpacing: "default",
        readerParagraphSpacing: "comfortable",
        readerWidth: "narrow",
        reduceMotion: "reduce",
        focusMode: "on",
        readingRuler: "off",
        hideDecorations: "on",
      },
    },
    compact: {
      label: "Compact",
      values: {
        theme: getSystemPreferredTheme,
        contrast: "standard",
        readerFont: "default",
        codeFont: "default",
        readerFontSize: "small",
        readerLineHeight: "compact",
        readerLetterSpacing: "default",
        readerWordSpacing: "default",
        readerParagraphSpacing: "compact",
        readerWidth: "wide",
        reduceMotion: "system",
        focusMode: "off",
        readingRuler: "off",
        hideDecorations: "off",
      },
    },
  };

  let currentPreferences = null;

  function getThemeList() {
    return Array.isArray(window.PIGGY_THEMES) ? window.PIGGY_THEMES : [];
  }

  function getSystemPreferredTheme() {
    if (
      window.matchMedia &&
      window.matchMedia("(prefers-contrast: more)").matches &&
      isKnownTheme("high-contrast")
    ) {
      return "high-contrast";
    }

    if (
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches &&
      isKnownTheme("dark")
    ) {
      return "dark";
    }

    return isKnownTheme("light") ? "light" : getThemeList()[0]?.path || "dark";
  }

  function getThemeType(themePath) {
    const themeData = getThemeList().find((theme) => theme.path === themePath);
    return themeData?.type || "dark";
  }

  function isKnownTheme(themePath) {
    return getThemeList().some((theme) => theme.path === themePath);
  }

  function preferTheme(preferredTheme, fallbackTheme) {
    return () => {
      if (isKnownTheme(preferredTheme)) return preferredTheme;
      if (isKnownTheme(fallbackTheme)) return fallbackTheme;
      return getSystemPreferredTheme();
    };
  }

  function getDefaultPreferences() {
    return Object.fromEntries(
      Object.entries(SETTINGS).map(([key, setting]) => [
        key,
        resolveValue(setting.defaultValue),
      ]),
    );
  }

  function resolveValue(value) {
    return typeof value === "function" ? value() : value;
  }

  function getValidValues(setting) {
    return setting.options?.map((option) => option.value) || null;
  }

  function normalizePreference(key, value) {
    const setting = SETTINGS[key];
    if (!setting) return value;

    if (setting.normalize) {
      return setting.normalize(value);
    }

    const validValues = getValidValues(setting);
    if (validValues && !validValues.includes(value)) {
      return resolveValue(setting.defaultValue);
    }

    return value ?? resolveValue(setting.defaultValue);
  }

  function safeGetItem(key) {
    try {
      return window.localStorage?.getItem(key) ?? null;
    } catch {
      return null;
    }
  }

  function safeSetItem(key, value) {
    try {
      window.localStorage?.setItem(key, value);
      return true;
    } catch {
      return false;
    }
  }

  function safeParse(rawValue) {
    if (!rawValue) return null;

    try {
      const parsed = JSON.parse(rawValue);
      return parsed && typeof parsed === "object" ? parsed : null;
    } catch {
      return null;
    }
  }

  function getStoredPreferenceValues() {
    const stored = safeParse(safeGetItem(STORE_KEY));
    if (!stored) return {};

    if (stored.values && typeof stored.values === "object") {
      return migrateStoredPreferenceValues(stored.values, stored.version);
    }

    const { version, ...values } = stored;
    return migrateStoredPreferenceValues(values, version);
  }

  function migrateStoredPreferenceValues(values, version = 0) {
    const migratedValues = { ...values };

    if (version < 2 && migratedValues.readerPreset === "default") {
      migratedValues.readerPreset = "balanced";
    }

    if (
      version < 3 &&
      ["dyslexia", "lowVision"].includes(migratedValues.readerPreset) &&
      (!migratedValues.codeFont || migratedValues.codeFont === "default")
    ) {
      migratedValues.codeFont = "atkinson-mono";
    }

    return migratedValues;
  }

  function getLegacyPreferences() {
    const preferences = {};

    Object.entries(SETTINGS).forEach(([key, setting]) => {
      if (!setting.legacyKey) return;

      const value = safeGetItem(setting.legacyKey);
      if (value !== null) {
        preferences[key] = value;
      }
    });

    return preferences;
  }

  function loadPreferences() {
    const defaults = getDefaultPreferences();
    const legacy = getLegacyPreferences();
    const stored = getStoredPreferenceValues();
    const preferences = { ...defaults, ...legacy, ...stored };

    Object.keys(SETTINGS).forEach((key) => {
      preferences[key] = normalizePreference(key, preferences[key]);
    });

    return preferences;
  }

  function persistPreferences(preferences) {
    safeSetItem(
      STORE_KEY,
      JSON.stringify({
        version: STORE_VERSION,
        values: preferences,
      }),
    );
  }

  function applyPreferences(preferences) {
    Object.entries(SETTINGS).forEach(([key, setting]) => {
      const value = normalizePreference(key, preferences[key]);
      const attributes = [
        setting.attribute,
        ...(setting.compatibilityAttributes || []),
      ].filter(Boolean);

      attributes.forEach((attribute) => {
        document.documentElement.setAttribute(attribute, value);
      });

      setting.afterApply?.(value, preferences);
    });
  }

  function emitPreferencesChange(changedKey, preferences) {
    document.dispatchEvent(
      new CustomEvent("piggy:preferenceschange", {
        detail: {
          changedKey,
          preferences: { ...preferences },
        },
      }),
    );
  }

  function bootstrap() {
    currentPreferences = loadPreferences();
    applyPreferences(currentPreferences);
    persistPreferences(currentPreferences);

    window.systemPreferredTheme = getSystemPreferredTheme();

    return { ...currentPreferences };
  }

  function getPreferences() {
    if (!currentPreferences) {
      return bootstrap();
    }

    return { ...currentPreferences };
  }

  function setPreference(key, value, options = {}) {
    if (!SETTINGS[key]) return getPreferences();

    const preferences = getPreferences();
    preferences[key] = normalizePreference(key, value);

    if (key !== "readerPreset" && options.keepPreset !== true) {
      preferences.readerPreset = "custom";
    }

    currentPreferences = preferences;
    applyPreferences(currentPreferences);
    persistPreferences(currentPreferences);
    emitPreferencesChange(key, currentPreferences);

    return { ...currentPreferences };
  }

  function setPreferences(values, options = {}) {
    const preferences = getPreferences();

    Object.entries(values).forEach(([key, value]) => {
      if (!SETTINGS[key]) return;
      preferences[key] = normalizePreference(key, resolveValue(value));
    });

    if (options.preset) {
      preferences.readerPreset = options.preset;
    } else if (options.keepPreset !== true) {
      preferences.readerPreset = "custom";
    }

    currentPreferences = preferences;
    applyPreferences(currentPreferences);
    persistPreferences(currentPreferences);
    emitPreferencesChange(options.changedKey || "multiple", currentPreferences);

    return { ...currentPreferences };
  }

  function applyPreset(presetId) {
    const preset = PRESETS[presetId];
    if (!preset) return getPreferences();

    const values = Object.fromEntries(
      Object.entries(preset.values).map(([key, value]) => [
        key,
        resolveValue(value),
      ]),
    );

    return setPreferences(values, {
      preset: presetId,
      changedKey: "readerPreset",
    });
  }

  function getSetting(key) {
    return SETTINGS[key] ? { ...SETTINGS[key] } : null;
  }

  function getOptions(key) {
    return VALUE_OPTIONS[key] ? [...VALUE_OPTIONS[key]] : [];
  }

  window.PiggyPreferences = {
    bootstrap,
    getPreferences,
    setPreference,
    setPreferences,
    applyPreset,
    getSetting,
    getOptions,
    getThemeType,
    getSystemPreferredTheme,
    settings: SETTINGS,
    presets: PRESETS,
    storeKey: STORE_KEY,
    storeVersion: STORE_VERSION,
  };
})();
