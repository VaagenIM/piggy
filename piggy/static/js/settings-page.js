(function () {
  const SETTINGS_SOURCE_KEY = "piggy.settingsSource.v1";

  let preferencesApi = null;
  let settingsPage = null;
  let settingsTabs = null;
  let settingsContent = null;
  let settingsPreviewColumn = null;
  let settingsControlsColumn = null;
  let settingsTabPanels = null;
  let settingsHost = null;
  let pageContent = null;
  let settingsButton = null;
  let settingsSourceContext = null;
  let inlineSettingsActive = false;
  let storedPageScrollY = 0;
  let preferenceAnimationTimeout = null;
  let initializedApi = null;

  function initialize(nextPreferencesApi) {
    if (initializedApi) return initializedApi;

    preferencesApi = nextPreferencesApi;
    settingsPage = document.getElementById("settings-page");
    settingsTabs = settingsPage?.querySelector("[data-settings-tabs]") || null;
    settingsContent = settingsPage?.querySelector(".settings-content") || null;
    settingsPreviewColumn =
      settingsPage?.querySelector(".settings-preview-column") || null;
    settingsControlsColumn =
      settingsPage?.querySelector(".settings-controls-column") || null;
    settingsTabPanels =
      settingsPage?.querySelector(".settings-tab-panels") || null;
    settingsHost = settingsPage?.closest("[data-settings-host]") || null;
    pageContent = document.querySelector("[data-reader-page-content]");
    settingsButton = document.getElementById("settings-button");
    settingsSourceContext = getSettingsSourceContext();

    const resetButton = document.getElementById("settings-reset-button");
    const returnLink = document.getElementById("settings-return-link");

    if (settingsButton && !settingsButton.dataset.settingsOpenHref) {
      settingsButton.dataset.settingsOpenHref =
        settingsButton.getAttribute("href") || "";
    }

    initializeSettingsTabs();
    window.PiggySettingsControls?.render(settingsPage, preferencesApi);
    updateSettingsControls(preferencesApi.getPreferences());
    updateReturnLink();
    updateSettingsButtonState(isSettingsActive());

    settingsButton?.addEventListener("click", handleSettingsButtonClick);
    returnLink?.addEventListener("click", handleReturnLinkClick);
    resetButton?.addEventListener("click", () =>
      preferencesApi.applyPreset("default"),
    );

    settingsPage?.addEventListener("click", handleSettingsClick);
    settingsPage?.addEventListener("change", handleSettingsChange);
    document.addEventListener("keydown", handleDocumentKeydown);
    window.addEventListener("resize", updateInlineSettingsOffset);
    window.visualViewport?.addEventListener(
      "resize",
      updateInlineSettingsOffset,
    );

    document.addEventListener("piggy:preferenceschange", (event) => {
      updateSettingsControls(event.detail.preferences);
      window.requestAnimationFrame(updateInlineSettingsOffset);
      animateSettingsPreferenceChange();
    });

    initializedApi = {
      isSettingsPage: isDirectSettingsPage(),
      isSettingsActive,
      getSourceContext() {
        return settingsSourceContext;
      },
    };

    return initializedApi;
  }

  function isInlineSettingsPage() {
    return settingsPage?.dataset.settingsInline === "true";
  }

  function isDirectSettingsPage() {
    return Boolean(settingsPage) && !isInlineSettingsPage();
  }

  function isSettingsActive() {
    return isDirectSettingsPage() || inlineSettingsActive;
  }

  function updateInlineSettingsOffset() {
    if (!settingsHost) return;

    const shouldSitBelowHeader = window.matchMedia(
      "(min-width: 800px) and (min-height: 431px)",
    ).matches;

    if (!shouldSitBelowHeader) {
      settingsHost.style.setProperty("--piggy-settings-inline-top", "0px");
      return;
    }

    const header = document.querySelector(".site-header");
    const headerBottom = header?.getBoundingClientRect().bottom || 0;
    settingsHost.style.setProperty(
      "--piggy-settings-inline-top",
      `${Math.max(0, Math.round(headerBottom))}px`,
    );
  }

  function resetSettingsScroll() {
    [
      settingsContent,
      settingsPreviewColumn,
      settingsControlsColumn,
      settingsTabPanels,
      settingsPage,
    ].forEach((element) => {
      element?.scrollTo?.({ top: 0, left: 0, behavior: "auto" });
    });
  }

  function initializeSettingsTabs() {
    if (!settingsTabs) return;

    const selectedTab =
      settingsTabs.querySelector('[data-settings-tab][aria-selected="true"]')
        ?.dataset.settingsTab ||
      settingsTabs.querySelector("[data-settings-tab]")?.dataset.settingsTab;

    activateSettingsTab(selectedTab, { animate: false });
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
      const isActive = panel.dataset.settingsPanel === activeTabId;
      panel.hidden = !isActive;
      panel.classList.toggle("settings-tab-panel--active", isActive);

      if (isActive && options.animate !== false) {
        restartPanelAnimation(panel);
      }
    });

    if (options.focus) {
      targetTab.focus();
    }

    if (options.resetScroll) {
      resetSettingsScroll();
    }
  }

  function restartPanelAnimation(panel) {
    panel.classList.remove("settings-tab-panel--entering");
    void panel.offsetWidth;
    panel.classList.add("settings-tab-panel--entering");
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

    activateSettingsTab(tabs[nextIndex].dataset.settingsTab, {
      focus: true,
      resetScroll: true,
    });
  }

  function handleSettingsButtonClick(event) {
    if (!isInlineSettingsPage()) {
      if (!isDirectSettingsPage()) {
        captureSettingsSource();
      }
      return;
    }

    event.preventDefault();

    if (inlineSettingsActive) {
      closeInlineSettings({ focusButton: true });
    } else {
      openInlineSettings();
    }
  }

  function handleReturnLinkClick(event) {
    if (!isInlineSettingsPage()) return;

    event.preventDefault();
    closeInlineSettings({ focusButton: true });
  }

  function handleDocumentKeydown(event) {
    if (event.key !== "Escape" || !inlineSettingsActive) return;

    event.preventDefault();
    closeInlineSettings({ focusButton: true });
  }

  function handleSettingsClick(event) {
    const tab = event.target.closest("[data-settings-tab]");
    if (tab && settingsTabs?.contains(tab)) {
      activateSettingsTab(tab.dataset.settingsTab, { resetScroll: true });
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

    if (prefId === "readerPreset") {
      preferencesApi.applyPreset(prefValue);
      return;
    }

    if (prefId === "reduceMotion") {
      preferencesApi.setPreferences(
        {
          reduceMotion: prefValue,
          hideDecorations: prefValue === "reduce" ? "on" : "off",
        },
        { changedKey: "reduceMotion" },
      );
      return;
    }

    preferencesApi.setPreference(prefId, prefValue);
  }

  function handleSettingsChange(event) {
    const select = event.target.closest("[data-pref-select]");
    if (!select) return;

    preferencesApi.setPreference(select.dataset.prefSelect, select.value);
  }

  function openInlineSettings() {
    if (!settingsPage || !settingsHost || !pageContent) {
      captureSettingsSource();
      const fallbackHref =
        settingsButton?.dataset.settingsOpenHref || settingsButton?.href;
      if (fallbackHref) {
        window.location.assign(fallbackHref);
      }
      return;
    }

    settingsSourceContext = getCurrentPageContext();
    storedPageScrollY = settingsSourceContext.scrollY;
    window.PiggyStorage?.writeSessionValue(
      SETTINGS_SOURCE_KEY,
      settingsSourceContext,
    );

    pageContent.hidden = true;
    settingsHost.hidden = false;
    inlineSettingsActive = true;

    updateInlineSettingsOffset();
    resetSettingsScroll();
    document.body.classList.add("settings-inline-active");
    settingsPage.classList.remove("settings-page--leaving");
    settingsPage.classList.add("settings-page--entering");

    window.requestAnimationFrame(() => {
      settingsPage.classList.add("settings-page--active");
    });

    window.setTimeout(() => {
      settingsPage.classList.remove("settings-page--entering");
    }, 260);

    updateReturnLink();
    updateSettingsButtonState(true);
  }

  function closeInlineSettings(options = {}) {
    if (!inlineSettingsActive) return;

    settingsPage?.classList.add("settings-page--leaving");
    settingsPage?.classList.remove("settings-page--active");
    updateSettingsButtonState(false);

    const finishClose = () => {
      inlineSettingsActive = false;
      if (settingsHost) settingsHost.hidden = true;
      if (pageContent) pageContent.hidden = false;
      document.body.classList.remove("settings-inline-active");
      settingsPage?.classList.remove(
        "settings-page--entering",
        "settings-page--leaving",
      );

      window.requestAnimationFrame(() => {
        window.scrollTo({ top: storedPageScrollY, behavior: "auto" });
        if (options.focusButton) {
          settingsButton?.focus();
        }
      });
    };

    if (shouldReduceMotion()) {
      finishClose();
    } else {
      window.setTimeout(finishClose, 150);
    }
  }

  function updateSettingsControls(preferences) {
    window.PiggySettingsControls?.update(
      settingsPage,
      preferencesApi,
      preferences,
    );
  }

  function animateSettingsPreferenceChange() {
    if (!settingsPage || shouldReduceMotion()) return;

    window.clearTimeout(preferenceAnimationTimeout);
    settingsPage.classList.remove("settings-page--preference-changing");
    void settingsPage.offsetWidth;
    settingsPage.classList.add("settings-page--preference-changing");

    preferenceAnimationTimeout = window.setTimeout(() => {
      settingsPage?.classList.remove("settings-page--preference-changing");
    }, 260);
  }

  function captureSettingsSource() {
    window.PiggyStorage?.writeSessionValue(
      SETTINGS_SOURCE_KEY,
      getCurrentPageContext(),
    );
  }

  function updateReturnLink() {
    const returnLink = document.getElementById("settings-return-link");
    if (!returnLink || !settingsPage) return;

    const sourceContext = settingsSourceContext || getSettingsSourceContext();
    returnLink.href = sourceContext.path || "/";

    const label = returnLink.querySelector("span");
    if (label) {
      label.textContent =
        isInlineSettingsPage() || sourceContext.pageKey === getCurrentPageKey()
          ? "Back"
          : "Back to page";
    }
  }

  function updateSettingsButtonState(active) {
    if (!settingsButton) return;

    const showBack = isDirectSettingsPage() || active;
    const label = settingsButton.querySelector(".site-settings-button-label");
    const backIcon = settingsButton.querySelector(
      '[data-settings-icon="back"]',
    );
    const settingsIcon = settingsButton.querySelector(
      '[data-settings-icon="settings"]',
    );
    const text = showBack
      ? settingsButton.dataset.settingsCloseLabel || "Back"
      : settingsButton.dataset.settingsOpenLabel || "Settings";
    const title = showBack
      ? settingsButton.dataset.settingsCloseTitle || "Back to page"
      : settingsButton.dataset.settingsOpenTitle || "Settings";

    if (label) label.textContent = text;
    if (backIcon) backIcon.hidden = !showBack;
    if (settingsIcon) settingsIcon.hidden = showBack;

    settingsButton.classList.toggle("site-settings-button--back", showBack);
    settingsButton.title = title;
    settingsButton.setAttribute("aria-label", title);

    if (isInlineSettingsPage()) {
      settingsButton.setAttribute("aria-expanded", String(active));
      settingsButton.href = active
        ? settingsSourceContext?.path || getCurrentPagePath()
        : settingsButton.dataset.settingsOpenHref || settingsButton.href;
    }
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
    if (!settingsPage || isInlineSettingsPage()) {
      return getCurrentPageContext();
    }

    const returnPath = getSettingsReturnPath();
    const storedContext =
      window.PiggyStorage?.readSessionValue(SETTINGS_SOURCE_KEY) || null;
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

  function shouldReduceMotion() {
    const preferences = preferencesApi?.getPreferences?.() || {};
    if (preferences.reduceMotion === "reduce") return true;

    return (
      preferences.reduceMotion === "system" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
    );
  }

  window.PiggySettingsPage = {
    initialize,
  };
})();
