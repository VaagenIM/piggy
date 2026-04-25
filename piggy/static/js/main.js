document.addEventListener("DOMContentLoaded", () => {
  const settingsMenu = document.getElementById("settings-menu");
  const settingsButton = document.getElementById("settings-button");
  const closeButton = document.querySelector("#settings-menu .close-button");

  const themeSelect = document.getElementById("theme-select");
  const fontSelect = document.getElementById("font-select");
  const monoSelect = document.getElementById("mono-select");
  const fontSizeSelect = document.getElementById("font-size-select");

  const THEME_STORAGE_KEY = "theme";
  const FONT_STORAGE_KEY = "fontTheme";
  const MONO_STORAGE_KEY = "monoTheme";
  const FONT_SIZE_STORAGE_KEY = "fontSize";
  const DEFAULT_FONT_THEME = "default";
  const DEFAULT_MONO_THEME = "default";
  const DEFAULT_FONT_SIZE = "default";

  function getThemeType(themePath) {
    const themes = Array.isArray(window.PIGGY_THEMES)
      ? window.PIGGY_THEMES
      : [];
    const themeData = themes.find((theme) => theme.path === themePath);

    return themeData?.type || "dark";
  }

  function closeAllCustomSelects(except = null) {
    document.querySelectorAll(".custom-select").forEach((select) => {
      if (select !== except) {
        closeCustomSelect(select);
      }
    });
  }

  function openCustomSelect(select) {
    if (!select) return;
    select.classList.add("open");
    updateOptionsMaxHeight(select);
  }

  function closeCustomSelect(select) {
    if (!select) return;
    select.classList.remove("open");

    const optionsContainer = select.querySelector(".options-container");
    if (optionsContainer) {
      optionsContainer.style.maxHeight = "";
    }
  }

  function toggleCustomSelect(select) {
    if (!select) return;

    const isOpen = select.classList.contains("open");
    closeAllCustomSelects(select);

    if (isOpen) {
      closeCustomSelect(select);
    } else {
      openCustomSelect(select);
    }
  }

  function updateOptionsMaxHeight(select) {
    const optionsContainer = select.querySelector(".options-container");
    if (!optionsContainer) return;

    const rect = optionsContainer.getBoundingClientRect();
    const availableHeight = window.innerHeight - rect.top - 10;
    optionsContainer.style.maxHeight = `${availableHeight}px`;
  }

  function pageTransition() {
    document.body.classList.add("transition");
    setTimeout(() => {
      document.body.classList.remove("transition");
    }, 1000);
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
    callIfFunction("stopFrostyShaderAnimation");
  }

  function applyTheme(theme) {
    const themeType = getThemeType(theme);

    localStorage.setItem(THEME_STORAGE_KEY, theme);
    document.documentElement.setAttribute("data-theme", theme);
    document.documentElement.setAttribute("data-theme-type", themeType);

    pageTransition();
    stopAllAnimations();

    switch (theme) {
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
      case "frosty":
        callIfFunction("startFrostyShaderAnimation");
        break;
    }
  }

  function applyFontTheme(fontTheme) {
    localStorage.setItem(FONT_STORAGE_KEY, fontTheme);
    document.documentElement.setAttribute("data-font-theme", fontTheme);
  }

  function applyMonoTheme(monoTheme) {
    localStorage.setItem(MONO_STORAGE_KEY, monoTheme);
    document.documentElement.setAttribute("data-mono-theme", monoTheme);
  }

  function applyFontSize(fontSize) {
    localStorage.setItem(FONT_SIZE_STORAGE_KEY, fontSize);
    document.documentElement.setAttribute("data-font-size", fontSize);
  }

  function initializeCustomSelect({
    select,
    storageKey,
    defaultValue,
    onChange,
  }) {
    if (!select) return;

    const selected = select.querySelector(".selected");
    const options = select.querySelectorAll(".option");

    if (!selected || options.length === 0) return;

    const savedValue = localStorage.getItem(storageKey) || defaultValue;
    const matchingOption = select.querySelector(
      `.option[data-value="${savedValue}"]`,
    );

    if (matchingOption) {
      selected.textContent = matchingOption.textContent;
      selected.setAttribute("data-value", savedValue);
    }

    selected.addEventListener("click", (event) => {
      toggleCustomSelect(select);
      event.stopPropagation();
    });

    options.forEach((option) => {
      option.addEventListener("click", (event) => {
        const value = option.getAttribute("data-value");

        selected.textContent = option.textContent;
        selected.setAttribute("data-value", value);

        onChange(value);
        closeCustomSelect(select);

        event.stopPropagation();
      });
    });
  }

  function openSettingsMenu() {
    settingsMenu.classList.add("open");
  }

  function closeSettingsMenu() {
    settingsMenu.classList.remove("open");
  }

  const currentTheme =
    localStorage.getItem(THEME_STORAGE_KEY) || systemPreferredTheme;
  applyTheme(currentTheme);

  initializeCustomSelect({
    select: themeSelect,
    storageKey: THEME_STORAGE_KEY,
    defaultValue: currentTheme,
    onChange: applyTheme,
  });

  initializeCustomSelect({
    select: fontSelect,
    storageKey: FONT_STORAGE_KEY,
    defaultValue: DEFAULT_FONT_THEME,
    onChange: applyFontTheme,
  });

  initializeCustomSelect({
    select: monoSelect,
    storageKey: MONO_STORAGE_KEY,
    defaultValue: DEFAULT_MONO_THEME,
    onChange: applyMonoTheme,
  });

  initializeCustomSelect({
    select: fontSizeSelect,
    storageKey: FONT_SIZE_STORAGE_KEY,
    defaultValue: DEFAULT_FONT_SIZE,
    onChange: applyFontSize,
  });

  document.addEventListener("click", () => {
    closeAllCustomSelects();
  });

  settingsButton?.addEventListener("click", openSettingsMenu);
  closeButton?.addEventListener("click", closeSettingsMenu);

  window.addEventListener("click", (event) => {
    if (
      settingsMenu?.classList.contains("open") &&
      !settingsMenu.contains(event.target) &&
      !settingsButton?.contains(event.target)
    ) {
      closeSettingsMenu();
    }
  });

  window.addEventListener("resize", () => {
    document.querySelectorAll(".custom-select.open").forEach((select) => {
      updateOptionsMaxHeight(select);
    });
  });
});
