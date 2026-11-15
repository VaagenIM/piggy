(() => {
  const menu = document.querySelector("[data-book-navigation]");
  if (!menu) return;

  const links = [...menu.querySelectorAll("[data-book-entry]")];
  const local = links.filter((link) => link.hasAttribute("data-book-local"));
  const label = menu.querySelector("[data-book-current-label]");
  const header = document.querySelector(".site-header");
  const targets = local
    .map((link) => ({
      link,
      target: document.getElementById(link.dataset.bookAnchor),
    }))
    .filter(({ target }) => target);
  let current = null;
  let frame = null;

  function select(link) {
    if (!link || link === current) return;
    current = link;
    links.forEach((entry) => entry.removeAttribute("aria-current"));
    link.setAttribute("aria-current", "location");
    label.textContent = link.textContent;
    const index = links.indexOf(link);
    [
      ["previous", links[index - 1]],
      ["next", links[index + 1]],
    ].forEach(([direction, entry]) => {
      document
        .querySelectorAll(`[data-book-${direction}]`)
        .forEach((control) => {
          control.hidden = !entry;
          if (entry) {
            control.href = entry.href;
            control.querySelector(
              `[data-book-${direction}-label]`,
            ).textContent = entry.textContent;
          } else {
            control.removeAttribute("href");
          }
        });
    });
  }

  function headerOffset() {
    return header && getComputedStyle(header).position === "sticky"
      ? header.getBoundingClientRect().height + 20
      : 20;
  }

  function resize() {
    document.documentElement.style.setProperty(
      "--book-scroll-offset",
      `${headerOffset()}px`,
    );
    scheduleScroll();
  }

  function fromScroll() {
    frame = null;
    let active = local[0];
    for (const { link, target } of targets) {
      if (target.getBoundingClientRect().top <= headerOffset() + 4)
        active = link;
    }
    select(active);
  }

  function scheduleScroll() {
    if (frame === null) frame = requestAnimationFrame(fromScroll);
  }

  function fromHash() {
    let hash;
    try {
      hash = decodeURIComponent(location.hash.slice(1));
    } catch {
      hash = "";
    }
    const link = local.find((entry) => entry.dataset.bookAnchor === hash);
    if (link) select(link);
    else scheduleScroll();
  }

  targets.forEach(({ target }) => target.setAttribute("tabindex", "-1"));
  menu.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && menu.open) {
      menu.open = false;
      menu.querySelector("summary").focus();
    }
  });
  document.addEventListener("click", (event) => {
    const link = event.target.closest("a[href]");
    if (
      !link ||
      event.button !== 0 ||
      event.metaKey ||
      event.ctrlKey ||
      event.shiftKey ||
      event.altKey
    )
      return;
    if (menu.contains(link)) menu.open = false;
    const url = new URL(link.href, location.href);
    if (
      url.pathname.replace(/\/$/, "") !==
        location.pathname.replace(/\/$/, "") ||
      !url.hash
    )
      return;
    let id;
    try {
      id = decodeURIComponent(url.hash.slice(1));
    } catch {
      return;
    }
    const target = targets.find((item) => item.target.id === id)?.target;
    if (target) {
      // Preserve native fragment navigation/history; focus only after an explicit
      // navigation action, never during passive scrolling or restoration.
      requestAnimationFrame(() => target.focus({ preventScroll: true }));
    }
  });
  window.addEventListener("hashchange", fromHash);
  window.addEventListener("scroll", scheduleScroll, { passive: true });
  window.addEventListener("resize", resize);
  window.addEventListener("pageshow", () => {
    // The browser may restore a scroll position after DOMContentLoaded, even
    // while retaining an earlier hash. Read the restored viewport last.
    requestAnimationFrame(() => requestAnimationFrame(fromScroll));
  });
  window.addEventListener("load", scheduleScroll);
  if (window.ResizeObserver && header)
    new ResizeObserver(resize).observe(header);
  resize();
  fromHash();
})();
