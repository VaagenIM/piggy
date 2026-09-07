(function () {
  const STORAGE_KEY = "piggy.siteLanguage";

  function setSiteLanguage(code) {
    try {
      window.localStorage.setItem(STORAGE_KEY, code);
    } catch {
      // localStorage unavailable - fall through to the cookie-only attempt below.
    }

    try {
      document.cookie =
        "ui_locale=" + code + "; path=/; max-age=31536000; samesite=lax";
    } catch {
      // Cookies unavailable; nothing more we can do client-side.
    }

    window.location.reload();
  }

  document.addEventListener("click", (event) => {
    const target = event.target.closest("[data-ui-locale]");
    if (!target) return;

    event.preventDefault();
    const code = target.getAttribute("data-ui-locale");
    if (code) setSiteLanguage(code);
  });
})();
