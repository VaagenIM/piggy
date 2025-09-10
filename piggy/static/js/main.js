document.addEventListener("DOMContentLoaded", () => {
  // Get elements for the settings menu
  const settingsMenu = document.getElementById("settings-menu");
  const settingsButton = document.getElementById("settings-button");
  const closeButton = document.querySelector("#settings-menu .close-button");

  // Get custom select elements for theme and font
  const themeSelect = document.getElementById("theme-select");
  const themeSelected = themeSelect.querySelector(".selected");
  const fontSelect = document.getElementById("font-select");
  const fontSelected = fontSelect
    ? fontSelect.querySelector(".selected")
    : null;

  // --- Helper Functions ---
  function closeAllCustomSelects(except = null) {
    document.querySelectorAll(".custom-select").forEach((select) => {
      if (select !== except) {
        select.classList.remove("open");
        const optionsContainer = select.querySelector(".options-container");
        if (optionsContainer) {
          optionsContainer.style.maxHeight = "";
        }
      }
    });
  }

  // Dynamically calculate available space and set max-height on the options container
  function updateOptionsMaxHeight(select) {
    const optionsContainer = select.querySelector(".options-container");
    const rect = optionsContainer.getBoundingClientRect();
    const availableHeight = window.innerHeight - rect.top - 10; // 10px margin
    optionsContainer.style.maxHeight = availableHeight + "px";
  }

  // Smooth page transition
  function pageTransition() {
    document.body.classList.add("transition");
    setTimeout(() => {
      document.body.classList.remove("transition");
    }, 1000);
  }

  // Stop all background animations
  function stopAllAnimations() {
    stopMatrixAnimation();
    stopOceanShaderAnimation();
    stopDesertShaderAnimation();
    stopSpaceAnimation();
  }

  // --- Background Animations ---
  // currentTheme is set in on-load.js; fallback to system preference if not set
  const currentTheme = localStorage.getItem("theme") || systemPreferredTheme;
  switch (currentTheme) {
    case "matrix":
      startMatrixAnimation();
      break;
    case "ocean":
      startOceanShaderAnimation();
      break;
    case "desert":
      startDesertShaderAnimation();
      break;
    case "space":
      startSpaceAnimation();
      break;
    default:
      stopAllAnimations();
  }

  // --- Settings Menu Functions ---
  function openSettingsMenu() {
    settingsMenu.classList.add("open");
  }

  function closeSettingsMenu() {
    settingsMenu.classList.remove("open");
  }

  // --- Initialize Theme Custom Select ---
  const matchingThemeOption = themeSelect.querySelector(
    `.option[data-value="${currentTheme}"]`,
  );
  if (matchingThemeOption) {
    themeSelected.textContent = matchingThemeOption.textContent;
    themeSelected.setAttribute("data-value", currentTheme);
  }

  // Toggle theme dropdown when clicking its selected area
  themeSelected.addEventListener("click", (e) => {
    closeAllCustomSelects(themeSelect);
    themeSelect.classList.toggle("open");
    if (themeSelect.classList.contains("open")) {
      updateOptionsMaxHeight(themeSelect);
    }
    e.stopPropagation();
  });

  // Attach click event listeners to each theme option
  themeSelect.querySelectorAll(".option").forEach((option) => {
    option.addEventListener("click", function (e) {
      const selectedTheme = this.getAttribute("data-value");

      themeSelected.textContent = this.textContent;
      themeSelected.setAttribute("data-value", selectedTheme);

      // save theme and apply
      localStorage.setItem("theme", selectedTheme);
      document.documentElement.setAttribute("data-theme", selectedTheme);

      pageTransition();
      stopAllAnimations();
      switch (selectedTheme) {
        case "matrix":
          startMatrixAnimation();
          break;
        case "ocean":
          startOceanShaderAnimation();
          break;
        case "desert":
          startDesertShaderAnimation();
          break;
        case "space":
          startSpaceAnimation();
          break;
        default:
          break;
      }

      // Close dropdown after selection
      themeSelect.classList.remove("open");

      const optionsContainer = themeSelect.querySelector(".options-container");
      optionsContainer.style.maxHeight = "";

      e.stopPropagation();
    });
  });

  // --- Initialize Font Custom Select ---
  if (fontSelect && fontSelected) {
    const savedFontTheme = localStorage.getItem("fontTheme") || "default";
    const matchingFontOption = fontSelect.querySelector(
      `.option[data-value="${savedFontTheme}"]`,
    );
    if (matchingFontOption) {
      fontSelected.textContent = matchingFontOption.textContent;
      fontSelected.setAttribute("data-value", savedFontTheme);
    }

    // Toggle font dropdown on click
    fontSelected.addEventListener("click", (e) => {
      closeAllCustomSelects(fontSelect);
      fontSelect.classList.toggle("open");
      if (fontSelect.classList.contains("open")) {
        updateOptionsMaxHeight(fontSelect);
      }
      e.stopPropagation();
    });

    // Attach event listeners for each font option
    fontSelect.querySelectorAll(".option").forEach((option) => {
      option.addEventListener("click", function (e) {
        const selectedFont = this.getAttribute("data-value");
        fontSelected.textContent = this.textContent;
        fontSelected.setAttribute("data-value", selectedFont);
        localStorage.setItem("fontTheme", selectedFont);
        document.documentElement.setAttribute("data-font-theme", selectedFont);
        fontSelect.classList.remove("open");
        e.stopPropagation();
      });
    });
  }

  // --- Global Listeners ---
  document.addEventListener("click", () => {
    closeAllCustomSelects();
  });

  // Settings menu event listeners
  settingsButton.addEventListener("click", openSettingsMenu);
  closeButton.addEventListener("click", closeSettingsMenu);
  window.addEventListener("click", function (event) {
    if (
      settingsMenu.classList.contains("open") &&
      !settingsMenu.contains(event.target) &&
      event.target !== settingsButton
    ) {
      closeSettingsMenu();
    }
  });
});
