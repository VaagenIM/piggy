(function () {
  const SCROLL_KEY = "piggy.readerScrollPositions.v1";

  let preferencesApi = null;
  let settingsPageApi = null;
  let settingsPage = null;
  let readerRuler = null;
  let markdownContent = null;
  let lastPreferences = null;
  let scrollSaveTimeout = null;
  let initialized = false;

  function initialize(nextPreferencesApi, options = {}) {
    if (initialized) return;
    initialized = true;

    preferencesApi = nextPreferencesApi;
    settingsPageApi = options.settingsPageApi || null;
    settingsPage = document.getElementById("settings-page");
    readerRuler = document.getElementById("reader-ruler");
    markdownContent = document.querySelector(
      "main .md-content:not(.settings-reader-preview)",
    );
    lastPreferences = preferencesApi.getPreferences();

    updateThemeEffects(lastPreferences);
    initializeReaderRuler();
    initializeRememberedPosition();
    initializeScrollTracking();
    initializeReducedMotionListener();

    document.addEventListener("piggy:preferenceschange", (event) => {
      const nextPreferences = event.detail.preferences;
      const changedKey = event.detail.changedKey;

      updateThemeEffects(nextPreferences, changedKey);

      if (changedKey === "rememberPosition" && settingsPage) {
        saveSourceScrollPosition();
      } else if (changedKey === "rememberPosition") {
        saveScrollPosition();
      }

      lastPreferences = nextPreferences;
    });
  }

  function initializeScrollTracking() {
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
  }

  function initializeReducedMotionListener() {
    window
      .matchMedia?.("(prefers-reduced-motion: reduce)")
      .addEventListener?.("change", () => {
        updateThemeEffects(preferencesApi.getPreferences(), "reduceMotion");
      });
  }

  function updateThemeEffects(preferences, changedKey = "") {
    const themeChanged =
      changedKey === "theme" ||
      (changedKey === "readerPreset" &&
        preferences.theme !== lastPreferences?.theme);

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

    const positions = window.PiggyStorage?.readLocalMap(SCROLL_KEY) || {};
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

    const positions = window.PiggyStorage?.readLocalMap(SCROLL_KEY) || {};
    positions[getCurrentPageKey()] = Math.max(0, Math.round(window.scrollY));
    window.PiggyStorage?.writeLocalMap(SCROLL_KEY, positions);
  }

  function saveSourceScrollPosition() {
    if (preferencesApi.getPreferences().rememberPosition !== "on") return;

    const sourceContext = settingsPageApi?.getSourceContext?.();
    if (!sourceContext?.pageKey) return;
    if (!sourceContext.capturedAt) return;
    if (!Number.isFinite(sourceContext.scrollY)) return;

    const positions = window.PiggyStorage?.readLocalMap(SCROLL_KEY) || {};
    positions[sourceContext.pageKey] = Math.max(
      0,
      Math.round(sourceContext.scrollY),
    );
    window.PiggyStorage?.writeLocalMap(SCROLL_KEY, positions);
  }

  function getCurrentPageKey() {
    return `${window.location.pathname}${window.location.search}`;
  }

  window.PiggyReaderRuntime = {
    initialize,
  };
})();
