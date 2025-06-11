const currentTheme = localStorage.getItem("theme") || "dark";
const fontTheme = localStorage.getItem("data-font-theme") || "default";
document.documentElement.setAttribute("data-theme", currentTheme);
document.documentElement.setAttribute("data-font-theme", fontTheme);
