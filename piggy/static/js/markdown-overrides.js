document.addEventListener(
  "toggle",
  (event) => {
    const details = event.target;

    if (!(details instanceof HTMLDetailsElement)) return;
    if (!details.open) return;
    if (!details.closest(".md-content")) return;

    requestAnimationFrame(() => {
      const rect = details.getBoundingClientRect();
      const viewportHeight = window.innerHeight;

      const bottomPadding = 24;

      if (rect.bottom > viewportHeight - bottomPadding) {
        window.scrollBy({
          top: rect.bottom - viewportHeight + bottomPadding,
          behavior: "smooth",
        });
      }
    });
  },
  true,
);
