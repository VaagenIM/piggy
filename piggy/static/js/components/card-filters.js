function initializeCardFilters() {
  document.querySelectorAll("[data-card-filters]").forEach((bar) => {
    const scope = bar.closest("[data-card-filter-scope]") || document.body;
    const cards = Array.from(scope.querySelectorAll(".piggy-card[data-tags]"));
    const options = Array.from(bar.querySelectorAll("[data-filter-tag]"));
    const toggle = bar.querySelector("[data-card-filters-toggle]");
    const panel = bar.querySelector("[data-card-filters-panel]");
    const search = bar.querySelector("[data-card-filters-search]");
    const none = bar.querySelector("[data-card-filters-none]");
    const group = bar.querySelector("[data-card-filters-group]");
    const active = bar.querySelector("[data-card-filters-active]");
    const badge = bar.querySelector("[data-card-filters-badge]");
    const reset = bar.querySelector("[data-card-filters-reset]");
    const empty = scope.querySelector("[data-card-filters-empty]");
    const labels = new Map(
      options.map((option) => [
        option.dataset.filterTag,
        option.dataset.filterLabel,
      ]),
    );
    const hiddenTags = new Set(
      options
        .filter((option) => option.hasAttribute("data-hidden-tag"))
        .map((option) => option.dataset.filterTag),
    );

    // Kept for the tab session, so going back to the page keeps the filters
    const storageKey = `piggy:card-filters:${window.location.pathname}`;
    const stored = window.PiggyStorage?.readSessionValue(storageKey);
    const selected = new Set(
      (Array.isArray(stored) ? stored : []).filter((tag) => labels.has(tag)),
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

    function renderActive() {
      active.replaceChildren(
        ...[...selected].map((tag) => {
          const chip = document.createElement("button");
          chip.type = "button";
          chip.className = "card-filters-chip";
          chip.textContent = labels.get(tag);
          chip.title = "Fjern filteret";
          chip.setAttribute("aria-label", `Fjern ${labels.get(tag)}`);
          chip.addEventListener("click", () => {
            selected.delete(tag);
            apply();
          });
          return chip;
        }),
      );
      badge.textContent = selected.size;
      badge.hidden = selected.size === 0;
      reset.hidden = selected.size === 0;
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
      options.forEach((option) =>
        option.setAttribute(
          "aria-pressed",
          String(selected.has(option.dataset.filterTag)),
        ),
      );
      renderActive();
      window.PiggyStorage?.writeSessionValue(storageKey, [...selected]);
    }

    function filterOptions() {
      const query = search.value.trim().toLowerCase();
      let shown = 0;
      let shownHidden = 0;
      options.forEach((option) => {
        const match = option.dataset.filterLabel.toLowerCase().includes(query);
        option.hidden = !match;
        if (match) {
          shown += 1;
          if (option.hasAttribute("data-hidden-tag")) shownHidden += 1;
        }
      });
      if (group) group.hidden = shownHidden === 0;
      none.hidden = shown > 0;
    }

    function isOpen() {
      return !panel.hidden;
    }

    function open() {
      panel.hidden = false;
      toggle.setAttribute("aria-expanded", "true");
      search.focus();
    }

    function close({ focusToggle = false } = {}) {
      if (!isOpen()) return;
      panel.hidden = true;
      toggle.setAttribute("aria-expanded", "false");
      search.value = "";
      filterOptions();
      if (focusToggle) toggle.focus();
    }

    toggle.addEventListener("click", () => (isOpen() ? close() : open()));

    options.forEach((option) => {
      option.addEventListener("click", () => {
        const tag = option.dataset.filterTag;
        if (!selected.delete(tag)) selected.add(tag);
        apply();
      });
    });

    search.addEventListener("input", filterOptions);
    // Enter picks the first tag that matches the search
    search.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      options.find((option) => !option.hidden)?.click();
    });

    document.addEventListener("click", (event) => {
      if (isOpen() && !bar.contains(event.target)) close();
    });
    bar.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && isOpen()) {
        event.stopPropagation();
        close({ focusToggle: true });
      }
    });

    reset.addEventListener("click", () => {
      selected.clear();
      apply();
      toggle.focus();
    });

    apply();
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeCardFilters);
} else {
  initializeCardFilters();
}
