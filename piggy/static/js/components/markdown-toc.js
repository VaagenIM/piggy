(function () {
  // Keep in sync with the `min-width` used for the desktop layout in
  // css/markdown/markdown-toc.css.
  const DESKTOP_MEDIA_QUERY = "(min-width: 1220px)";

  function initToc(sidebar) {
    const toggle = sidebar.querySelector("[data-toc-toggle]");
    const panel = sidebar.querySelector("[data-toc-panel]");
    const backdrop = sidebar.querySelector("[data-toc-backdrop]");

    if (!toggle || !panel) return;

    function isOpen() {
      return !panel.hidden;
    }

    function openPanel() {
      panel.hidden = false;
      if (backdrop) backdrop.hidden = false;
      toggle.setAttribute("aria-expanded", "true");
      document.documentElement.classList.add("toc-scroll-lock");
    }

    function closePanel() {
      panel.hidden = true;
      if (backdrop) backdrop.hidden = true;
      toggle.setAttribute("aria-expanded", "false");
      document.documentElement.classList.remove("toc-scroll-lock");
    }

    toggle.addEventListener("click", () => {
      if (isOpen()) {
        closePanel();
      } else {
        openPanel();
      }
    });

    if (backdrop) {
      backdrop.addEventListener("click", closePanel);
    }

    panel.addEventListener("click", (event) => {
      if (event.target.closest("[data-toc-link]")) {
        closePanel();
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && isOpen()) {
        closePanel();
        toggle.focus();
      }
    });

    if (typeof window.matchMedia === "function") {
      const desktopQuery = window.matchMedia(DESKTOP_MEDIA_QUERY);
      const handleBreakpointChange = (event) => {
        if (event.matches) closePanel();
      };

      if (typeof desktopQuery.addEventListener === "function") {
        desktopQuery.addEventListener("change", handleBreakpointChange);
      } else if (typeof desktopQuery.addListener === "function") {
        desktopQuery.addListener(handleBreakpointChange);
      }
    }

    initScrollSpy(panel);
  }

  function initScrollSpy(panel) {
    const links = Array.from(panel.querySelectorAll("[data-toc-link]"));
    const targets = links
      .map((link) => {
        const hash = link.getAttribute("href") || "";
        if (!hash.startsWith("#") || hash.length < 2) return null;

        const heading = document.getElementById(
          decodeURIComponent(hash.slice(1)),
        );
        return heading ? { link, heading } : null;
      })
      .filter(Boolean);

    if (targets.length === 0) return;

    function setActive(activeLink) {
      if (activeLink.classList.contains("is-active")) return;
      links.forEach((link) => {
        link.classList.toggle("is-active", link === activeLink);
      });
      revealInPanel(activeLink);
    }

    // Keep the active entry in view in a long (scrolling) panel, without
    // scrolling the page itself like scrollIntoView() could
    function revealInPanel(link) {
      const panelRect = panel.getBoundingClientRect();
      const linkRect = link.getBoundingClientRect();
      if (linkRect.top < panelRect.top) {
        panel.scrollTop -= panelRect.top - linkRect.top;
      } else if (linkRect.bottom > panelRect.bottom) {
        panel.scrollTop += linkRect.bottom - panelRect.bottom;
      }
    }

    // The current section is the last heading scrolled up to its
    // `scroll-margin-top` (the sticky header clearance), which is also where
    // an anchor jump lands it. Watching heading visibility instead marks
    // whichever heading entered view last, often the one after a clicked link.
    let scheduled = false;

    function updateActive() {
      scheduled = false;
      // Headings in collapsed blocks have no box (and would read as top 0)
      const shown = targets.filter(
        (target) => target.heading.getClientRects().length > 0,
      );
      if (shown.length === 0) return;

      // The last sections can be too short to ever reach the top, so the
      // end of the page belongs to the last heading
      const scrolledToEnd =
        window.innerHeight + window.scrollY >=
        document.documentElement.scrollHeight - 2;

      let current = shown[0];
      for (const target of shown) {
        const offset =
          parseFloat(getComputedStyle(target.heading).scrollMarginTop) || 0;
        if (target.heading.getBoundingClientRect().top > offset + 1) break;
        current = target;
      }
      setActive((scrolledToEnd ? shown.at(-1) : current).link);
    }

    function scheduleUpdate() {
      if (scheduled) return;
      scheduled = true;
      requestAnimationFrame(updateActive);
    }

    window.addEventListener("scroll", scheduleUpdate, { passive: true });
    window.addEventListener("resize", scheduleUpdate, { passive: true });
    updateActive();
  }

  function initAll() {
    document
      .querySelectorAll("[data-toc-sidebar]")
      .forEach((sidebar) => initToc(sidebar));
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }
})();
