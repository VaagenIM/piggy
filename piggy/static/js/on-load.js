// Initialize theme and font settings asap
const systemPreferredTheme =
  window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";

const currentTheme = localStorage.getItem("theme") || systemPreferredTheme;
const fontTheme = localStorage.getItem("fontTheme") || "default";

document.documentElement.setAttribute("data-theme", currentTheme);
document.documentElement.setAttribute("data-font-theme", fontTheme);
