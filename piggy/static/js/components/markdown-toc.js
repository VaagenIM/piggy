(function () {
  // Keep in sync with the `min-width` used for the desktop layout in
  // css/markdown/markdown-toc.css.
  const DESKTOP_MEDIA_QUERY = "(min-width: 1220px)";
  const FOLDED_KEY = "piggy:toc-folded";

  function headingFor(link) {
    const hash = link.getAttribute("href") || "";
    if (!hash.startsWith("#") || hash.length < 2) return null;
    return document.getElementById(decodeURIComponent(hash.slice(1)));
  }

  // A heading in an inactive content tab or a closed <details> has no box, so
  // an anchor jump to it does nothing: open what hides it first
  function revealHeading(heading) {
    for (let node = heading.parentElement; node; node = node.parentElement) {
      if (node.tagName === "DETAILS") node.open = true;
      if (node.classList.contains("tabbed-block")) {
        const index = Array.from(node.parentElement.children).indexOf(node);
        const input = node
          .closest(".tabbed-set")
          ?.querySelectorAll(":scope > input")[index];
        if (input && !input.checked) input.click();
      }
    }
  }

  function isHidden(element) {
    return element.getClientRects().length === 0;
  }

  // Only the open tab's headings are listed: the others aren't on the page
  function syncTabbedEntries(panel) {
    panel.querySelectorAll("[data-toc-link]").forEach((link) => {
      const heading = headingFor(link);
      const item = link.closest(".toc-sidebar__item");
      if (heading && item) {
        item.hidden =
          Boolean(heading.closest(".tabbed-block")) && isHidden(heading);
      }
    });
  }

  function revealLocationHash() {
    const id = decodeURIComponent(window.location.hash.slice(1));
    const heading = id ? document.getElementById(id) : null;
    if (heading && isHidden(heading)) {
      revealHeading(heading);
      heading.scrollIntoView();
    }
  }

  // Small screens: the bar sticks below the header (sticky from 800px up),
  // and tucks away while scrolling down, like a browser's address bar
  function initStickyBar(sidebar, isOpen) {
    const desktop = window.matchMedia(DESKTOP_MEDIA_QUERY);
    const header = document.querySelector(".site-header");
    let lastY = window.scrollY;

    function placeBar() {
      const sticky = header && getComputedStyle(header).position === "sticky";
      const below = sticky ? header.getBoundingClientRect().height : 0;
      sidebar.style.setProperty("--piggy-toc-bar-top", `${below + 8}px`);
    }

    function onScroll() {
      const y = window.scrollY;
      if (Math.abs(y - lastY) < 6) return;
      const down = y > lastY;
      lastY = y;

      const top = parseFloat(
        sidebar.style.getPropertyValue("--piggy-toc-bar-top"),
      );
      const stuck = sidebar.getBoundingClientRect().top <= top + 1;
      sidebar.classList.toggle(
        "is-tucked",
        down && stuck && !isOpen() && !desktop.matches,
      );
    }

    placeBar();
    window.addEventListener("resize", placeBar, { passive: true });
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  function initFold(sidebar) {
    const fold = sidebar.querySelector("[data-toc-fold]");
    if (!fold) return;

    function setFolded(folded) {
      sidebar.toggleAttribute("data-toc-folded", folded);
      fold.setAttribute("aria-expanded", String(!folded));
      fold.title = folded
        ? "Vis innholdsfortegnelsen"
        : "Skjul innholdsfortegnelsen";
    }

    setFolded(
      window.PiggyStorage?.readJson("localStorage", FOLDED_KEY, false) === true,
    );
    fold.addEventListener("click", () => {
      const folded = !sidebar.hasAttribute("data-toc-folded");
      setFolded(folded);
      window.PiggyStorage?.writeJson("localStorage", FOLDED_KEY, folded);
    });
  }

  function initToc(sidebar) {
    const toggle = sidebar.querySelector("[data-toc-toggle]");
    const panel = sidebar.querySelector("[data-toc-panel]");

    if (!toggle || !panel) return;

    function isOpen() {
      return !panel.hidden;
    }

    function openPanel() {
      panel.hidden = false;
      toggle.setAttribute("aria-expanded", "true");
      sidebar.classList.remove("is-tucked");
    }

    function closePanel() {
      panel.hidden = true;
      toggle.setAttribute("aria-expanded", "false");
    }

    toggle.addEventListener("click", () => {
      if (isOpen()) {
        closePanel();
      } else {
        openPanel();
      }
    });

    // The list folds out over the text, so a tap beside it closes it
    document.addEventListener("click", (event) => {
      if (isOpen() && !sidebar.contains(event.target)) closePanel();
    });

    panel.addEventListener("click", (event) => {
      const link = event.target.closest("[data-toc-link]");
      if (!link) return;

      const heading = headingFor(link);
      if (heading && isHidden(heading)) {
        event.preventDefault();
        revealHeading(heading);
        window.history.pushState(null, "", link.getAttribute("href"));
        heading.scrollIntoView();
      }
      closePanel();
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

    initFold(sidebar);
    initStickyBar(sidebar, isOpen);
    initScrollSpy(panel);

    // Linked tabs switch other tab sets too, so sync after any tab change
    const sync = () => requestAnimationFrame(() => syncTabbedEntries(panel));
    document.addEventListener("change", (event) => {
      if (event.target.closest(".tabbed-set")) sync();
    });
    document.addEventListener("click", (event) => {
      if (event.target.closest(".tabbed-labels")) sync();
    });
    syncTabbedEntries(panel);
  }

  function initScrollSpy(panel) {
    const links = Array.from(panel.querySelectorAll("[data-toc-link]"));
    const targets = links
      .map((link) => {
        const heading = headingFor(link);
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
    // Links to a heading in a hidden tab (from the TOC, or shared) work too
    revealLocationHash();
    window.addEventListener("hashchange", revealLocationHash);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }
})();
