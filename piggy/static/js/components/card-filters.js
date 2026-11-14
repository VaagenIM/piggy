function initializeCardFilters() {
  document.querySelectorAll("[data-card-filters]").forEach((bar) => {
    const scope = bar.closest("[data-card-filter-scope]") || document.body;
    const cards = Array.from(scope.querySelectorAll(".piggy-card[data-tags]"));
    const chips = Array.from(bar.querySelectorAll("[data-filter-tag]"));
    const reset = bar.querySelector("[data-card-filters-reset]");
    const more = bar.querySelector("[data-card-filters-more]");
    const empty = scope.querySelector("[data-card-filters-empty]");
    const hiddenTags = new Set(
      chips
        .filter((chip) => chip.hasAttribute("data-hidden-tag"))
        .map((chip) => chip.dataset.filterTag),
    );

    // Kept for the tab session, so going back to the page keeps the filters
    const storageKey = `piggy:card-filters:${window.location.pathname}`;
    const known = new Set(chips.map((chip) => chip.dataset.filterTag));
    const stored = window.PiggyStorage?.readSessionValue(storageKey);
    const selected = new Set(
      (Array.isArray(stored) ? stored : []).filter((tag) => known.has(tag)),
    );

    // Hidden tags hide a card until one of them is picked, the other tags
    // narrow the cards down to those with any of the picked tags
    function isShown(tags) {
      const hiddenBy = tags.filter((tag) => hiddenTags.has(tag));
      if (hiddenBy.length && !hiddenBy.some((tag) => selected.has(tag))) {
        return false;
      }
      const picked = [...selected].filter((tag) => !hiddenTags.has(tag));
      return picked.length === 0 || tags.some((tag) => picked.includes(tag));
    }

    function apply() {
      cards.forEach((card) => {
        card.hidden = !isShown(card.dataset.tags.split("|").filter(Boolean));
      });

      scope
        .querySelectorAll("[data-card-filter-section]")
        .forEach((section) => {
          const shown = section.querySelectorAll(".piggy-card:not([hidden])");
          section.hidden = shown.length === 0;
          const count = section.querySelector("[data-card-filter-count]");
          if (count) count.textContent = shown.length;
        });

      if (empty) empty.hidden = cards.some((card) => !card.hidden);
      chips.forEach((chip) =>
        chip.setAttribute(
          "aria-pressed",
          String(selected.has(chip.dataset.filterTag)),
        ),
      );
      if (reset) reset.hidden = selected.size === 0;
      window.PiggyStorage?.writeSessionValue(storageKey, [...selected]);
    }

    chips.forEach((chip) => {
      chip.addEventListener("click", () => {
        const tag = chip.dataset.filterTag;
        if (!selected.delete(tag)) selected.add(tag);
        apply();
      });
    });

    more?.addEventListener("click", () => {
      const expanded = bar.classList.toggle("is-expanded");
      more.setAttribute("aria-expanded", String(expanded));
      more.textContent = expanded
        ? more.dataset.lessLabel
        : more.dataset.moreLabel;
    });

    reset?.addEventListener("click", () => {
      selected.clear();
      apply();
      chips[0]?.focus();
    });

    apply();
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeCardFilters);
} else {
  initializeCardFilters();
}
