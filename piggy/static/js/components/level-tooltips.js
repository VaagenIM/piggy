document.addEventListener("DOMContentLoaded", () => {
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

  tips.forEach((tip) => {
    resizeObserver?.observe(tip);

    tip.querySelectorAll("img").forEach((img) => {
      if (!img.complete) {
        img.addEventListener("load", () => positionTooltip(tip), {
          once: true,
        });
      }
    });

    const trigger = tip.parentElement;
    if (!trigger) return;

    const updateSoon = () => requestAnimationFrame(() => positionTooltip(tip));

    trigger.addEventListener("pointerenter", updateSoon);
    trigger.addEventListener("pointerdown", updateSoon);
    trigger.addEventListener("click", updateSoon);
    trigger.addEventListener("focusin", updateSoon);
    trigger.addEventListener("touchstart", updateSoon, { passive: true });
  });

  updateAll();
});
