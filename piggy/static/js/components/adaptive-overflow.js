function initializeAdaptiveOverflow() {
  const containers = Array.from(
    document.querySelectorAll("[data-adaptive-overflow]"),
  );
  // Compactors apply their `data-adaptive-compact` steps one by one (as
  // `data-compact` tokens for CSS to act on) until their content fits.
  const compactors = Array.from(
    document.querySelectorAll("[data-adaptive-compact]"),
  );
  if (containers.length === 0 && compactors.length === 0) return;

  let scheduled = false;
  const pressedContainers = new Set();

  function getTiers(container) {
    return Array.from(
      container.querySelectorAll(":scope > [data-adaptive-tier]"),
    ).sort(
      (a, b) => Number(a.dataset.adaptiveTier) - Number(b.dataset.adaptiveTier),
    );
  }

  function getAvailableWidth(container) {
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
    return containerRect.width - reserveWidth - gap;
  }

  function persist(element, kind, value) {
    const adaptiveKey = element.dataset.adaptiveKey;
    if (!adaptiveKey) return;
    try {
      localStorage.setItem(`piggy:adaptive-${kind}:${adaptiveKey}`, value);
    } catch (e) {
      // localStorage may be unavailable (private mode, quota, etc.) --
      // persistence is just an anti-flash nicety, safe to skip.
    }
  }

  function updateContainer(container) {
    if (pressedContainers.has(container)) return;

    const tiers = getTiers(container);
    if (tiers.length === 0) return;

    const availableWidth = getAvailableWidth(container);

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

    persist(container, "tier", String(tiers.indexOf(chosen)));

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

  // Fits when nothing overflows the compactor and every adaptive container
  // inside it has room for at least its narrowest tier.
  function compactorFits(compactor) {
    if (compactor.scrollWidth > compactor.clientWidth + 1) return false;

    return Array.from(
      compactor.querySelectorAll("[data-adaptive-overflow]"),
    ).every((container) => {
      const narrowest = getTiers(container).at(-1);
      return (
        !narrowest || narrowest.scrollWidth <= getAvailableWidth(container) + 1
      );
    });
  }

  function updateCompactor(compactor) {
    const steps = compactor.dataset.adaptiveCompact.split(/\s+/);
    const applied = [];

    // Always start from the uncompacted layout, so a wider viewport can undo
    // earlier steps (the layout is only measured here, never painted)
    compactor.dataset.compact = "";
    for (const step of steps.filter(Boolean)) {
      if (compactorFits(compactor)) break;
      applied.push(step);
      compactor.dataset.compact = applied.join(" ");
    }

    persist(compactor, "compact", compactor.dataset.compact);
  }

  function updateAll() {
    scheduled = false;
    // Compacting changes the room left for the containers, so it goes first
    compactors.forEach(updateCompactor);
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
    [...compactors, ...containers].forEach((element) =>
      resizeObserver.observe(element),
    );
    // A compactor's own size rarely changes (e.g. a full-width navbar), but
    // what it holds does, e.g. the font size or a label swapped by script
    compactors.forEach((compactor) =>
      Array.from(compactor.children).forEach((child) =>
        resizeObserver.observe(child),
      ),
    );
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
