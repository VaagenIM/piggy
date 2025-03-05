document.addEventListener("DOMContentLoaded", () => {
  // Get elements for the settings menu
  const settingsMenu = document.getElementById("settings-menu");
  const settingsButton = document.getElementById("settings-button");
  const closeButton = document.querySelector("#settings-menu .close-button");

  // Get custom select elements for theme and font
  const themeSelect = document.getElementById("theme-select");
  const themeSelected = themeSelect.querySelector(".selected");
  const fontSelect = document.getElementById("font-select");
  const fontSelected = fontSelect ? fontSelect.querySelector(".selected") : null;

  // --- Helper Functions ---
  // Close all custom selects (except an optional one to keep open)
  function closeAllCustomSelects(except = null) {
    document.querySelectorAll(".custom-select").forEach(select => {
      if (select !== except) {
        select.classList.remove("open");
        const optionsContainer = select.querySelector(".options-container");
        if (optionsContainer) {
          // Clear the inline maxHeight so it reverts to the CSS (0 when not open)
          optionsContainer.style.maxHeight = "";
        }
      }
    });
  }

  // Dynamically calculate available space and set max-height on the options container
  function updateOptionsMaxHeight(select) {
    const optionsContainer = select.querySelector('.options-container');
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

  // Stop all background animations (functions from your animation files)
  function stopAllAnimations() {
    stopMatrixAnimation();
    stopOceanShaderAnimation();
    stopSpaceAnimation();
  }

  // --- Background Animations ---
  // currentTheme is set in on-load.js; fallback to "dark" if missing
  const currentTheme = localStorage.getItem("theme") || "dark";
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

  // --- Settings Menu Functions ---
  function openSettingsMenu() {
    settingsMenu.classList.add("open");
  }
  function closeSettingsMenu() {
    settingsMenu.classList.remove("open");
  }

  // --- Initialize Theme Custom Select ---
  const matchingThemeOption = themeSelect.querySelector(`.option[data-value="${currentTheme}"]`);
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
  themeSelect.querySelectorAll(".option").forEach(option => {
    option.addEventListener("click", function (e) {
      const selectedTheme = this.getAttribute("data-value");
      // Update the display
      themeSelected.textContent = this.textContent;
      themeSelected.setAttribute("data-value", selectedTheme);
      
      // Save and apply the new theme
      localStorage.setItem("theme", selectedTheme);
      document.documentElement.setAttribute("data-theme", selectedTheme);

      // Execute page transition and manage animations
      pageTransition();
      stopAllAnimations();
      switch (selectedTheme) {
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
          break;
      }

      // Close dropdown after selection
      themeSelect.classList.remove("open");
  
      // Also clear the inline style:
      const optionsContainer = themeSelect.querySelector(".options-container");
      optionsContainer.style.maxHeight = "";
      
      e.stopPropagation();
    });
  });

  // --- Initialize Font Custom Select (if available) ---
  if (fontSelect && fontSelected) {
    const savedFontTheme = localStorage.getItem("fontTheme") || "default";
    const matchingFontOption = fontSelect.querySelector(`.option[data-value="${savedFontTheme}"]`);
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
    fontSelect.querySelectorAll(".option").forEach(option => {
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
  // Close any open custom select when clicking outside
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
