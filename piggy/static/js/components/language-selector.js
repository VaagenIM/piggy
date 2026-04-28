function initializeLanguageSelectors() {
  const preferred = ["", "nno", "eng", "ukr"];
  const rank = new Map(preferred.map((code, index) => [code, index]));
  const fallbackRank = 1e9;

  document.querySelectorAll("[data-language-select]").forEach((select) => {
    const trigger = select.querySelector(".language-trigger");
    const dropdown = select.querySelector("[data-language-dropdown]");
    if (!trigger || !dropdown) return;
    const isDetails = select.tagName === "DETAILS";

    const links = Array.from(dropdown.children).filter(
      (child) => child.tagName === "A",
    );

    links.sort((a, b) => {
      const leftLang = a.dataset.lang ?? "";
      const rightLang = b.dataset.lang ?? "";
      const leftRank = rank.has(leftLang) ? rank.get(leftLang) : fallbackRank;
      const rightRank = rank.has(rightLang)
        ? rank.get(rightLang)
        : fallbackRank;

      if (leftRank !== rightRank) return leftRank - rightRank;

      return leftLang.localeCompare(rightLang);
    });

    links.forEach((link) => dropdown.appendChild(link));

    function close() {
      select.classList.remove("is-open");
      trigger.setAttribute("aria-expanded", "false");
      if (isDetails) {
        select.removeAttribute("open");
      }
    }

    function toggle() {
      if (isDetails) return;

      setOpen(!select.classList.contains("is-open"));
    }

    function setOpen(isOpen) {
      select.classList.toggle("is-open", isOpen);
      trigger.setAttribute("aria-expanded", String(isOpen));
    }

    function setLanguageCookie(lang) {
      if (lang) {
        document.cookie = `lang=${encodeURIComponent(lang)}; path=/; SameSite=Lax`;
      } else {
        document.cookie = "lang=; path=/; max-age=0; SameSite=Lax";
      }
    }

    function navigateToLanguageTarget(link) {
      const target = new URL(link.href, window.location.href).href;

      if (target === window.location.href) {
        window.location.reload();
      } else {
        window.location.assign(target);
      }
    }

    trigger.addEventListener("click", (event) => {
      if (isDetails) return;

      event.stopPropagation();
      toggle();
    });

    select.addEventListener("toggle", () => {
      if (isDetails) {
        setOpen(select.open);
      }
    });

    links.forEach((link) => {
      link.addEventListener("click", (event) => {
        if ("languageOption" in link.dataset) {
          event.preventDefault();
          setLanguageCookie(link.dataset.languageOption);
          navigateToLanguageTarget(link);
          return;
        }

        close();
      });
    });

    document.addEventListener("click", (event) => {
      if (!select.contains(event.target)) close();
    });

    select.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        close();
        trigger.focus();
      }
    });
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeLanguageSelectors);
} else {
  initializeLanguageSelectors();
}
