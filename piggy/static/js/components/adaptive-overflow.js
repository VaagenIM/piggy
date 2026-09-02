function initializeAdaptiveOverflow() {
  const containers = Array.from(
    document.querySelectorAll("[data-adaptive-overflow]"),
  );
  if (containers.length === 0) return;

  let scheduled = false;
  const pressedContainers = new Set();

  function getTiers(container) {
    return Array.from(
      container.querySelectorAll(":scope > [data-adaptive-tier]"),
    ).sort(
      (a, b) => Number(a.dataset.adaptiveTier) - Number(b.dataset.adaptiveTier),
    );
  }

  function updateContainer(container) {
    if (pressedContainers.has(container)) return;

    const tiers = getTiers(container);
    if (tiers.length === 0) return;

    const reserveSelector = container.dataset.adaptiveReserveSelector;
    const reserveEl = reserveSelector
      ? container.querySelector(reserveSelector)
      : null;

    const containerRect = container.getBoundingClientRect();
    const reserveWidth = reserveEl
      ? reserveEl.getBoundingClientRect().width
      : 0;
    const containerStyle = getComputedStyle(container);
    const gap = parseFloat(containerStyle.columnGap || containerStyle.gap) || 0;
    const availableWidth = containerRect.width - reserveWidth - gap;

    let chosen = tiers[tiers.length - 1]; // guaranteed fallback: narrowest tier
    for (const tier of tiers) {
      const collapseAt = parseInt(tier.dataset.adaptiveCollapseAt || "", 10);
      const countSelector = tier.dataset.adaptiveCountSelector;
      const countTarget = countSelector
        ? tier.querySelector(countSelector)
        : tier;
      const overCount =
        Number.isFinite(collapseAt) &&
        countTarget &&
        countTarget.children.length > collapseAt;
      const overWidth = tier.scrollWidth > availableWidth + 1;
      if (!overCount && !overWidth) {
        chosen = tier;
        break;
      }
    }

    const previousActive = tiers.find((tier) =>
      tier.classList.contains("is-active"),
    );
    const previousEffective = previousActive || tiers[0];
    if (previousEffective === chosen) return; // no change

    tiers.forEach((tier) =>
      tier.classList.toggle("is-active", tier === chosen),
    );
    container.dataset.activeTier = String(tiers.indexOf(chosen));

    if (previousEffective !== chosen) {
      const openDropdown = previousEffective.querySelector(
        "[data-dropdown][open]",
      );
      if (openDropdown) {
        window.PiggyDropdown?.close(openDropdown, { animate: false });
      }
    }
  }

  function updateAll() {
    scheduled = false;
    containers.forEach(updateContainer);
  }

  function scheduleUpdate() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(updateAll);
  }

  window.addEventListener("resize", scheduleUpdate, { passive: true });
  window.addEventListener("orientationchange", scheduleUpdate, {
    passive: true,
  });

  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", scheduleUpdate, {
      passive: true,
    });
  }

  if (document.fonts) {
    document.fonts.ready.then(scheduleUpdate);
  }

  if ("ResizeObserver" in window) {
    const resizeObserver = new ResizeObserver(scheduleUpdate);
    containers.forEach((container) => resizeObserver.observe(container));
  }

  containers.forEach((container) => {
    const release = () => {
      pressedContainers.delete(container);
      scheduleUpdate();
    };
    container.addEventListener("pointerdown", () =>
      pressedContainers.add(container),
    );
    container.addEventListener("pointerup", release);
    container.addEventListener("pointercancel", release);
  });

  scheduleUpdate();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeAdaptiveOverflow);
} else {
  initializeAdaptiveOverflow();
}
