document.addEventListener("DOMContentLoaded", () => {
  const preferred = ["", "nno", "eng", "ukr"];
  const rank = new Map(preferred.map((code, index) => [code, index]));
  const fallbackRank = 1e9;

  document.querySelectorAll("[data-language-dropdown]").forEach((dropdown) => {
    const links = Array.from(dropdown.querySelectorAll(":scope > a"));

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
  });
});
