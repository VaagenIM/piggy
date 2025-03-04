// Get elements
const settingsMenu = document.getElementById("settings-menu");
const settingsButton = document.getElementById("settings-button");
const closeButton = document.querySelector("#settings-menu .close-button");
const themeSelect = document.getElementById("theme-select");
const dyslexiaButton = document.getElementById("dyslexia-button");
// Declared in on-load.js
// const currentTheme = localStorage.getItem("theme") || "dark";
// const fontTheme = localStorage.getItem("data-font-theme") || "default";

function pageTransition() {
  document.body.classList.add("transition");
  setTimeout(() => {
    document.body.classList.remove("transition");
  }, 1000);
}

// Function to open the settings menu
function openSettingsMenu() {
  settingsMenu.classList.add("open");
}

// Function to close the settings menu
function closeSettingsMenu() {
  settingsMenu.classList.remove("open");
}

function toggleDyslexia() {
  // Retrieve the current theme from the data attribute
  let fontTheme = document.documentElement.getAttribute("data-font-theme");

  // Toggle between 'default' and 'dyslexia'
  if (fontTheme === "default") {
    document.documentElement.setAttribute("data-font-theme", "dyslexia");
    localStorage.setItem("data-font-theme", "dyslexia"); // Save theme to localStorage
    dyslexiaButton.innerHTML = "Dyslexia Friendly Mode [✅]";
  } else {
    document.documentElement.setAttribute("data-font-theme", "default");
    localStorage.setItem("data-font-theme", "default"); // Save theme to localStorage
    dyslexiaButton.innerHTML = "Dyslexia Friendly Mode";
  }

  pageTransition();
}

// TODO: fix this:
if (fontTheme === "default") {
  dyslexiaButton.innerHTML = "Dyslexia Friendly Mode";
} else {
  dyslexiaButton.innerHTML = "Dyslexia Friendly Mode [✅]";
}

// Set the selected option based on the current theme
themeSelect.value = currentTheme;

// Start Matrix animation if the theme is "matrix"
if (currentTheme === "matrix") {
  startMatrixAnimation();
} else if (currentTheme === "ocean") {
  startOceanShaderAnimation();
}

// Event listener for the Settings button
settingsButton.addEventListener("click", openSettingsMenu);

// Event listener for the Close button inside the menu
closeButton.addEventListener("click", closeSettingsMenu);

dyslexiaButton.addEventListener("click", toggleDyslexia);

// Event listener for theme selection change
themeSelect.addEventListener("change", function () {
  pageTransition();

  const selectedTheme = themeSelect.value;
  document.documentElement.setAttribute("data-theme", selectedTheme);
  localStorage.setItem("theme", selectedTheme); // Save theme to localStorage

  // Activate or deactivate the Matrix effect based on the selected theme
  if (selectedTheme === "matrix") {
    stopOceanShaderAnimation();
    startMatrixAnimation();
  } else if (selectedTheme === "ocean") {
    stopMatrixAnimation();
    startOceanShaderAnimation();
  } else {
    stopMatrixAnimation();
    stopOceanShaderAnimation();
  }
});

// Close settings menu when clicking outside of it
window.addEventListener("click", function (event) {
  if (
    settingsMenu.classList.contains("open") && // Only if the menu is open
    !settingsMenu.contains(event.target) && // Click is outside the menu
    event.target !== settingsButton // Click is not on the settings button
  ) {
    closeSettingsMenu();
  }
});

// card search script
