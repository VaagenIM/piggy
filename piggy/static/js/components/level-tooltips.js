function initializeLevelTooltips() {
  const tips = document.querySelectorAll(".level-select .nav-tooltip");
  if (tips.length === 0) return;

  function viewportWidth() {
    return window.visualViewport
      ? window.visualViewport.width
      : document.documentElement.clientWidth;
  }

  function viewportHeight() {
    return window.visualViewport
      ? window.visualViewport.height
      : window.innerHeight;
  }

  function clamp(value, min, max) {
    if (max < min) return (min + max) / 2;
    return Math.min(Math.max(value, min), max);
  }

  function positionTooltip(tip) {
    const padding = 8;
    const trigger = tip.parentElement;
    if (!trigger) return;

    const triggerRect = trigger.getBoundingClientRect();
    const baseLeft = triggerRect.left + triggerRect.width / 2;
    const bottomTop = triggerRect.bottom + 5;

    tip.dataset.placement = "bottom";
    tip.style.setProperty("--arrow-shift", "0px");
    tip.style.setProperty("--tooltip-left", `${baseLeft}px`);
    tip.style.setProperty("--tooltip-top", `${bottomTop}px`);

    const vw = viewportWidth();
    const vh = viewportHeight();
    const rect = tip.getBoundingClientRect();
    const centeredLeft = clamp(
      baseLeft,
      padding + rect.width / 2,
      vw - padding - rect.width / 2,
    );

    let top = bottomTop;

    if (
      top + rect.height > vh - padding &&
      triggerRect.top - rect.height - 5 >= padding
    ) {
      top = triggerRect.top - rect.height - 5;
      tip.dataset.placement = "top";
    }

    const maxArrowShift = Math.max(0, rect.width / 2 - 12);
    const arrowShift = clamp(
      baseLeft - centeredLeft,
      -maxArrowShift,
      maxArrowShift,
    );

    tip.style.setProperty("--tooltip-left", `${centeredLeft}px`);
    tip.style.setProperty("--tooltip-top", `${top}px`);
    tip.style.setProperty("--arrow-shift", `${arrowShift}px`);
  }

  function showTooltip(tip) {
    positionTooltip(tip);
    tip.classList.add("is-tooltip-visible");
  }

  function hideTooltip(tip) {
    tip.classList.remove("is-tooltip-visible");
  }

  const updateAll = () => tips.forEach(positionTooltip);

  window.addEventListener("resize", updateAll, { passive: true });
  window.addEventListener("scroll", updateAll, { passive: true });
  window.addEventListener("orientationchange", updateAll, { passive: true });

  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", updateAll, {
      passive: true,
    });
    window.visualViewport.addEventListener("scroll", updateAll, {
      passive: true,
    });
  }

  document.querySelectorAll(".level-select").forEach((levelSelect) => {
    levelSelect.addEventListener("scroll", updateAll, { passive: true });
  });

  const resizeObserver =
    "ResizeObserver" in window
      ? new ResizeObserver((entries) => {
          for (const entry of entries) positionTooltip(entry.target);
        })
      : null;

  tips.forEach((tip, index) => {
    resizeObserver?.observe(tip);

    if (!tip.id) {
      tip.id = `level-tooltip-${index + 1}`;
    }

    tip.querySelectorAll("img").forEach((img) => {
      if (!img.complete) {
        img.addEventListener("load", () => positionTooltip(tip), {
          once: true,
        });
      }
    });

    const trigger = tip.parentElement;
    if (!trigger) return;

    trigger.setAttribute("aria-describedby", tip.id);

    const updateSoon = () => requestAnimationFrame(() => positionTooltip(tip));
    const showSoon = () => requestAnimationFrame(() => showTooltip(tip));

    trigger.addEventListener("pointerenter", showSoon);
    trigger.addEventListener("pointerleave", () => hideTooltip(tip));
    trigger.addEventListener("pointerdown", updateSoon);
    trigger.addEventListener("click", updateSoon);
    trigger.addEventListener("focusin", showSoon);
    trigger.addEventListener("focusout", () => hideTooltip(tip));
    trigger.addEventListener("touchstart", updateSoon, { passive: true });
  });

  updateAll();
}

