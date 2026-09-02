(function () {
  const dropdowns = [];
  const closeTimers = new Map();

  function shouldReduceMotion() {
    return (
      window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }

  function getPanel(details) {
    return details.querySelector(":scope > .piggy-dropdown-panel");
  }

  function getSummary(details) {
    return details.querySelector(":scope > .piggy-dropdown-trigger");
  }

  function clearCloseTimer(details) {
    const timer = closeTimers.get(details);
    if (timer) window.clearTimeout(timer);
    closeTimers.delete(details);
    details.classList.remove("piggy-dropdown-closing");
  }

  function openDropdown(details) {
    if (details.open) return;
    clearCloseTimer(details);
    closeAllExcept(details);
    details.open = true;
  }

  function closeDropdown(details, options = {}) {
    if (!details.open) return;
    clearCloseTimer(details);

    const finish = () => {
      closeTimers.delete(details);
      details.open = false;
      details.classList.remove("piggy-dropdown-closing");
      if (options.focusSummary) {
        getSummary(details)?.focus();
      }
    };

    if (options.animate === false || shouldReduceMotion()) {
      finish();
      return;
    }

    details.classList.add("piggy-dropdown-closing");
    const panel = getPanel(details);
    panel?.addEventListener("animationend", finish, { once: true });
    closeTimers.set(details, window.setTimeout(finish, 220));
  }

  function toggleDropdown(details) {
    if (details.open && !details.classList.contains("piggy-dropdown-closing")) {
      closeDropdown(details);
    } else {
      openDropdown(details);
    }
  }

  function closeAllExcept(exception, options = {}) {
    dropdowns.forEach((details) => {
      if (details !== exception && details.open) {
        closeDropdown(details, options);
      }
    });
  }

  function positionPanel(details) {
    const panel = getPanel(details);
    const summary = getSummary(details);
    if (!panel || !summary) return;

    panel.classList.remove("piggy-dropdown-panel--flip-up");

    const padding = 8;
    const summaryRect = summary.getBoundingClientRect();
    const panelRect = panel.getBoundingClientRect();
    const viewportHeight = window.visualViewport
      ? window.visualViewport.height
      : window.innerHeight;

    const overflowsBelow =
      summaryRect.bottom + panelRect.height + padding > viewportHeight;
    const fitsAbove = summaryRect.top - panelRect.height - padding >= 0;

    if (overflowsBelow && fitsAbove) {
      panel.classList.add("piggy-dropdown-panel--flip-up");
    }
  }

  function registerDropdown(details) {
    if (!details || dropdowns.includes(details)) return;

    const summary = getSummary(details);
    if (!summary) return;

    dropdowns.push(details);

    summary.addEventListener("click", (event) => {
      event.preventDefault();
      toggleDropdown(details);
    });

    details.addEventListener("click", (event) => {
      if (event.target.closest(".piggy-dropdown-row")) {
        closeDropdown(details);
      }
    });

    details.addEventListener("toggle", () => {
      summary.setAttribute("aria-expanded", String(details.open));
      if (details.open) {
        requestAnimationFrame(() => positionPanel(details));
      }
    });
  }

  function initializeDropdowns() {
    document
      .querySelectorAll("[data-dropdown]")
      .forEach((details) => registerDropdown(details));
  }

  document.addEventListener("click", (event) => {
    dropdowns.forEach((details) => {
      if (details.open && !details.contains(event.target)) {
        closeDropdown(details);
      }
    });
  });

  document.addEventListener("keydown", (event) => {
    const activeDetails = event.target.closest("[data-dropdown]");

    if (event.key === "Escape") {
      const openDetails = dropdowns.filter((details) => details.open);
      if (openDetails.length === 0) return;
      event.preventDefault();
      openDetails.forEach((details) => {
        closeDropdown(details, { focusSummary: details === activeDetails });
      });
      return;
    }

    if (!activeDetails) return;

    const rows = Array.from(
      activeDetails.querySelectorAll(".piggy-dropdown-row"),
    );
    if (rows.length === 0) return;

    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      openDropdown(activeDetails);

      const currentIndex = rows.indexOf(document.activeElement);
      const selectedIndex = Math.max(
        rows.findIndex((row) => row.getAttribute("aria-selected") === "true"),
        0,
      );
      let nextIndex = currentIndex === -1 ? selectedIndex : currentIndex;
      if (currentIndex !== -1) {
        nextIndex += event.key === "ArrowDown" ? 1 : -1;
      }
      rows[((nextIndex % rows.length) + rows.length) % rows.length]?.focus();
      return;
    }

    if (event.key === "Home" || event.key === "End") {
      if (!activeDetails.open || !event.target.closest(".piggy-dropdown-row")) {
        return;
      }
      event.preventDefault();
      rows[event.key === "Home" ? 0 : rows.length - 1]?.focus();
    }
  });

  window.addEventListener(
    "scroll",
    (event) => {
      dropdowns.forEach((details) => {
        if (!details.open) return;
        const panel = getPanel(details);
        if (panel && panel.contains(event.target)) return;
        closeDropdown(details, { animate: false });
      });
    },
    { passive: true, capture: true },
  );

  window.PiggyDropdown = {
    register: registerDropdown,
    close: closeDropdown,
    closeAll: (options) => closeAllExcept(null, options),
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeDropdowns);
  } else {
    initializeDropdowns();
  }
})();
