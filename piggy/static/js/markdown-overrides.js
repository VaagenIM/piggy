document.addEventListener(
  "click",
  (event) => {
    const summary = event.target.closest(".md-content details > summary");
    if (!summary) return;

    const details = summary.parentElement;
    if (!(details instanceof HTMLDetailsElement)) return;

    event.preventDefault();

    if (details.dataset.piggyAnimating === "true") return;

    if (details.open) {
      piggyCloseDetails(details, summary);
    } else {
      piggyOpenDetails(details, summary);
    }
  },
  true,
);

function piggyOpenDetails(details, summary) {
  if (piggyShouldReduceMotion()) {
    details.open = true;
    piggyScrollDetailsIntoView(details);
    return;
  }

  details.dataset.piggyAnimating = "true";
  details.classList.add("piggy-details-animating");

  const startHeight = summary.offsetHeight;

  details.style.height = `${startHeight}px`;
  details.open = true;

  const endHeight = details.scrollHeight;

  const animation = details.animate(
    [{ height: `${startHeight}px` }, { height: `${endHeight}px` }],
    {
      duration: 220,
      easing: "ease-out",
    },
  );

  animation.onfinish = () => {
    details.style.height = "";
    details.classList.remove("piggy-details-animating");
    delete details.dataset.piggyAnimating;

    piggyScrollDetailsIntoView(details);
  };

  animation.oncancel = () => {
    details.style.height = "";
    details.classList.remove("piggy-details-animating");
    delete details.dataset.piggyAnimating;
  };
}

function piggyCloseDetails(details, summary) {
  if (piggyShouldReduceMotion()) {
    details.open = false;
    return;
  }

  details.dataset.piggyAnimating = "true";
  details.classList.add("piggy-details-animating");

  const startHeight = details.scrollHeight;
  const endHeight = summary.offsetHeight;

  details.style.height = `${startHeight}px`;

  const animation = details.animate(
    [{ height: `${startHeight}px` }, { height: `${endHeight}px` }],
    {
      duration: 180,
      easing: "ease-in",
    },
  );

  animation.onfinish = () => {
    details.open = false;
    details.style.height = "";
    details.classList.remove("piggy-details-animating");
    delete details.dataset.piggyAnimating;
  };

  animation.oncancel = () => {
    details.style.height = "";
    details.classList.remove("piggy-details-animating");
    delete details.dataset.piggyAnimating;
  };
}

function piggyShouldReduceMotion() {
  const preference = document.documentElement.getAttribute(
    "data-reader-reduce-motion",
  );

  if (preference === "reduce") return true;
  if (preference === "allow") return false;

  return Boolean(
    window.matchMedia?.("(prefers-reduced-motion: reduce)").matches,
  );
}

function piggyScrollDetailsIntoView(details) {
  const rect = details.getBoundingClientRect();
  const viewportHeight = window.innerHeight;
  const bottomPadding = 32;

  if (rect.bottom > viewportHeight - bottomPadding) {
    window.scrollBy({
      top: rect.bottom - viewportHeight + bottomPadding,
      behavior: "smooth",
    });
  }
}

const PIGGY_CODE_LANGUAGE_LABELS = {
  bash: "Bash",
  c: "C",
  cpp: "C++",
  csharp: "C#",
  cs: "C#",
  css: "CSS",
  go: "Go",
  html: "HTML",
  java: "Java",
  javascript: "JavaScript",
  js: "JavaScript",
  json: "JSON",
  kotlin: "Kotlin",
  markdown: "Markdown",
  md: "Markdown",
  php: "PHP",
  py: "Python",
  python: "Python",
  rb: "Ruby",
  rs: "Rust",
  ruby: "Ruby",
  rust: "Rust",
  scss: "SCSS",
  sh: "Shell",
  shell: "Shell",
  sql: "SQL",
  swift: "Swift",
  ts: "TypeScript",
  typescript: "TypeScript",
  xml: "XML",
  yaml: "YAML",
  yml: "YAML",
};

const PIGGY_SVG_NAMESPACE = "http://www.w3.org/2000/svg";

document.addEventListener("DOMContentLoaded", () => {
  piggyInitializeCodeTitlebars();
  piggyObserveCodeTitlebars();
});

function piggyInitializeCodeTitlebars(root = document) {
  const highlights = [];

  if (root instanceof Element && root.matches(".md-content div.highlight")) {
    highlights.push(root);
  }

  if (typeof root.querySelectorAll === "function") {
    highlights.push(...root.querySelectorAll(".md-content div.highlight"));
  }

  highlights.forEach(piggyEnhanceCodeBlock);
}

