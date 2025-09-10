// Initialize theme and font settings asap
const currentTheme = localStorage.getItem("theme") || "dark";
const fontTheme = localStorage.getItem("fontTheme") || "default";

document.documentElement.setAttribute("data-theme", currentTheme);
document.documentElement.setAttribute("data-font-theme", fontTheme);