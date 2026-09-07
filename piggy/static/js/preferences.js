(function () {
  const STORE_KEY = "piggy.readerPreferences.v1";
  const STORE_VERSION = 9;
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
      detail: "Standard",
    },
    {
      value: "atkinson",
      label: "Atkinson Hyperlegible",
      detail: "Lesbare bokstaver",
    },
    {
      value: "lexend",
      label: "Lexend",
      detail: "Tekst med mye mellomrom",
    },
    {
      value: "lexia",
      label: "Lexia",
      detail: "Dysleksivennlig",
    },
    {
      value: "open-dyslexic",
      label: "OpenDyslexic",
      detail: "Dysleksivennlig",
    },
    {
      value: "nunito",
      label: "Nunito",
      detail: "Rund skrifttype",
    },
    {
      value: "lato",
      label: "Lato",
      detail: "Humanist sans",
    },
    {
      value: "quicksand",
      label: "Quicksand",
      detail: "Myk og rund skrifttype",
    },
    {
      value: "arial",
      label: "Arial",
      detail: "System",
    },
    {
      value: "verdana",
      label: "Verdana",
      detail: "Bred skrift",
    },
    {
      value: "bitter",
      label: "Bitter",
      detail: "Serif skrift",
    },
    {
      value: "georgia",
      label: "Georgia",
      detail: "Serif skrift",
    },
  ];

  const CODE_FONT_OPTIONS = [
    { value: "default", label: "Cascadia Code", detail: "Default" },
    {
      value: "atkinson-mono",
      label: "Atkinson Hyperlegible Mono",
      detail: "Lesbare symboler",
    },
    { value: "fira-code", label: "Fira Code", detail: "Ligaturer" },
    { value: "roboto-mono", label: "Roboto Mono", detail: "Clean" },
    { value: "jetbrains-mono", label: "JetBrains Mono", detail: "Utvikler" },
    { value: "dm-mono", label: "DM Mono", detail: "Light" },
    { value: "ubuntu-mono", label: "Ubuntu Mono", detail: "Klassisk" },
    { value: "kode-mono", label: "Kode Mono", detail: "Teknisk" },
    { value: "lucida", label: "Lucida Console", detail: "System" },
    { value: "courier", label: "Courier New", detail: "System" },
  ];

  const VALUE_OPTIONS = {
    readerPreset: [
      {
        value: "default",
        label: "Standard",
        detail: "Standard utseende på piggy",
      },
      {
        value: "balanced",
        label: "Balansert",
        detail: "Komfortabel med moderne tekst",
      },
      {
        value: "dyslexia",
        label: "Dysleksivennlig",
        detail: "Mer mellomrom og en vennligere form",
      },
      {
        value: "lowVision",
        label: "Nedsatt syn",
        detail: "Stor tekst og sterke kontraster",
      },
      {
        value: "projector",
        label: "Prosjektor",
        detail: "For å vises på skjerm i klasserommet",
      },
      {
        value: "lowGlare",
        label: "Lav blending",
        detail: "Dempede farger og mindre bevegelse",
      },
      {
        value: "focus",
        label: "Fokus",
        detail: "Stille side med en smal leser",
      },
      {
        value: "compact",
        label: "Kompakt",
        detail: "Tett visning",
      },
      {
        value: "randomized",
        label: "Tilfeldig",
        detail: "Gjør alt tilfeldig",
      },
      {
        value: "custom",
        label: "Egendefinert",
        detail: "Dine nåværende innstillinger",
      },
    ],
    contrast: [
      { value: "standard", label: "Standard" },
      { value: "soft", label: "Myk" },
      { value: "strong", label: "Sterke" },
    ],
    accentColor: [
      { value: "0", label: "Standard", hex: "#2f7dd1" },
      { value: "1", label: "Rosé", hex: "#d6469e" },
      { value: "2", label: "Grønn", hex: "#2e9e5b" },
      { value: "3", label: "Rav", hex: "#c98a2e" },
      { value: "4", label: "Fiolett", hex: "#8a4fd1" },
      { value: "5", label: "Blågrønn", hex: "#1f9e9e" },
      { value: "6", label: "Crimson", hex: "#c9384f" },
      { value: "7", label: "Lime", hex: "#a3b52e" },
    ],
    readerFont: FONT_OPTIONS,
    codeFont: CODE_FONT_OPTIONS,
    readerFontSize: [
      { value: "xx-small", label: "Bitteliten" },
      { value: "x-small", label: "Mindre" },
      { value: "small", label: "Liten" },
      { value: "default", label: "Vanlig" },
      { value: "large", label: "Stor" },
      { value: "x-large", label: "Større" },
      { value: "xx-large", label: "Massiv" },
      { value: "xxx-large", label: "Gigantisk" },
    ],
    fontSizeAffectsUi: [
      { value: "off", label: "Bare innhold" },
      { value: "on", label: "Innhold og UI" },
    ],
    readerLineHeight: [
      { value: "original", label: "Standard" },
      { value: "compact", label: "Kompakt" },
      { value: "comfortable", label: "Behagelig" },
      { value: "spacious", label: "Mye mellomrom" },
      { value: "extra", label: "Ekstra mellomrom" },
    ],
    readerLetterSpacing: [
      { value: "default", label: "Standard" },
      { value: "wide", label: "Bred" },
      { value: "extra", label: "Ekstra bred" },
    ],
    readerWordSpacing: [
      { value: "default", label: "Standard" },
      { value: "wide", label: "Bred" },
      { value: "extra", label: "Ekstra bred" },
    ],
    readerParagraphSpacing: [
      { value: "original", label: "Standard" },
      { value: "compact", label: "Kompakt" },
      { value: "comfortable", label: "Behagelig" },
      { value: "spacious", label: "Mye mellomrom" },
      { value: "extra", label: "Ekstra mellomrom" },
    ],
    readerWidth: [
      { value: "narrow", label: "Smal" },
      { value: "medium", label: "Standard" },
      { value: "wide", label: "Bred" },
      { value: "full", label: "Full bredde" },
    ],
    reduceMotion: [
      { value: "system", label: "System" },
      { value: "reduce", label: "Lite" },
      { value: "allow", label: "Animert" },
    ],
    focusMode: [
      { value: "off", label: "Av" },
      { value: "on", label: "På" },
    ],
    readingRuler: [
      { value: "off", label: "Av" },
      { value: "on", label: "På" },
    ],
    hideDecorations: [
      { value: "off", label: "Av" },
      { value: "on", label: "På" },
    ],
    rememberPosition: [
      { value: "off", label: "Av" },
      { value: "on", label: "På" },
    ],
  };

  (function applyI18n() {
    const i18n =
      window.PIGGY_I18N && typeof window.PIGGY_I18N === "object"
        ? window.PIGGY_I18N
        : {};

    Object.keys(VALUE_OPTIONS).forEach((key) => {
      const group = i18n[key];
      if (!group) return;

      VALUE_OPTIONS[key].forEach((option) => {
        const translated = group[option.value];
        if (!translated) return;
        if (translated.label !== undefined) option.label = translated.label;
        if (translated.detail !== undefined) option.detail = translated.detail;
      });
    });
  })();

  function getReadableTextColor(hex) {
    const match = /^#?([0-9a-f]{6})$/i.exec((hex || "").trim());
    if (!match) return null;

    const value = parseInt(match[1], 16);
    const r = (value >> 16) & 255;
    const g = (value >> 8) & 255;
    const b = value & 255;
    const brightness = (r * 299 + g * 587 + b * 114) / 1000;

    return brightness > 140 ? "#000000" : "#ffffff";
  }

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
    accentColor: {
      defaultValue: "0",
      attribute: "data-accent-color",
      options: VALUE_OPTIONS.accentColor,
      afterApply(value) {
        if (value === "0") {
          document.documentElement.style.removeProperty(
            "--piggy-accent-text-override",
          );
          return;
        }

        const resolved = getComputedStyle(document.documentElement)
          .getPropertyValue("--piggy-accent-override")
          .trim();
        const textColor = getReadableTextColor(resolved);

        if (textColor) {
          document.documentElement.style.setProperty(
            "--piggy-accent-text-override",
            textColor,
          );
        } else {
          document.documentElement.style.removeProperty(
            "--piggy-accent-text-override",
          );
        }
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
    fontSizeAffectsUi: {
      defaultValue: "off",
      attribute: "data-reader-font-size-affects-ui",
      options: VALUE_OPTIONS.fontSizeAffectsUi,
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
        fontSizeAffectsUi: "off",
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
        fontSizeAffectsUi: "off",
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
        fontSizeAffectsUi: "off",
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
        fontSizeAffectsUi: "off",
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
    projector: {
      label: "Projector",
      values: {
        theme: preferTheme("light", "readable"),
        contrast: "standard",
        readerFont: "verdana",
        codeFont: "atkinson-mono",
        readerFontSize: "xx-large",
        fontSizeAffectsUi: "off",
        readerLineHeight: "spacious",
        readerLetterSpacing: "default",
        readerWordSpacing: "default",
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
        theme: preferTheme("dark", "dusk"),
        contrast: "soft",
        readerFont: "default",
        codeFont: "default",
        readerFontSize: "default",
        fontSizeAffectsUi: "off",
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
        fontSizeAffectsUi: "off",
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
        fontSizeAffectsUi: "off",
        readerLineHeight: "compact",
        readerLetterSpacing: "default",
        readerWordSpacing: "default",
        readerParagraphSpacing: "compact",
        readerWidth: "full",
        reduceMotion: "system",
        focusMode: "off",
        readingRuler: "off",
        hideDecorations: "off",
      },
    },
  };

  const PREFERENCE_VALUE_KEYS = [
    ...new Set(
      Object.values(PRESETS).flatMap((preset) => Object.keys(preset.values)),
    ),
  ];
  const RANDOMIZED_VALUE_KEYS = [
    "theme",
    "readerFont",
    "codeFont",
    "readerFontSize",
    "readerLineHeight",
    "readerLetterSpacing",
    "readerWordSpacing",
    "readerParagraphSpacing",
    "readerWidth",
  ];

  let currentPreferences = null;
  let currentCustomValues = null;

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

  function getStoredPreferenceRecord() {
    const stored = safeParse(safeGetItem(STORE_KEY));
    if (!stored) {
      return {
        version: 0,
        values: {},
        customValues: null,
      };
    }

    if (stored.values && typeof stored.values === "object") {
      return {
        version: stored.version || 0,
        values: migrateStoredPreferenceValues(stored.values, stored.version),
        customValues: migrateStoredCustomValues(
          stored.customValues,
          stored.version,
        ),
      };
    }

    const { version, ...values } = stored;
    return {
      version: version || 0,
      values: migrateStoredPreferenceValues(values, version),
      customValues: null,
    };
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

    if (
      version < 4 &&
      migratedValues.readerPreset === "projector" &&
      migratedValues.contrast === "strong"
    ) {
      migratedValues.contrast = "standard";
    }

    return migratedValues;
  }

  function migrateStoredCustomValues(values, version = 0) {
    if (!values || typeof values !== "object") return null;

    const migratedValues = migrateStoredPreferenceValues(values, version);
    delete migratedValues.readerPreset;
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
    const storedRecord = getStoredPreferenceRecord();
    const stored = storedRecord.values;
    const shouldRefreshPreset = Object.prototype.hasOwnProperty.call(
      stored,
      "readerPreset",
    );
    let preferences = { ...defaults, ...legacy, ...stored };

    Object.keys(SETTINGS).forEach((key) => {
      preferences[key] = normalizePreference(key, preferences[key]);
    });

    preferences = refreshPresetPreferences(preferences, shouldRefreshPreset);
    preferences = syncEffectPreferences(preferences);

    currentCustomValues = normalizeCustomValues(
      storedRecord.customValues,
      preferences,
    );

    return preferences;
  }

  function refreshPresetPreferences(preferences, shouldRefresh) {
    const presetId = preferences.readerPreset;
    if (
      !shouldRefresh ||
      !presetId ||
      presetId === "custom" ||
      !PRESETS[presetId]
    ) {
      return preferences;
    }

    return {
      ...preferences,
      ...getPresetValues(presetId),
      readerPreset: presetId,
    };
  }

  function persistPreferences(preferences) {
    safeSetItem(
      STORE_KEY,
      JSON.stringify({
        version: STORE_VERSION,
        values: preferences,
        customValues: getPersistedCustomValues(preferences),
      }),
    );
  }

  function getPersistedCustomValues(preferences) {
    if (currentCustomValues) return { ...currentCustomValues };
    if (preferences.readerPreset === "custom") {
      return getPreferenceValues(preferences);
    }

    return null;
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
    if (key === "readerPreset" && value === "custom") {
      return applyPreset("custom");
    }

    const preferences = getPreferences();
    preferences[key] = normalizePreference(key, value);
    const changesPresetValue = PREFERENCE_VALUE_KEYS.includes(key);
    syncEffectPreferences(preferences);

    if (changesPresetValue && options.keepPreset !== true) {
      preferences.readerPreset = "custom";
    }

    if (changesPresetValue && preferences.readerPreset === "custom") {
      currentCustomValues = getPreferenceValues(preferences);
    }

    currentPreferences = preferences;
    applyPreferences(currentPreferences);
    persistPreferences(currentPreferences);
    emitPreferencesChange(key, currentPreferences);

    return { ...currentPreferences };
  }

  function setPreferences(values, options = {}) {
    const preferences = getPreferences();
    const changesPresetValue = Object.keys(values).some((key) =>
      PREFERENCE_VALUE_KEYS.includes(key),
    );

    Object.entries(values).forEach(([key, value]) => {
      if (!SETTINGS[key]) return;
      preferences[key] = normalizePreference(key, resolveValue(value));
    });
    syncEffectPreferences(preferences);

    if (options.preset) {
      preferences.readerPreset = options.preset;
    } else if (changesPresetValue && options.keepPreset !== true) {
      preferences.readerPreset = "custom";
    }

    if (changesPresetValue && preferences.readerPreset === "custom") {
      currentCustomValues = getPreferenceValues(preferences);
    }

    currentPreferences = preferences;
    applyPreferences(currentPreferences);
    persistPreferences(currentPreferences);
    emitPreferencesChange(options.changedKey || "multiple", currentPreferences);

    return { ...currentPreferences };
  }

  function applyPreset(presetId) {
    if (presetId === "custom") {
      const values =
        currentCustomValues || getPreferenceValues(getPreferences());
      return setPreferences(values, {
        preset: "custom",
        changedKey: "readerPreset",
      });
    }

    if (presetId === "randomized") {
      return setPreferences(getRandomizedPresetValues(), {
        preset: "randomized",
        changedKey: "readerPreset",
      });
    }

    const preset = PRESETS[presetId];
    if (!preset) return getPreferences();

    return setPreferences(getPresetValues(presetId), {
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

  function getPreferenceValues(preferences) {
    return Object.fromEntries(
      PREFERENCE_VALUE_KEYS.map((key) => [
        key,
        normalizePreference(key, preferences[key]),
      ]),
    );
  }

  function getPresetValues(presetId) {
    const preset = PRESETS[presetId];
    if (!preset) return {};

    return Object.fromEntries(
      Object.entries(preset.values).map(([key, value]) => [
        key,
        normalizePreference(key, resolveValue(value)),
      ]),
    );
  }

  function getRandomizedPresetValues() {
    return {
      ...Object.fromEntries(
        RANDOMIZED_VALUE_KEYS.map((key) => [key, getRandomizedValue(key)]),
      ),
      fontSizeAffectsUi: "off",
    };
  }

  function getRandomizedValue(key) {
    if (key === "theme") {
      const themes = getThemeList()
        .map((theme) => theme.path)
        .filter(Boolean);
      return chooseRandom(themes) || getSystemPreferredTheme();
    }

    const values = getValidValues(SETTINGS[key]) || [];
    return chooseRandom(values) || resolveValue(SETTINGS[key]?.defaultValue);
  }

  function chooseRandom(values) {
    if (!Array.isArray(values) || values.length === 0) return null;
    return values[Math.floor(Math.random() * values.length)];
  }

  function syncEffectPreferences(preferences) {
    preferences.hideDecorations =
      preferences.reduceMotion === "reduce" ? "on" : "off";
    return preferences;
  }

  function normalizeCustomValues(values, preferences) {
    const source =
      values && typeof values === "object"
        ? values
        : preferences.readerPreset === "custom"
          ? preferences
          : null;

    if (!source) return null;

    return syncEffectPreferences(
      Object.fromEntries(
        PREFERENCE_VALUE_KEYS.map((key) => [
          key,
          normalizePreference(key, source[key] ?? preferences[key]),
        ]),
      ),
    );
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
