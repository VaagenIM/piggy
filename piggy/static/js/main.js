// Get elements
const settingsMenu = document.getElementById("settings-menu");
const settingsButton = document.getElementById("settings-button");
const closeButton = document.querySelector("#settings-menu .close-button");
const themeSelect = document.getElementById("theme-select");
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

// Set the selected option based on the current theme
themeSelect.value = currentTheme;

function stopAllAnimations() {
  stopMatrixAnimation();
  stopOceanShaderAnimation();
  stopSpaceAnimation();
}

// Start animation if a theme with animation is selected
switch (currentTheme) {
  case "matrix":
    startMatrixAnimation();
    break;
  case "ocean":
    startOceanShaderAnimation();
    break;
  case "space":
    startSpaceAnimation();
    break;
  default:
    stopAllAnimations();
}

// Event listener for the Settings button
settingsButton.addEventListener("click", openSettingsMenu);

// Event listener for the Close button inside the menu
closeButton.addEventListener("click", closeSettingsMenu);

// Event listener for theme selection change
themeSelect.addEventListener("change", function () {
  pageTransition();

  const selectedTheme = themeSelect.value;
  document.documentElement.setAttribute("data-theme", selectedTheme);
  localStorage.setItem("theme", selectedTheme); // Save theme to localStorage
  
  switch (selectedTheme) {
    case "matrix":
      stopAllAnimations();
      startMatrixAnimation();
      break;
    case "ocean":
      stopAllAnimations();
      startOceanShaderAnimation();
      break;
    case "space":
      stopAllAnimations();
      startSpaceAnimation();
      break;
    default:
      stopAllAnimations();
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
