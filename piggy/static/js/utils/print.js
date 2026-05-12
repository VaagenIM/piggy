let _preThemeRef = null;

function readCurrentTheme() {
  const html = typeof document !== "undefined" && document.documentElement;
  if (!html) return null;
  return html.getAttribute("data-theme") || null;
}

function applyTheme(theme) {
  if (theme == null) return;
  const html = typeof document !== "undefined" && document.documentElement;
  if (!html) return;
  html.setAttribute("data-theme", theme);
}

function handleBeforePrint() {
  _preThemeRef = readCurrentTheme();
  applyTheme("light");
}

function handleAfterPrint() {
  if (_preThemeRef == null) return;
  applyTheme(_preThemeRef);
  _preThemeRef = null;
}

if (typeof window !== "undefined") {
  window.addEventListener("beforeprint", handleBeforePrint);
  window.addEventListener("afterprint", handleAfterPrint);

  if (window.matchMedia) {
    const mql = window.matchMedia("print");
    const onChange = (e) =>
      e.matches ? handleBeforePrint() : handleAfterPrint();
    if (mql.addEventListener) mql.addEventListener("change", onChange);
    else if (mql.addListener) mql.addListener(onChange);
  }
}
