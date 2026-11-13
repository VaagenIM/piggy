function initializeLanguageOptions() {
  // Read by the GitHub Pages redirect in partials/header/language-selector.html
  const LANGUAGE_STORAGE_KEY = "piggy:language";

  function setLanguageCookie(lang) {
    if (lang) {
      document.cookie = `lang=${encodeURIComponent(lang)}; path=/; SameSite=Lax`;
    } else {
      document.cookie = "lang=; path=/; max-age=0; SameSite=Lax";
    }
  }

  function rememberLanguage(lang) {
    try {
      localStorage.setItem(LANGUAGE_STORAGE_KEY, lang);
    } catch (e) {
      // Without storage the choice simply isn't carried over to other pages
    }
  }

  function navigateToLanguageTarget(link) {
    const target = new URL(link.href, window.location.href).href;

    if (target === window.location.href) {
      window.location.reload();
    } else {
      window.location.assign(target);
    }
  }

  document
    .querySelectorAll(".language-selector [data-lang]")
    .forEach((link) => {
      link.addEventListener("click", () => rememberLanguage(link.dataset.lang));
    });

  document.querySelectorAll("[data-language-option]").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      setLanguageCookie(link.dataset.languageOption);
      navigateToLanguageTarget(link);
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeLanguageOptions);
} else {
  initializeLanguageOptions();
}
