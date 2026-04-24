const systemPreferredTheme =
  window.matchMedia && window.matchMedia("(prefers-contrast: more)").matches
    ? "high-contrast"
    : window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";

function getThemeType(themePath) {
  const themes = Array.isArray(window.PIGGY_THEMES) ? window.PIGGY_THEMES : [];
  const themeData = themes.find((theme) => theme.path === themePath);

  return themeData?.type || "dark";
}

// Initialize theme and font settings asap
const currentTheme = localStorage.getItem("theme") || systemPreferredTheme;
const currentThemeType = getThemeType(currentTheme);

const fontTheme = localStorage.getItem("fontTheme") || "default";
const monoTheme = localStorage.getItem("monoTheme") || "default";
const fontSize = localStorage.getItem("fontSize") || "default";

document.documentElement.setAttribute("data-theme", currentTheme);
document.documentElement.setAttribute("data-theme-type", currentThemeType);
document.documentElement.setAttribute("data-font-theme", fontTheme);
document.documentElement.setAttribute("data-mono-theme", monoTheme);
document.documentElement.setAttribute("data-font-size", fontSize);