function initializeLevelMenus() {
  function viewportWidth() {
    return window.visualViewport
      ? window.visualViewport.width
      : document.documentElement.clientWidth;
  }

  function viewportHeight() {
    return window.visualViewport
      ? window.visualViewport.height
      : window.innerHeight;
  }

  function positionMenu(menu) {
    const trigger = menu.querySelector(".level-menu-trigger");
    const dropdown = menu.querySelector(".level-menu-dropdown");
    if (!trigger || !dropdown) return;

    const padding = 8;
    const triggerRect = trigger.getBoundingClientRect();
    const rem = parseFloat(getComputedStyle(document.documentElement).fontSize);
    const top = triggerRect.bottom + 6;
    const left = Math.max(padding, triggerRect.left);
    const availableWidth = viewportWidth() - left - padding;
    const readableWidth = 22 * (Number.isFinite(rem) ? rem : 16);
    const width = Math.max(
      0,
      Math.min(Math.max(triggerRect.width, readableWidth), availableWidth),
    );
    const availableHeight = viewportHeight() - top - padding;
    const lockedHeight = Math.min(viewportHeight() * 0.6, availableHeight);

    dropdown.style.setProperty("--level-menu-dropdown-top", `${top}px`);
    dropdown.style.setProperty("--level-menu-dropdown-left", `${left}px`);
    dropdown.style.setProperty("--level-menu-dropdown-width", `${width}px`);
    dropdown.style.setProperty(
      "--level-menu-dropdown-max-height",
      `${Math.max(80, lockedHeight)}px`,
    );
  }

  function updateOpenMenus() {
    document.querySelectorAll(".level-menu[open]").forEach(positionMenu);
  }

  function closeLevelMenus() {
    document.querySelectorAll(".level-menu").forEach((menu) => {
      const trigger = menu.querySelector(".level-menu-trigger");
      menu.removeAttribute("open");
      trigger?.setAttribute("aria-expanded", "false");
    });
  }

  function closeLanguageMenus() {
    document.querySelectorAll("[data-language-select]").forEach((select) => {
      select.classList.remove("is-open");
      select.removeAttribute("open");
      select
        .querySelector("[aria-expanded]")
        ?.setAttribute("aria-expanded", "false");
    });
  }

  window.addEventListener("resize", updateOpenMenus, { passive: true });
  window.addEventListener("scroll", updateOpenMenus, { passive: true });
  window.addEventListener("orientationchange", updateOpenMenus, {
    passive: true,
  });

  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", updateOpenMenus, {
      passive: true,
    });
    window.visualViewport.addEventListener("scroll", updateOpenMenus, {
      passive: true,
    });
  }

  document.querySelectorAll(".level-menu").forEach((menu) => {
    const trigger = menu.querySelector(".level-menu-trigger");
    if (!trigger) return;

    function close() {
      menu.removeAttribute("open");
      trigger.setAttribute("aria-expanded", "false");
    }

    menu.addEventListener("toggle", () => {
      trigger.setAttribute("aria-expanded", String(menu.open));
      if (menu.open) {
        closeLanguageMenus();
        requestAnimationFrame(() => positionMenu(menu));
      }
    });

    trigger.addEventListener("pointerdown", () => {
      requestAnimationFrame(() => positionMenu(menu));
    });

    document.addEventListener("click", (event) => {
      if (menu.open && !menu.contains(event.target)) close();
    });

    menu.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        close();
        trigger.focus();
      }
    });
  });

  document.querySelectorAll("[data-language-select]").forEach((select) => {
    select.addEventListener("toggle", () => {
      if (select.open || select.classList.contains("is-open")) {
        closeLevelMenus();
      }
    });
  });
}

function initializeLevelControls() {
  initializeLevelTooltips();
  initializeLevelMenus();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeLevelControls);
} else {
  initializeLevelControls();
}
