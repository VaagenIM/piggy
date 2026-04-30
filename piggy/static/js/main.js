document.addEventListener("DOMContentLoaded", () => {
  const preferencesApi = window.PiggyPreferences;
  if (!preferencesApi) return;

  const settingsMenu = document.getElementById("settings-menu");
  const settingsButton = document.getElementById("settings-button");
  const settingsBackdrop = document.getElementById("settings-backdrop");
  const closeButton = settingsMenu?.querySelector(".settings-close-button");
  const resetButton = document.getElementById("settings-reset-button");
  const bookmarkButton = document.getElementById("settings-bookmark-button");
  const completeButton = document.getElementById("settings-complete-button");
  const readerRuler = document.getElementById("reader-ruler");
  const markdownContent = document.querySelector("main .md-content");

  const BOOKMARKS_KEY = "piggy.readerBookmarks.v1";
  const PROGRESS_KEY = "piggy.readerProgress.v1";
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
    rememberPosition: "Resume this page",
  };

  let lastPreferences = preferencesApi.getPreferences();
  let lastFocusedElement = null;
  let previousBodyOverflow = "";
  let scrollSaveTimeout = null;

  renderSettingsControls();
  updateSettingsControls(lastPreferences);
  updateThemeEffects(lastPreferences);
  updateSupportButtons();
  initializeReaderRuler();
  initializeRememberedPosition();

  settingsButton?.addEventListener("click", openSettingsMenu);
  closeButton?.addEventListener("click", closeSettingsMenu);
  settingsBackdrop?.addEventListener("click", closeSettingsMenu);
  resetButton?.addEventListener("click", () =>
    preferencesApi.applyPreset("default"),
  );
  bookmarkButton?.addEventListener("click", toggleBookmark);
  completeButton?.addEventListener("click", toggleComplete);

  settingsMenu?.addEventListener("click", handleSettingsClick);
  settingsMenu?.addEventListener("change", handleSettingsChange);
  settingsMenu?.addEventListener("keydown", handleSettingsKeydown);

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && settingsMenu?.classList.contains("open")) {
      closeSettingsMenu();
    }
  });

  document.addEventListener("piggy:preferenceschange", (event) => {
    const nextPreferences = event.detail.preferences;
    const changedKey = event.detail.changedKey;

    updateSettingsControls(nextPreferences);
    updateThemeEffects(nextPreferences, changedKey);

    if (changedKey === "rememberPosition") {
      saveScrollPosition();
    }

    lastPreferences = nextPreferences;
  });

  window.addEventListener(
    "scroll",
    () => {
      if (preferencesApi.getPreferences().rememberPosition !== "on") return;

      window.clearTimeout(scrollSaveTimeout);
      scrollSaveTimeout = window.setTimeout(saveScrollPosition, 160);
    },
    { passive: true },
  );
  window.addEventListener("pagehide", saveScrollPosition);

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

    renderPageOutline(getRenderTarget("outline"));
  }

  function getRenderTarget(name) {
    return settingsMenu?.querySelector(`[data-settings-render="${name}"]`);
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

      const title = document.createElement("span");
      title.className = "settings-option-title";
      title.textContent = preset.label;

      const detail = document.createElement("span");
      detail.className = "settings-option-detail";
      detail.textContent = preset.detail;

      button.append(title, detail);
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

      const meta = document.createElement("span");
      meta.className = "theme-card-meta";
      meta.textContent = getThemeMetaText(theme);

      const description = document.createElement("span");
      description.className = "theme-card-description";
      description.textContent = theme.description || "";

      const tags = createThemeTags(theme);
      const body = document.createElement("span");
      body.className = "theme-card-body";
      body.append(title, meta, description, tags);

      button.append(preview, body);
      container.append(button);
    });
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

  function renderPageOutline(container) {
    if (!container) return;

    container.replaceChildren();

    const pageRoot = document.querySelector("main") || document;
    const headings = [
      ...pageRoot.querySelectorAll(".md-content h2, .md-content h3"),
    ].filter((heading) => heading.textContent.trim());

    if (headings.length === 0) {
      const empty = document.createElement("p");
      empty.className = "settings-outline-empty";
      empty.textContent = "No sections on this page";
      container.append(empty);
      return;
    }

    const list = document.createElement("div");
    list.className = "settings-outline-list";
    const usedIds = new Set(
      [...document.querySelectorAll("[id]")].map((element) => element.id),
    );

    headings.forEach((heading) => {
      if (!heading.id) {
        heading.id = createUniqueSlug(heading.textContent, usedIds);
      } else {
        usedIds.add(heading.id);
      }

      const link = document.createElement("a");
      link.className = "settings-outline-link";
      if (heading.tagName.toLowerCase() === "h3") {
        link.classList.add("settings-outline-link--child");
      }
      link.href = `#${heading.id}`;
      link.textContent = heading.textContent.trim();
      link.addEventListener("click", () => {
        window.setTimeout(closeSettingsMenu, 80);
      });
      list.append(link);
    });

    container.append(list);
  }

  function handleSettingsClick(event) {
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
    settingsMenu
      ?.querySelectorAll("[data-pref-id][data-pref-value]")
      .forEach((control) => {
        const { prefId, prefValue } = control.dataset;
        control.setAttribute(
          "aria-pressed",
          preferences[prefId] === prefValue ? "true" : "false",
        );
      });

    settingsMenu?.querySelectorAll("[data-pref-select]").forEach((select) => {
      const id = select.dataset.prefSelect;
      select.value = preferences[id];
    });

    settingsMenu?.querySelectorAll("[data-pref-toggle]").forEach((toggle) => {
      const id = toggle.dataset.prefToggle;
      toggle.setAttribute(
        "aria-pressed",
        preferences[id] === "on" ? "true" : "false",
      );
    });

    settingsMenu?.querySelectorAll("[data-pref-current]").forEach((element) => {
      const id = element.dataset.prefCurrent;
      element.textContent = getOptionLabel(id, preferences[id]);
    });

    settingsMenu?.querySelectorAll("[data-pref-preview]").forEach((element) => {
      updateSettingPreview(element, element.dataset.prefPreview, preferences);
    });
  }

  function openSettingsMenu() {
    if (!settingsMenu || !settingsButton) return;

    lastFocusedElement = document.activeElement;
    if (settingsBackdrop) {
      settingsBackdrop.hidden = false;
    }
    previousBodyOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    settingsMenu.removeAttribute("inert");
    settingsMenu.setAttribute("aria-hidden", "false");
    settingsButton.setAttribute("aria-expanded", "true");

    window.requestAnimationFrame(() => {
      settingsBackdrop?.classList.add("open");
      settingsMenu.classList.add("open");
      closeButton?.focus();
    });
  }

  function closeSettingsMenu() {
    if (!settingsMenu || !settingsButton) return;

    settingsBackdrop?.classList.remove("open");
    settingsMenu.classList.remove("open");
    settingsMenu.setAttribute("aria-hidden", "true");
    settingsMenu.setAttribute("inert", "");
    settingsButton.setAttribute("aria-expanded", "false");
    document.body.style.overflow = previousBodyOverflow;

    window.setTimeout(() => {
      if (!settingsMenu.classList.contains("open") && settingsBackdrop) {
        settingsBackdrop.hidden = true;
      }
    }, 220);

    if (lastFocusedElement instanceof HTMLElement) {
      lastFocusedElement.focus();
    }
  }

  function handleSettingsKeydown(event) {
    if (event.key !== "Tab") return;

    const focusableElements = getFocusableElements(settingsMenu);
    if (focusableElements.length === 0) return;

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    if (event.shiftKey && document.activeElement === firstElement) {
      event.preventDefault();
      lastElement.focus();
    } else if (!event.shiftKey && document.activeElement === lastElement) {
      event.preventDefault();
      firstElement.focus();
    }
  }

  function getFocusableElements(root) {
    if (!root) return [];

    return [
      ...root.querySelectorAll(
        'a[href], button:not([disabled]), select:not([disabled]), textarea:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])',
      ),
    ].filter((element) => {
      const closedDetails = element.closest("details:not([open])");
      if (closedDetails && element.tagName.toLowerCase() !== "summary") {
        return false;
      }

      const style = window.getComputedStyle(element);
      return style.display !== "none" && style.visibility !== "hidden";
    });
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
    if (preferencesApi.getPreferences().rememberPosition === "on") {
      restoreScrollPosition();
    }
  }

  function restoreScrollPosition() {
    if (window.location.hash) return;

    const positions = readStorageMap(SCROLL_KEY);
    const savedPosition = positions[getPageKey()];

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
    positions[getPageKey()] = Math.max(0, Math.round(window.scrollY));
    writeStorageMap(SCROLL_KEY, positions);
  }

  function toggleBookmark() {
    const bookmarks = readStorageMap(BOOKMARKS_KEY);
    const pageKey = getPageKey();

    if (bookmarks[pageKey]) {
      delete bookmarks[pageKey];
    } else {
      bookmarks[pageKey] = {
        title: getPageTitle(),
        path: window.location.pathname,
        updatedAt: new Date().toISOString(),
      };
    }

    writeStorageMap(BOOKMARKS_KEY, bookmarks);
    updateSupportButtons();
  }

  function toggleComplete() {
    const progress = readStorageMap(PROGRESS_KEY);
    const pageKey = getPageKey();

    if (progress[pageKey]) {
      delete progress[pageKey];
    } else {
      progress[pageKey] = {
        title: getPageTitle(),
        path: window.location.pathname,
        completedAt: new Date().toISOString(),
      };
    }

    writeStorageMap(PROGRESS_KEY, progress);
    updateSupportButtons();
  }

  function updateSupportButtons() {
    const pageKey = getPageKey();
    const bookmarks = readStorageMap(BOOKMARKS_KEY);
    const progress = readStorageMap(PROGRESS_KEY);

    if (bookmarkButton) {
      const isBookmarked = Boolean(bookmarks[pageKey]);
      bookmarkButton.setAttribute("aria-pressed", String(isBookmarked));
      bookmarkButton.textContent = isBookmarked
        ? "Bookmarked"
        : "Bookmark page";
    }

    if (completeButton) {
      const isComplete = Boolean(progress[pageKey]);
      completeButton.setAttribute("aria-pressed", String(isComplete));
      completeButton.textContent = isComplete ? "Completed" : "Mark complete";
    }
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

  function createUniqueSlug(value, usedIds) {
    const baseSlug = value
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");

    const fallback = Math.random().toString(36).slice(2);
    const stem = `section-${baseSlug || fallback}`;
    let candidate = stem;
    let count = 2;

    while (usedIds.has(candidate)) {
      candidate = `${stem}-${count}`;
      count += 1;
    }

    usedIds.add(candidate);
    return candidate;
  }

  function getPageKey() {
    return `${window.location.pathname}${window.location.search}`;
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
