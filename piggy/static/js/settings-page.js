(function () {
  const SETTINGS_SOURCE_KEY = "piggy.settingsSource.v1";

  let preferencesApi = null;
  let settingsPage = null;
  let settingsTabs = null;
  let settingsSourceContext = null;
  let initializedApi = null;

  function initialize(nextPreferencesApi) {
    if (initializedApi) return initializedApi;

    preferencesApi = nextPreferencesApi;
    settingsPage = document.getElementById("settings-page");
    settingsTabs = settingsPage?.querySelector("[data-settings-tabs]");
    settingsSourceContext = getSettingsSourceContext();

    const settingsButton = document.getElementById("settings-button");
    const resetButton = document.getElementById("settings-reset-button");

    initializeSettingsTabs();
    window.PiggySettingsControls?.render(settingsPage, preferencesApi);
    updateSettingsControls(preferencesApi.getPreferences());
    updateReturnLink();

    settingsButton?.addEventListener("click", captureSettingsSource);
    resetButton?.addEventListener("click", () =>
      preferencesApi.applyPreset("default"),
    );

    settingsPage?.addEventListener("click", handleSettingsClick);
    settingsPage?.addEventListener("change", handleSettingsChange);

    document.addEventListener("piggy:preferenceschange", (event) => {
      updateSettingsControls(event.detail.preferences);
    });

    initializedApi = {
      isSettingsPage: Boolean(settingsPage),
      getSourceContext() {
        return settingsSourceContext;
      },
    };

    return initializedApi;
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

    if (prefId === "readerPreset") {
      preferencesApi.applyPreset(prefValue);
      return;
    }

    preferencesApi.setPreference(prefId, prefValue);
  }

  function handleSettingsChange(event) {
    const select = event.target.closest("[data-pref-select]");
    if (!select) return;

    preferencesApi.setPreference(select.dataset.prefSelect, select.value);
  }

  function updateSettingsControls(preferences) {
    window.PiggySettingsControls?.update(
      settingsPage,
      preferencesApi,
      preferences,
    );
  }

  function captureSettingsSource() {
    if (settingsPage) return;

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
        sourceContext.pageKey === getCurrentPageKey() ? "Back" : "Back to page";
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
    if (!settingsPage) {
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

  window.PiggySettingsPage = {
    initialize,
  };
})();
