document.addEventListener("DOMContentLoaded", () => {
  const preferencesApi = window.PiggyPreferences;
  if (!preferencesApi) return;

  const settingsPage = document.getElementById("settings-page");
  const settingsTabs = settingsPage?.querySelector("[data-settings-tabs]");
  const settingsButton = document.getElementById("settings-button");
  const returnLink = document.getElementById("settings-return-link");
  const resetButton = document.getElementById("settings-reset-button");
  const readerRuler = document.getElementById("reader-ruler");
  const markdownContent = document.querySelector(
    "main .md-content:not(.settings-reader-preview)",
  );

  const SETTINGS_SOURCE_KEY = "piggy.settingsSource.v1";
  const SCROLL_KEY = "piggy.readerScrollPositions.v1";

  const CONTROL_LABELS = {
    contrast: "Contrast",
    readerFont: "Reading font",
    codeFont: "Code font",
    readerFontSize: "Text size",
    readerLineHeight: "Line height",
    readerLetterSpacing: "Letter spacing",
    readerWordSpacing: "Word spacing",
    readerParagraphSpacing: "Paragraph spacing",
    readerWidth: "Reading width",
    focusMode: "Focus mode",
    readingRuler: "Reading ruler",
    hideDecorations: "Quiet page",
    reduceMotion: "Motion",
    rememberPosition: "Remember position",
  };

  const TOGGLE_LABELS = {
    focusMode: "Dim navigation while reading",
    readingRuler: "Show reading ruler",
    hideDecorations: "Hide animated backgrounds",
    rememberPosition: "Remember where you stopped reading",
  };

  const PRESET_ICONS = {
    default: "settings",
    balanced: "scale",
    dyslexia: "book",
    lowVision: "eye",
    projector: "monitor",
    lowGlare: "moon",
    focus: "target",
    compact: "rows",
    custom: "sliders",
  };

  const ICON_PATHS = {
    book: [
      "M2 6.5A2.5 2.5 0 0 1 4.5 4H10a2 2 0 0 1 2 2v14a2 2 0 0 0-2-2H4.5A2.5 2.5 0 0 0 2 20.5Z",
      "M22 6.5A2.5 2.5 0 0 0 19.5 4H14a2 2 0 0 0-2 2v14a2 2 0 0 1 2-2h5.5a2.5 2.5 0 0 1 2.5 2.5Z",
    ],
    code: ["m16 18 6-6-6-6", "m8 6-6 6 6 6"],
    eye: [
      "M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z",
      "M12 15.5A3.5 3.5 0 1 0 12 8a3.5 3.5 0 0 0 0 7.5Z",
    ],
    leaf: [
      "M5 21c8 0 14-6 14-14V3h-4C7 3 3 7 3 15c0 2.2.8 4.1 2 6Z",
      "M3 21c4-7 8-10 16-14",
    ],
    monitor: ["M4 5h16v11H4Z", "M8 21h8", "M12 16v5"],
    moon: ["M21 12.8A8.5 8.5 0 1 1 11.2 3 7 7 0 0 0 21 12.8Z"],
    rows: ["M4 6h16", "M4 12h16", "M4 18h16"],
    scale: ["M12 3v18", "M5 6h14", "M6 6l-3 7h6Z", "M18 6l-3 7h6Z"],
    settings: [
      "M12 15.5A3.5 3.5 0 1 0 12 8a3.5 3.5 0 0 0 0 7.5Z",
      "M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 8.92 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9c.16.62.66 1.09 1.28 1.09H21a2 2 0 0 1 0 4h-.32c-.62 0-1.12.47-1.28.91Z",
    ],
    sliders: [
      "M4 6h8",
      "M16 6h4",
      "M14 4v4",
      "M4 12h4",
      "M12 12h8",
      "M10 10v4",
      "M4 18h10",
      "M18 18h2",
      "M16 16v4",
    ],
    sparkle: [
      "M12 3l1.6 5.2L19 10l-5.4 1.8L12 17l-1.6-5.2L5 10l5.4-1.8Z",
      "M19 15l.7 2.3L22 18l-2.3.7L19 21l-.7-2.3L16 18l2.3-.7Z",
    ],
    sun: [
      "M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z",
      "M12 2v2",
      "M12 20v2",
      "M4.93 4.93l1.41 1.41",
      "M17.66 17.66l1.41 1.41",
      "M2 12h2",
      "M20 12h2",
      "M6.34 17.66l-1.41 1.41",
      "M19.07 4.93l-1.41 1.41",
    ],
    target: [
      "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z",
      "M12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12Z",
      "M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z",
    ],
    waves: [
      "M2 8c2 0 2-2 4-2s2 2 4 2 2-2 4-2 2 2 4 2 2-2 4-2",
      "M2 14c2 0 2-2 4-2s2 2 4 2 2-2 4-2 2 2 4 2 2-2 4-2",
    ],
  };

  let lastPreferences = preferencesApi.getPreferences();
  let scrollSaveTimeout = null;
  let settingsSourceContext = null;

  settingsSourceContext = getSettingsSourceContext();
  initializeSettingsTabs();
  renderSettingsControls();
  updateSettingsControls(lastPreferences);
  updateThemeEffects(lastPreferences);
  updateReturnLink();
  initializeReaderRuler();
  initializeRememberedPosition();

  settingsButton?.addEventListener("click", captureSettingsSource);
  resetButton?.addEventListener("click", () =>
    preferencesApi.applyPreset("default"),
  );

  settingsPage?.addEventListener("click", handleSettingsClick);
  settingsPage?.addEventListener("change", handleSettingsChange);

  document.addEventListener("piggy:preferenceschange", (event) => {
    const nextPreferences = event.detail.preferences;
    const changedKey = event.detail.changedKey;

    updateSettingsControls(nextPreferences);
    updateThemeEffects(nextPreferences, changedKey);

    if (changedKey === "rememberPosition" && settingsPage) {
      saveSourceScrollPosition();
    } else if (changedKey === "rememberPosition") {
      saveScrollPosition();
    }

    lastPreferences = nextPreferences;
  });

  window.addEventListener(
    "scroll",
    () => {
      if (settingsPage) return;
      if (preferencesApi.getPreferences().rememberPosition !== "on") return;

      window.clearTimeout(scrollSaveTimeout);
      scrollSaveTimeout = window.setTimeout(saveScrollPosition, 160);
    },
    { passive: true },
  );
  window.addEventListener("pagehide", () => {
    if (!settingsPage) saveScrollPosition();
  });

  window
    .matchMedia?.("(prefers-reduced-motion: reduce)")
    .addEventListener?.("change", () => {
      updateThemeEffects(preferencesApi.getPreferences(), "reduceMotion");
    });

  function renderSettingsControls() {
    renderPresetCards(getRenderTarget("presets"));
    renderThemeCards(getRenderTarget("themes"));
    renderSegmentedControl("contrast", getRenderTarget("contrast"));

    renderSelectControl("readerFont", getRenderTarget("readerFont"));
    renderSelectControl("codeFont", getRenderTarget("codeFont"));
    renderSegmentedControl("readerFontSize", getRenderTarget("readerFontSize"));

    renderSegmentedControl(
      "readerLineHeight",
      getRenderTarget("readerLineHeight"),
    );
    renderSegmentedControl(
      "readerLetterSpacing",
      getRenderTarget("readerLetterSpacing"),
    );
    renderSegmentedControl(
      "readerWordSpacing",
      getRenderTarget("readerWordSpacing"),
    );
    renderSegmentedControl(
      "readerParagraphSpacing",
      getRenderTarget("readerParagraphSpacing"),
    );
    renderSegmentedControl("readerWidth", getRenderTarget("readerWidth"));

    renderToggleControl("focusMode", getRenderTarget("focusMode"));
    renderToggleControl("readingRuler", getRenderTarget("readingRuler"));
    renderToggleControl("hideDecorations", getRenderTarget("hideDecorations"));
    renderSegmentedControl("reduceMotion", getRenderTarget("reduceMotion"));
    renderToggleControl(
      "rememberPosition",
      getRenderTarget("rememberPosition"),
    );
  }

  function getRenderTarget(name) {
    return settingsPage?.querySelector(`[data-settings-render="${name}"]`);
  }

  function renderPresetCards(container) {
    if (!container) return;

    container.replaceChildren();

    preferencesApi.getOptions("readerPreset").forEach((preset) => {
      const button = document.createElement("button");
      button.className = "settings-option-card";
      button.type = "button";
      button.dataset.prefId = "readerPreset";
      button.dataset.prefValue = preset.value;
      button.setAttribute("aria-pressed", "false");

      const header = document.createElement("span");
      header.className = "settings-option-header";

      const title = document.createElement("span");
      title.className = "settings-option-title";
      title.textContent = preset.label;

      const detail = document.createElement("span");
      detail.className = "settings-option-detail";
      detail.textContent = preset.detail;

      header.append(createSettingsIcon(PRESET_ICONS[preset.value]), title);
      button.append(header, detail);
      container.append(button);
    });
  }

  function renderThemeCards(container) {
    if (!container) return;

    container.replaceChildren();

    getThemes().forEach((theme) => {
      const button = document.createElement("button");
      button.className = "theme-card";
      button.type = "button";
      button.dataset.prefId = "theme";
      button.dataset.prefValue = theme.path;
      button.setAttribute("aria-pressed", "false");

      const preview = document.createElement("span");
      preview.className = "theme-card-preview";
      preview.setAttribute("aria-hidden", "true");
      preview.append(createThemePreview(theme));

      const title = document.createElement("span");
      title.className = "theme-card-title";
      title.textContent = theme.name;

      const titleRow = document.createElement("span");
      titleRow.className = "theme-card-title-row";
      titleRow.append(createSettingsIcon(getThemeIconName(theme)), title);

      const meta = document.createElement("span");
      meta.className = "theme-card-meta";
      meta.textContent = getThemeMetaText(theme);

      const description = document.createElement("span");
      description.className = "theme-card-description";
      description.textContent = theme.description || "";

      const tags = createThemeTags(theme);
      const body = document.createElement("span");
      body.className = "theme-card-body";
      body.append(titleRow, meta, description, tags);

      button.append(preview, body);
      container.append(button);
    });
  }

  function createSettingsIcon(name) {
    const iconName = ICON_PATHS[name] ? name : "settings";
    const icon = document.createElement("span");
    icon.className = "settings-card-icon";
    icon.setAttribute("aria-hidden", "true");

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("fill", "none");
    svg.setAttribute("stroke", "currentColor");
    svg.setAttribute("stroke-width", "2");
    svg.setAttribute("stroke-linecap", "round");
    svg.setAttribute("stroke-linejoin", "round");

    ICON_PATHS[iconName].forEach((pathData) => {
      const path = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "path",
      );
      path.setAttribute("d", pathData);
      svg.append(path);
    });

    icon.append(svg);
    return icon;
  }

  function getThemeIconName(theme) {
    const path = theme.path || "";
    const tags = [
      path,
      theme.type,
      theme.category,
      ...(Array.isArray(theme.tags) ? theme.tags : []),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();

    if (path === "light" || tags.includes("bright")) return "sun";
    if (path === "ocean" || tags.includes("ocean")) return "waves";
    if (path === "matrix" || tags.includes("code")) return "code";
    if (path === "sage" || path === "readable" || tags.includes("calm")) {
      return "leaf";
    }
    if (path === "high-contrast" || tags.includes("contrast")) return "eye";
    if (Number(theme.id) >= 100 || tags.includes("animated")) return "sparkle";
    if (theme.type === "light") return "sun";
    return "moon";
  }

  function createThemePreview(theme) {
    const colors = getThemePreviewColors(theme);
    const preview = document.createElement("span");
    preview.className = "theme-card-preview-stage";
    preview.style.background = colors.background;

    const surface = document.createElement("span");
    surface.className = "theme-card-preview-surface";
    surface.style.background = colors.surface;
    surface.style.color = colors.text;
    surface.style.borderColor = colors.border;

    const heading = document.createElement("span");
    heading.className = "theme-card-preview-heading";
    heading.style.background = colors.accent;

    const line = document.createElement("span");
    line.className = "theme-card-preview-line";
    line.style.background = colors.text;

    const shortLine = document.createElement("span");
    shortLine.className =
      "theme-card-preview-line theme-card-preview-line--short";
    shortLine.style.background = colors.text;

    const accent = document.createElement("span");
    accent.className = "theme-card-preview-accent";
    accent.style.background = colors.accent;

    surface.append(heading, line, shortLine, accent);
    preview.append(surface, createThemeSwatches(colors));

    return preview;
  }

  function createThemeSwatches(colors) {
    const swatchColors = [
      colors.background,
      colors.surface,
      colors.text,
      colors.accent,
      colors.border,
    ];
    const swatches = document.createElement("span");
    swatches.className = "theme-card-swatches";

    swatchColors.forEach((color) => {
      const swatch = document.createElement("span");
      swatch.className = "theme-card-swatch";
      swatch.style.background = color;
      swatches.append(swatch);
    });

    return swatches;
  }

  function getThemePreviewColors(theme) {
    if (theme.preview) {
      return {
        background: theme.preview.background || "#ffffff",
        surface: theme.preview.surface || theme.preview.background || "#ffffff",
        text: theme.preview.text || "#111111",
        accent: theme.preview.accent || theme.preview.text || "#333333",
        border: theme.preview.border || theme.preview.accent || "#999999",
      };
    }

    const themePath = theme.path;
    const host = document.createElement("div");
    host.setAttribute("data-theme", themePath);
    host.style.cssText =
      "position:absolute;left:-9999px;top:-9999px;width:1px;height:1px;overflow:hidden;";

    const variables = {
      background: "--piggy-main",
      surface: "--piggy-menu",
      text: "--piggy-text-main",
      accent: "--piggy-button-active",
      border: "--piggy-button-border",
    };

    const swatches = Object.entries(variables).map(([key, variable]) => {
      const swatch = document.createElement("span");
      swatch.dataset.previewKey = key;
      swatch.style.backgroundColor = `var(${variable})`;
      host.append(swatch);
      return swatch;
    });

    document.body.append(host);

    const colors = Object.fromEntries(
      swatches.map((swatch) => {
        const color = window.getComputedStyle(swatch).backgroundColor;
        return [
          swatch.dataset.previewKey,
          color && color !== "rgba(0, 0, 0, 0)" ? color : "currentColor",
        ];
      }),
    );

    host.remove();

    return colors;
  }

  function getThemeMetaText(theme) {
    const labels = [capitalize(theme.type || "theme")];

    if (theme.category && theme.category !== "standard") {
      labels.push(theme.category);
    } else if (theme.path === "high-contrast") {
      labels.push("accessible");
    } else if (Number(theme.id) >= 100) {
      labels.push("animated");
    }

    return labels.join(" / ");
  }

  function createThemeTags(theme) {
    const tags = document.createElement("span");
    tags.className = "theme-card-tags";

    const tagValues = [
      ...(Array.isArray(theme.tags) ? theme.tags : []),
      ...(Array.isArray(theme.recommended_for) ? theme.recommended_for : []),
      theme.category && theme.category !== "standard" ? theme.category : "",
      Number(theme.id) >= 100 ? "animated" : "",
    ].filter(Boolean);

    [...new Set(tagValues)].slice(0, 3).forEach((tag) => {
      const tagElement = document.createElement("span");
      tagElement.className = "theme-card-tag";
      tagElement.textContent = tag;
      tags.append(tagElement);
    });

    return tags;
  }

  function renderSelectControl(id, container) {
    if (!container) return;

    const labelText = CONTROL_LABELS[id] || id;
    const labelId = `settings-${id}-label`;
    const options = preferencesApi.getOptions(id);

    const field = document.createElement("label");
    field.className = "settings-select-field";

    const label = document.createElement("span");
    label.className = "settings-label";
    label.id = labelId;
    label.textContent = labelText;

    const select = document.createElement("select");
    select.className = "settings-select";
    select.dataset.prefSelect = id;
    select.setAttribute("aria-labelledby", labelId);

    options.forEach((option) => {
      const optionElement = document.createElement("option");
      optionElement.value = option.value;
      optionElement.textContent = option.detail
        ? `${option.label} - ${option.detail}`
        : option.label;
      optionElement.style.fontFamily = getFontSampleFamily(id, option.value);
      select.append(optionElement);
    });

    const preview = document.createElement("span");
    preview.className = "settings-select-preview";
    preview.dataset.prefPreview = id;

    field.append(label, select, preview);
    container.replaceChildren(field);
  }

  function renderSegmentedControl(id, container) {
    if (!container) return;

    const labelText = CONTROL_LABELS[id] || id;
    const group = document.createElement("div");
    group.className = "settings-control-group";

    const label = document.createElement("div");
    label.className = "settings-label";
    label.textContent = labelText;

    const current = document.createElement("span");
    current.className = "settings-current-value";
    current.dataset.prefCurrent = id;
    label.append(current);

    const segmented = document.createElement("div");
    segmented.className = "settings-segmented";
    segmented.setAttribute("role", "group");
    segmented.setAttribute("aria-label", labelText);

    preferencesApi.getOptions(id).forEach((option) => {
      const button = document.createElement("button");
      button.className = "settings-segmented-button";
      button.type = "button";
      button.dataset.prefId = id;
      button.dataset.prefValue = option.value;
      button.setAttribute("aria-pressed", "false");

      const title = document.createElement("span");
      title.className = "settings-segmented-title";
      title.textContent = option.label;

      const preview = createSettingOptionPreview(id, option.value);
      button.append(title, preview);
      segmented.append(button);
    });

    group.append(label, segmented);
    container.replaceChildren(group);
  }

  function renderToggleControl(id, container) {
    if (!container) return;

    const button = document.createElement("button");
    button.className = "settings-toggle";
    button.type = "button";
    button.dataset.prefToggle = id;
    button.setAttribute("aria-pressed", "false");

    const label = document.createElement("span");
    label.textContent = TOGGLE_LABELS[id] || CONTROL_LABELS[id] || id;

    const state = document.createElement("span");
    state.className = "settings-toggle-state";
    state.setAttribute("aria-hidden", "true");

    button.append(label, state);
    container.replaceChildren(button);
  }

  function initializeSettingsTabs() {
    if (!settingsTabs) return;

    const selectedTab =
      settingsTabs.querySelector('[data-settings-tab][aria-selected="true"]')
        ?.dataset.settingsTab ||
      settingsTabs.querySelector("[data-settings-tab]")?.dataset.settingsTab;

    activateSettingsTab(selectedTab);
    settingsTabs.addEventListener("keydown", handleSettingsTabKeydown);
  }

  function activateSettingsTab(tabId, options = {}) {
    if (!settingsTabs || !tabId) return;

    const tabs = [...settingsTabs.querySelectorAll("[data-settings-tab]")];
    const panels = [...settingsTabs.querySelectorAll("[data-settings-panel]")];
    const targetTab =
      tabs.find((tab) => tab.dataset.settingsTab === tabId) || tabs[0];

    if (!targetTab) return;

    const activeTabId = targetTab.dataset.settingsTab;

    tabs.forEach((tab) => {
      const isSelected = tab.dataset.settingsTab === activeTabId;
      tab.setAttribute("aria-selected", String(isSelected));
      tab.tabIndex = isSelected ? 0 : -1;
    });

    panels.forEach((panel) => {
      panel.hidden = panel.dataset.settingsPanel !== activeTabId;
    });

    if (options.focus) {
      targetTab.focus();
    }
  }

  function handleSettingsTabKeydown(event) {
    if (!settingsTabs) return;

    const navigationKeys = [
      "ArrowLeft",
      "ArrowRight",
      "ArrowUp",
      "ArrowDown",
      "Home",
      "End",
    ];

    if (!navigationKeys.includes(event.key)) return;

    const tabs = [...settingsTabs.querySelectorAll("[data-settings-tab]")];
    const currentTab = event.target.closest("[data-settings-tab]");
    const currentIndex = tabs.indexOf(currentTab);

    if (currentIndex === -1) return;

    event.preventDefault();

    let nextIndex = currentIndex;

    if (event.key === "Home") {
      nextIndex = 0;
    } else if (event.key === "End") {
      nextIndex = tabs.length - 1;
    } else if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      nextIndex = (currentIndex + 1) % tabs.length;
    } else {
      nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
    }

    activateSettingsTab(tabs[nextIndex].dataset.settingsTab, { focus: true });
  }

  function handleSettingsClick(event) {
    const tab = event.target.closest("[data-settings-tab]");
    if (tab && settingsTabs?.contains(tab)) {
      activateSettingsTab(tab.dataset.settingsTab);
      return;
    }

    const toggle = event.target.closest("[data-pref-toggle]");
    if (toggle) {
      const id = toggle.dataset.prefToggle;
      const currentValue = preferencesApi.getPreferences()[id];
      preferencesApi.setPreference(id, currentValue === "on" ? "off" : "on");
      return;
    }

    const button = event.target.closest("[data-pref-id][data-pref-value]");
    if (!button) return;

    const { prefId, prefValue } = button.dataset;

    if (prefId === "readerPreset" && prefValue !== "custom") {
      preferencesApi.applyPreset(prefValue);
      return;
    }

    preferencesApi.setPreference(prefId, prefValue, {
      keepPreset: prefId === "readerPreset",
    });
  }

  function handleSettingsChange(event) {
    const select = event.target.closest("[data-pref-select]");
    if (!select) return;

    preferencesApi.setPreference(select.dataset.prefSelect, select.value);
  }

  function updateSettingsControls(preferences) {
    settingsPage
      ?.querySelectorAll("[data-pref-id][data-pref-value]")
      .forEach((control) => {
        const { prefId, prefValue } = control.dataset;
        control.setAttribute(
          "aria-pressed",
          preferences[prefId] === prefValue ? "true" : "false",
        );
      });

    settingsPage?.querySelectorAll("[data-pref-select]").forEach((select) => {
      const id = select.dataset.prefSelect;
      select.value = preferences[id];
    });

    settingsPage?.querySelectorAll("[data-pref-toggle]").forEach((toggle) => {
      const id = toggle.dataset.prefToggle;
      toggle.setAttribute(
        "aria-pressed",
        preferences[id] === "on" ? "true" : "false",
      );
    });

    settingsPage?.querySelectorAll("[data-pref-current]").forEach((element) => {
      const id = element.dataset.prefCurrent;
      element.textContent = getOptionLabel(id, preferences[id]);
    });

    settingsPage?.querySelectorAll("[data-pref-preview]").forEach((element) => {
      updateSettingPreview(element, element.dataset.prefPreview, preferences);
    });
  }

  function captureSettingsSource() {
    if (settingsPage) return;

    writeSessionValue(SETTINGS_SOURCE_KEY, getCurrentPageContext());
  }

  function updateReturnLink() {
    if (!returnLink || !settingsPage) return;

    const sourceContext = settingsSourceContext || getSettingsSourceContext();
    returnLink.href = sourceContext.path || "/";

    const label = returnLink.querySelector("span");
    if (label) {
      label.textContent =
        sourceContext.pageKey === getCurrentPageKey() ? "Back" : "Back to page";
    }
  }

  function updateThemeEffects(preferences, changedKey = "") {
    const themeChanged =
      changedKey === "theme" ||
      (changedKey === "readerPreset" &&
        preferences.theme !== lastPreferences.theme);

    if (themeChanged && shouldAnimatePreferenceChange(preferences)) {
      pageTransition();
    }

    stopAllAnimations();

    if (shouldSuppressThemeEffects(preferences)) {
      return;
    }

    switch (preferences.theme) {
      case "matrix":
        callIfFunction("startMatrixAnimation");
        break;
      case "space":
        callIfFunction("startSpaceAnimation");
        break;
      case "ocean":
        callIfFunction("startOceanShaderAnimation");
        break;
      case "desert":
        callIfFunction("startDesertShaderAnimation");
        break;
      case "golden":
        callIfFunction("startGoldenShaderAnimation");
        break;
    }
  }

  function shouldSuppressThemeEffects(preferences) {
    if (preferences.hideDecorations === "on") return true;
    if (preferences.reduceMotion === "reduce") return true;

    return (
      preferences.reduceMotion === "system" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
    );
  }

  function shouldAnimatePreferenceChange(preferences) {
    return !shouldSuppressThemeEffects(preferences);
  }

  function pageTransition() {
    document.body.classList.add("transition");
    window.setTimeout(() => {
      document.body.classList.remove("transition");
    }, 400);
  }

  function callIfFunction(name) {
    if (typeof window[name] === "function") {
      window[name]();
    }
  }

  function stopAllAnimations() {
    callIfFunction("stopMatrixAnimation");
    callIfFunction("stopSpaceAnimation");
    callIfFunction("stopOceanShaderAnimation");
    callIfFunction("stopDesertShaderAnimation");
    callIfFunction("stopGoldenShaderAnimation");
  }

  function initializeReaderRuler() {
    if (!readerRuler || !markdownContent) return;

    const updateRuler = (clientY) => {
      if (preferencesApi.getPreferences().readingRuler !== "on") return;

      document.documentElement.style.setProperty(
        "--piggy-reader-ruler-top",
        `${clientY}px`,
      );
      readerRuler.classList.add("is-visible");
    };

    markdownContent.addEventListener("mousemove", (event) => {
      updateRuler(event.clientY);
    });

    markdownContent.addEventListener(
      "touchmove",
      (event) => {
        const touch = event.touches[0];
        if (touch) updateRuler(touch.clientY);
      },
      { passive: true },
    );

    markdownContent.addEventListener("mouseleave", () => {
      readerRuler.classList.remove("is-visible");
    });

    document.addEventListener("piggy:preferenceschange", (event) => {
      if (event.detail.preferences.readingRuler !== "on") {
        readerRuler.classList.remove("is-visible");
      }
    });
  }

  function initializeRememberedPosition() {
    if (settingsPage) return;

    if (preferencesApi.getPreferences().rememberPosition === "on") {
      restoreScrollPosition();
    }
  }

  function restoreScrollPosition() {
    if (window.location.hash) return;

    const positions = readStorageMap(SCROLL_KEY);
    const savedPosition = positions[getCurrentPageKey()];

    if (!Number.isFinite(savedPosition) || savedPosition <= 0) return;

    window.setTimeout(() => {
      window.scrollTo({
        top: savedPosition,
        behavior: shouldSuppressThemeEffects(preferencesApi.getPreferences())
          ? "auto"
          : "smooth",
      });
    }, 120);
  }

  function saveScrollPosition() {
    if (preferencesApi.getPreferences().rememberPosition !== "on") return;

    const positions = readStorageMap(SCROLL_KEY);
    positions[getCurrentPageKey()] = Math.max(0, Math.round(window.scrollY));
    writeStorageMap(SCROLL_KEY, positions);
  }

  function saveSourceScrollPosition() {
    if (preferencesApi.getPreferences().rememberPosition !== "on") return;
    if (!settingsSourceContext?.pageKey) return;
    if (!settingsSourceContext.capturedAt) return;
    if (!Number.isFinite(settingsSourceContext.scrollY)) return;

    const positions = readStorageMap(SCROLL_KEY);
    positions[settingsSourceContext.pageKey] = Math.max(
      0,
      Math.round(settingsSourceContext.scrollY),
    );
    writeStorageMap(SCROLL_KEY, positions);
  }

  function readStorageMap(key) {
    try {
      const rawValue = window.localStorage?.getItem(key);
      const parsed = rawValue ? JSON.parse(rawValue) : {};
      return parsed && typeof parsed === "object" ? parsed : {};
    } catch {
      return {};
    }
  }

  function writeStorageMap(key, value) {
    try {
      window.localStorage?.setItem(key, JSON.stringify(value));
    } catch {
      return false;
    }

    return true;
  }

  function readSessionValue(key) {
    try {
      const rawValue = window.sessionStorage?.getItem(key);
      return rawValue ? JSON.parse(rawValue) : null;
    } catch {
      return null;
    }
  }

  function writeSessionValue(key, value) {
    try {
      window.sessionStorage?.setItem(key, JSON.stringify(value));
    } catch {
      return false;
    }

    return true;
  }

  function getThemes() {
    return Array.isArray(window.PIGGY_THEMES) ? window.PIGGY_THEMES : [];
  }

  function getOptionLabel(id, value) {
    const option = preferencesApi
      .getOptions(id)
      .find((candidate) => candidate.value === value);

    return option?.label || value;
  }

  function createSettingOptionPreview(id, value) {
    const preview = document.createElement("span");
    preview.className = "settings-option-preview";
    preview.dataset.previewType = id;
    preview.setAttribute("aria-hidden", "true");

    switch (id) {
      case "readerFontSize":
        preview.textContent = "Aa";
        preview.style.fontSize = getFontSizePreview(value);
        break;
      case "readerLineHeight":
        preview.classList.add("settings-option-preview--lines");
        preview.style.lineHeight = getLineHeightPreview(value);
        preview.append(
          createPreviewLine("Line one"),
          createPreviewLine("Line two"),
        );
        break;
      case "readerLetterSpacing":
        preview.textContent = "Spacing";
        preview.style.letterSpacing = getLetterSpacingPreview(value);
        break;
      case "readerWordSpacing":
        preview.textContent = "Word spacing";
        preview.style.wordSpacing = getWordSpacingPreview(value);
        break;
      case "readerParagraphSpacing":
        preview.classList.add("settings-option-preview--paragraphs");
        preview.style.gap = getParagraphSpacingPreview(value);
        preview.append(
          createPreviewLine("First paragraph"),
          createPreviewLine("Second paragraph"),
        );
        break;
      case "readerWidth":
        preview.classList.add("settings-option-preview--measure");
        preview.append(createMeasurePreview(value));
        break;
      case "contrast":
        preview.classList.add("settings-option-preview--contrast");
        preview.append(createContrastPreview(value));
        break;
      case "reduceMotion":
        preview.textContent =
          value === "reduce" ? "Still" : value === "allow" ? "Moves" : "System";
        break;
      default:
        preview.textContent = getOptionLabel(id, value);
        break;
    }

    return preview;
  }

  function updateSettingPreview(element, id, preferences) {
    const value = preferences[id];
    element.textContent = "";
    element.style.fontFamily = "";
    element.style.fontSize = "";

    if (id === "readerFont" || id === "codeFont") {
      element.textContent =
        id === "codeFont" ? "const answer = 42;" : "A clearer reading sample";
      element.style.fontFamily = getFontSampleFamily(id, value);
      return;
    }

    element.textContent = getOptionLabel(id, value);
  }

  function createPreviewLine(text) {
    const line = document.createElement("span");
    line.textContent = text;
    return line;
  }

  function createMeasurePreview(value) {
    const measure = document.createElement("span");
    measure.className = "settings-measure-preview";
    measure.style.width = getWidthPreview(value);
    return measure;
  }

  function createContrastPreview(value) {
    const contrast = document.createElement("span");
    contrast.className = `settings-contrast-preview settings-contrast-preview--${value}`;
    return contrast;
  }

  function getFontSizePreview(value) {
    const sizes = {
      "xx-small": "0.72rem",
      "x-small": "0.82rem",
      small: "0.92rem",
      default: "1rem",
      large: "1.12rem",
      "x-large": "1.25rem",
      "xx-large": "1.38rem",
      "xxx-large": "1.55rem",
    };

    return sizes[value] || sizes.default;
  }

  function getLineHeightPreview(value) {
    const lineHeights = {
      original: "1.75",
      compact: "1.25",
      comfortable: "1.45",
      spacious: "1.7",
      extra: "1.95",
    };

    return lineHeights[value] || lineHeights.comfortable;
  }

  function getLetterSpacingPreview(value) {
    const spacings = {
      default: "0",
      wide: "0.12em",
      extra: "0.2em",
    };

    return spacings[value] || spacings.default;
  }

  function getWordSpacingPreview(value) {
    const spacings = {
      default: "0",
      wide: "0.28em",
      extra: "0.48em",
    };

    return spacings[value] || spacings.default;
  }

  function getParagraphSpacingPreview(value) {
    const spacings = {
      original: "0.18rem",
      compact: "0.1rem",
      comfortable: "0.22rem",
      spacious: "0.38rem",
      extra: "0.58rem",
    };

    return spacings[value] || spacings.comfortable;
  }

  function getWidthPreview(value) {
    const widths = {
      narrow: "42%",
      medium: "58%",
      wide: "78%",
      full: "100%",
    };

    return widths[value] || widths.medium;
  }

  function getFontSampleFamily(id, value) {
    const families = {
      default: '"Noto Sans", sans-serif',
      atkinson: '"Atkinson Hyperlegible", Arial, sans-serif',
      lexend: '"Lexend", "Noto Sans", sans-serif',
      lexia: '"Lexia", "Comic Sans MS", sans-serif',
      "open-dyslexic": '"OpenDyslexic", "Comic Sans MS", sans-serif',
      nunito: '"Nunito", "Noto Sans", sans-serif',
      lato: '"Lato", "Noto Sans", sans-serif',
      bitter: '"Bitter", serif',
      quicksand: '"Quicksand", sans-serif',
      arial: "Arial, Helvetica, sans-serif",
      verdana: "Verdana, Geneva, sans-serif",
      georgia: "Georgia, serif",
      times: '"Times New Roman", Times, serif',
      courier: '"Courier New", Courier, monospace',
      "fira-code": '"Fira Code", monospace',
      "roboto-mono": '"Roboto Mono", monospace',
      "jetbrains-mono": '"JetBrains Mono", monospace',
      "dm-mono": '"DM Mono", monospace',
      "atkinson-mono":
        '"Atkinson Hyperlegible Mono", "Cascadia Code PL", monospace',
      "ubuntu-mono": '"Ubuntu Mono", monospace',
      "kode-mono": '"Kode Mono", monospace',
    };

    if (id === "codeFont" && value === "default") {
      return '"Cascadia Code PL", monospace';
    }

    return families[value] || "inherit";
  }

  function getCurrentPageContext() {
    return {
      pageKey: getCurrentPageKey(),
      path: getCurrentPagePath(),
      title: getPageTitle(),
      scrollY: Math.max(0, Math.round(window.scrollY)),
      capturedAt: new Date().toISOString(),
    };
  }

  function getSettingsSourceContext() {
    if (!settingsPage) {
      return getCurrentPageContext();
    }

    const returnPath = getSettingsReturnPath();
    const storedContext = readSessionValue(SETTINGS_SOURCE_KEY);
    if (
      storedContext?.pageKey &&
      storedContext.pageKey === getPageKeyFromPath(returnPath)
    ) {
      return storedContext;
    }

    if (
      storedContext?.pageKey &&
      settingsPage.dataset.settingsHasReturnTo !== "true"
    ) {
      return storedContext;
    }

    return {
      pageKey: getPageKeyFromPath(returnPath),
      path: returnPath,
      title: "the previous page",
      scrollY: 0,
    };
  }

  function getSettingsReturnPath() {
    return normalizeInternalPath(settingsPage?.dataset.settingsReturnTo) || "/";
  }

  function normalizeInternalPath(value) {
    if (!value || typeof value !== "string") return "";

    try {
      const url = new URL(value, window.location.origin);
      if (url.origin !== window.location.origin) return "";
      return `${url.pathname}${url.search}`;
    } catch {
      return "";
    }
  }

  function getPageKeyFromPath(path) {
    const normalizedPath = normalizeInternalPath(path) || "/";
    return normalizedPath.split("#")[0];
  }

  function getCurrentPagePath() {
    return `${window.location.pathname}${window.location.search}`;
  }

  function getCurrentPageKey() {
    return getCurrentPagePath();
  }

  function getPageTitle() {
    return (
      document.querySelector("main .assignment-heading")?.textContent.trim() ||
      document.title ||
      window.location.pathname
    );
  }

  function capitalize(value) {
    if (!value) return "";
    return value.charAt(0).toUpperCase() + value.slice(1);
  }
});