function piggyObserveCodeTitlebars() {
  const markdownContent = document.querySelector(".md-content");
  if (!markdownContent) return;

  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        piggyInitializeCodeTitlebars(node);
      }
    }
  });

  observer.observe(markdownContent, {
    childList: true,
    subtree: true,
  });
}

function piggyEnhanceCodeBlock(highlight) {
  if (!(highlight instanceof HTMLElement)) return;
  if (!highlight.querySelector(":scope > pre, :scope > .highlighttable"))
    return;
  if (highlight.dataset.piggyCodeTitlebar === "true") return;
  if (!piggyShouldShowCodeLanguage(highlight)) return;

  const language = piggyGetCodeLanguage(highlight);
  if (!language) return;

  const title = piggyGetCodeTitle(highlight);
  const titlebar = piggyCreateCodeTitlebar(language, title);

  highlight.insertBefore(titlebar, highlight.firstElementChild);
  highlight.dataset.piggyCodeTitlebar = "true";
  highlight.classList.add("piggy-code-titlebar-ready");
}

function piggyGetCodeLanguage(highlight) {
  const languageClass = [...highlight.classList].find((className) =>
    className.startsWith("language-"),
  );
  const rawLanguage = languageClass
    ? languageClass.replace(/^language-/, "")
    : "";

  return piggyFormatCodeLanguage(rawLanguage);
}

function piggyShouldShowCodeLanguage(highlight) {
  const dataValue =
    highlight.dataset.showLanguage ?? highlight.dataset.piggyShowLanguage;

  if (typeof dataValue === "string") {
    return dataValue.toLowerCase() !== "false";
  }

  return (
    highlight.classList.contains("show-language") ||
    highlight.classList.contains("show-code-language")
  );
}

function piggyFormatCodeLanguage(rawLanguage) {
  const normalized = rawLanguage.trim().toLowerCase();
  if (!normalized || normalized === "text" || normalized === "plaintext") {
    return "";
  }

  if (PIGGY_CODE_LANGUAGE_LABELS[normalized]) {
    return PIGGY_CODE_LANGUAGE_LABELS[normalized];
  }

  return normalized
    .split(/[-_]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function piggyGetCodeTitle(highlight) {
  const tableFilename = highlight.querySelector(
    ".highlighttable th.filename .filename",
  );
  const directFilename = [...highlight.children].find((child) =>
    child.classList?.contains("filename"),
  );

  return (
    tableFilename?.textContent?.trim() ||
    directFilename?.textContent?.trim() ||
    ""
  );
}

function piggyCreateCodeTitlebar(language, title) {
  const titlebar = document.createElement("div");
  titlebar.className = "piggy-code-titlebar";

  if (language) {
    const languageGroup = document.createElement("span");
    languageGroup.className = "piggy-code-titlebar-language";

    const languageLabel = document.createElement("span");
    languageLabel.className = "piggy-code-titlebar-label";
    languageLabel.textContent = language;

    languageGroup.append(piggyCreateCodeLanguageIcon(), languageLabel);
    titlebar.append(languageGroup);
  }

  if (title) {
    if (language) {
      const separator = document.createElement("span");
      separator.className = "piggy-code-titlebar-separator";
      separator.setAttribute("aria-hidden", "true");
      separator.textContent = "/";

      titlebar.append(separator);
    }

    const titleLabel = document.createElement("span");
    titleLabel.className = "piggy-code-titlebar-title";
    titleLabel.textContent = title;

    titlebar.append(titleLabel);
  }
  return titlebar;
}

function piggyCreateCodeLanguageIcon() {
  const icon = document.createElementNS(PIGGY_SVG_NAMESPACE, "svg");
  icon.classList.add("piggy-code-titlebar-icon");
  icon.setAttribute("aria-hidden", "true");
  icon.setAttribute("viewBox", "0 0 24 24");
  icon.setAttribute("fill", "none");
  icon.setAttribute("stroke", "currentColor");
  icon.setAttribute("stroke-linecap", "round");
  icon.setAttribute("stroke-linejoin", "round");

  ["m18 16 4-4-4-4", "m6 8-4 4 4 4", "m14.5 4-5 16"].forEach((pathData) => {
    const path = document.createElementNS(PIGGY_SVG_NAMESPACE, "path");
    path.setAttribute("d", pathData);
    icon.append(path);
  });

  return icon;
}
