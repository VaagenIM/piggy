const systemPreferredTheme =
  window.matchMedia && window.matchMedia("(prefers-contrast: more)").matches
    ? "high-contrast"
    : window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";

// Initialize theme and font settings asap
const currentTheme = localStorage.getItem("theme") || systemPreferredTheme;
const fontTheme = localStorage.getItem("fontTheme") || "default";

document.documentElement.setAttribute("data-theme", currentTheme);
document.documentElement.setAttribute("data-font-theme", fontTheme);
