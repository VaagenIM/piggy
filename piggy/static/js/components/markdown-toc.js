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
    if (!("IntersectionObserver" in window)) return;

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
      links.forEach((link) => {
        link.classList.toggle("is-active", link === activeLink);
      });
    }

    // Anchor-jumps land a heading at its `scroll-margin-top` (the sticky
    // header clearance), so the observer's activation band has to start at
    // or above that same offset - otherwise a just-clicked link never
    // registers as active because its heading landed above the band.
    const headingOffset =
      parseFloat(getComputedStyle(targets[0].heading).scrollMarginTop) || 0;
    const topMargin = Math.max(headingOffset - 4, 0);

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const target = targets.find((t) => t.heading === entry.target);
          if (target) setActive(target.link);
        });
      },
      { rootMargin: `-${topMargin}px 0px -70% 0px`, threshold: 0 },
    );

    targets.forEach((target) => observer.observe(target.heading));
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
