function initializeLanguageOptions() {
  function setLanguageCookie(lang) {
    if (lang) {
      document.cookie = `lang=${encodeURIComponent(lang)}; path=/; SameSite=Lax`;
    } else {
      document.cookie = "lang=; path=/; max-age=0; SameSite=Lax";
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
