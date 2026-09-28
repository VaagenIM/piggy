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
  piggyScheduleLineNumberSync();
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
    let sawAddedNodes = false;

    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        piggyInitializeCodeTitlebars(node);
        sawAddedNodes = true;
      }
    }

    if (sawAddedNodes) piggyScheduleLineNumberSync();
  });

  observer.observe(markdownContent, {
    childList: true,
    subtree: true,
  });
}

/****************************************\
|* LINE NUMBER / WRAPPED-LINE SYNCING   *|
\****************************************/
let piggyLineNumberSyncScheduled = false;

function piggyScheduleLineNumberSync() {
  if (piggyLineNumberSyncScheduled) return;
  piggyLineNumberSyncScheduled = true;

  requestAnimationFrame(() => {
    piggyLineNumberSyncScheduled = false;
    piggySyncAllLineNumberWrapping();
  });
}

window.addEventListener("resize", piggyScheduleLineNumberSync, {
  passive: true,
});
window.addEventListener("orientationchange", piggyScheduleLineNumberSync, {
  passive: true,
});

if (window.visualViewport) {
  window.visualViewport.addEventListener(
    "resize",
    piggyScheduleLineNumberSync,
    {
      passive: true,
    },
  );
}

if (document.fonts) {
  document.fonts.ready.then(piggyScheduleLineNumberSync);
}

document.addEventListener(
  "piggy:preferenceschange",
  piggyScheduleLineNumberSync,
);

function piggyObserveMarkdownContentResize() {
  const markdownContent = document.querySelector(".md-content");
  if (!markdownContent || typeof ResizeObserver === "undefined") return;

  const observer = new ResizeObserver(() => {
    piggyScheduleLineNumberSync();
  });
  observer.observe(markdownContent);
}

document.addEventListener(
  "DOMContentLoaded",
  piggyObserveMarkdownContentResize,
);

function piggyIsCodeWrapEnabled() {
  return (
    document.documentElement.getAttribute("data-reader-code-wrap") !== "off"
  );
}

function piggySyncAllLineNumberWrapping(root = document) {
  const tables = [];

  if (root instanceof Element && root.matches(".md-content .highlighttable")) {
    tables.push(root);
  }

  if (typeof root.querySelectorAll === "function") {
    tables.push(...root.querySelectorAll(".md-content .highlighttable"));
  }

  tables.forEach(piggySyncLineNumberWrapping);
}

function piggySyncLineNumberWrapping(highlighttable) {
  const normals = [
    ...highlighttable.querySelectorAll(".linenodiv pre .normal"),
  ];
  if (!normals.length) return;

  if (!piggyIsCodeWrapEnabled()) {
    normals.forEach((normal) => {
      normal.style.marginBottom = "";
    });
    return;
  }

  const codeElement = highlighttable.querySelector("td.code pre > code");
  if (!codeElement) return;

  const codeRect = codeElement.getBoundingClientRect();
  if (codeRect.width === 0 && codeRect.height === 0) return;

  const lineSpans = [...codeElement.querySelectorAll(":scope > span[id]")];
  if (lineSpans.length !== normals.length) return;

  const lineHeight = parseFloat(getComputedStyle(codeElement).lineHeight);
  if (!lineHeight) return;

  lineSpans.forEach((lineSpan, index) => {
    const normal = normals[index];
    if (!normal) return;

    const wrappedRows = Math.max(
      1,
      Math.round(lineSpan.getBoundingClientRect().height / lineHeight),
    );
    const extraHeight = (wrappedRows - 1) * lineHeight;

    normal.style.marginBottom = extraHeight > 0.5 ? `${extraHeight}px` : "";
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

/****************************************\
|* PYODIDE EDITORS                      *|
\****************************************/
document.addEventListener("DOMContentLoaded", piggyInitializePyodideEditors);
document.addEventListener(
  "piggy:preferenceschange",
  piggySyncPyodideEditorWrapping,
);

function piggyGetPyodideEditors() {
  return [...document.querySelectorAll(".md-content .pyodide-editor")]
    .map((element) => element.env?.editor)
    .filter(Boolean);
}

function piggyInitializePyodideEditors() {
  piggyGetPyodideEditors().forEach((editor) => {
    editor.setOption("maxLines", Infinity);
    piggyHighlightPyodideSelection(editor);
    piggyFocusPyodideEditorFromPadding(editor);
  });

  piggySyncPyodideEditorWrapping();
  document.querySelectorAll(".md-content .pyodide").forEach((pyodide) => {
    piggyAddPyodideCopyButtons(pyodide);
    piggyAddPyodideHelp(pyodide);
  });
  piggyUsePyodideRunner();
}

// markdown-exec prints Pyodide's whole PythonError, trim it
const PIGGY_PYODIDE_RUNNER = `
import sys
import traceback
from pyodide.code import eval_code_async

async def run(code, namespace):
    try:
        return await eval_code_async(code, namespace, filename="main.py")
    except SystemExit as exc:
        # Like CPython: exit codes are silent, exit("message") is printed
        if exc.code is not None and not isinstance(exc.code, int):
            print(exc.code, file=sys.stderr)
    except BaseException as exc:
        tb = exc.__traceback__
        while tb and tb.tb_frame.f_code.co_filename != "main.py":
            tb = tb.tb_next
        print("".join(traceback.format_exception(type(exc), exc, tb)), end="", file=sys.stderr)

run
`;
let piggyPyodideRunner = null;

function piggyUsePyodideRunner() {
  // Run / Ctrl+Enter call markdown-exec's global evaluatePython() on click
  if (typeof window.evaluatePython !== "function") return;

  window.evaluatePython = async (pyodide, editor, output, session) => {
    pyodide.setStdout({
      batched: (text) => piggyWritePyodideOutput(output, text),
    });
    pyodide.setStderr({
      batched: (text) => piggyWritePyodideOutput(output, text, true),
    });
    output.replaceChildren();

    try {
      piggyPyodideRunner ??= pyodide.runPython(PIGGY_PYODIDE_RUNNER, {
        globals: pyodide.globals.get("dict")(),
      });
      const result = await piggyPyodideRunner(
        editor.getValue(),
        window.getSession(session, pyodide), // markdown-exec's shared namespaces
      );

      // Like markdown-exec: show the value of a trailing expression
      if (result) piggyWritePyodideOutput(output, String(result));
      result?.destroy?.();
    } catch (error) {
      piggyWritePyodideOutput(output, String(error), true);
    }
  };
}

function piggyWritePyodideOutput(output, text, isError = false) {
  if (!isError) {
    output.append(`${text}\n`);
    return;
  }

  const error = document.createElement("span");
  error.className = "pyodide-output__error";
  error.textContent = `${text}\n`;
  output.append(error);
}

// The editor area has padding around Ace, so let clicks there focus the editor
// like a text field: above the code goes to the start, below it to the end.
function piggyFocusPyodideEditorFromPadding(editor) {
  const editorArea = editor.container.parentElement;

  editorArea.addEventListener("mousedown", (event) => {
    if (event.target !== editorArea) return;

    event.preventDefault();
    editor.focus();

    if (event.offsetY < editorArea.clientHeight / 2) {
      editor.navigateFileStart();
    } else {
      editor.navigateFileEnd();
    }
  });
}

function piggyAddPyodideCopyButtons(pyodide) {
  const [editorBar, outputBar] = pyodide.querySelectorAll(
    ":scope > .pyodide-editor-bar",
  );
  const editorElement = pyodide.querySelector(".pyodide-editor");
  const output = pyodide.querySelector(".pyodide-output");
  if (!editorBar || !outputBar || !editorElement || !output) return;

  const copyCode = piggyCreatePyodideCopyButton();
  copyCode.addEventListener("click", () => {
    const code = editorElement.env?.editor?.getValue();

    if (code) {
      copyCode.dataset.clipboardText = code;
    } else {
      delete copyCode.dataset.clipboardText;
    }
  });
  editorBar.append(copyCode);

  const copyOutput = piggyCreatePyodideCopyButton();
  copyOutput.classList.add("pyodide-copy-output");
  copyOutput.dataset.clipboardTarget = `#${CSS.escape(output.id)}`;
  outputBar.append(copyOutput);
}

function piggyCreatePyodideCopyButton() {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "md-code__button";
  button.title = "Copy to clipboard";
  button.dataset.mdType = "copy";

  return button;
}

/* Help popup behind the ⓘ button in the editor bar */
const PIGGY_IS_MAC = /Mac|iPhone|iPad/.test(
  navigator.userAgentData?.platform || navigator.platform || "",
);
const PIGGY_MOD_KEY = PIGGY_IS_MAC ? "⌘" : "Ctrl";
const PIGGY_ALT_KEY = PIGGY_IS_MAC ? "⌥" : "Alt";

const PIGGY_PYODIDE_HELP = {
  title: "Slik bruker du editoren",
  items: [
    [
      "edit",
      "Rediger",
      "Klikk i koden og endre den som du vil. Endringene lagres ikke hvis du laster inn siden på nytt.",
    ],
    [
      "run",
      "Kjør",
      "Trykk Run for å kjøre koden, og se resultatet under Output. Python lastes inn når siden åpnes, så det kan ta noen sekunder før Run virker.",
    ],
    ["copy", "Kopier", "Kopier-knappene kopierer koden eller resultatet."],
  ],
  shortcutsTitle: "Hurtigtaster",
  // Run is markdown-exec's own Ctrl+Enter handler, which is Ctrl on Mac too
  shortcuts: [
    [[["Ctrl", "Enter"]], "Kjør koden"],
    [[["Tab"], ["Shift", "Tab"]], "Rykk inn / rykk ut"],
    [
      [
        [PIGGY_MOD_KEY, "Z"],
        [PIGGY_MOD_KEY, "Y"],
      ],
      "Angre / gjør om",
    ],
    [
      [
        [PIGGY_ALT_KEY, "↑"],
        [PIGGY_ALT_KEY, "↓"],
      ],
      "Flytt linjen opp / ned",
    ],
  ],
};

function piggyAddPyodideHelp(pyodide) {
  const editorBar = pyodide.querySelector(":scope > .pyodide-editor-bar");
  const label = editorBar?.querySelector(
    ".pyodide-bar-item:not(.pyodide-clickable)",
  );
  if (!label || !HTMLElement.prototype.hasOwnProperty("popover")) return;

  const help = piggyCreatePyodideHelp();
  const button = document.createElement("button");
  button.type = "button";
  button.className = "pyodide-help-button";
  button.title = PIGGY_PYODIDE_HELP.title;
  button.setAttribute("aria-label", PIGGY_PYODIDE_HELP.title);
  button.popoverTargetElement = help;

  label.after(button);
  pyodide.append(help);

  // The popup lives in the top layer, so place it under the button ourselves
  const position = () => piggyPositionPyodideHelp(help, button);
  help.addEventListener("toggle", (event) => {
    const open = event.newState === "open";
    const method = open ? "addEventListener" : "removeEventListener";

    if (open) position();
    window[method]("scroll", position, { capture: true, passive: true });
    window[method]("resize", position, { passive: true });
  });
}

function piggyCreatePyodideHelp() {
  const help = document.createElement("aside");
  help.className = "pyodide-help";
  help.popover = "auto";
  help.setAttribute("role", "dialog");
  help.setAttribute("aria-label", PIGGY_PYODIDE_HELP.title);

  const header = document.createElement("div");
  header.className = "pyodide-help__header";

  const title = document.createElement("strong");
  title.className = "pyodide-help__title";
  title.textContent = PIGGY_PYODIDE_HELP.title;

  const close = document.createElement("button");
  close.type = "button";
  close.className = "pyodide-help__close";
  close.setAttribute("aria-label", "Lukk");
  close.popoverTargetElement = help;
  close.popoverTargetAction = "hide";

  header.append(title, close);
  help.append(header);

  PIGGY_PYODIDE_HELP.items.forEach(([icon, name, text]) => {
    const item = document.createElement("div");
    item.className = `pyodide-help__item pyodide-help__item--${icon}`;

    const itemName = document.createElement("strong");
    itemName.textContent = `${name}:`;

    const itemText = document.createElement("span");
    itemText.append(itemName, ` ${text}`);

    item.append(itemText);
    help.append(item);
  });

  const shortcutsTitle = document.createElement("strong");
  shortcutsTitle.className = "pyodide-help__subtitle";
  shortcutsTitle.textContent = PIGGY_PYODIDE_HELP.shortcutsTitle;

  const shortcuts = document.createElement("div");
  shortcuts.className = "pyodide-help__shortcuts";

  PIGGY_PYODIDE_HELP.shortcuts.forEach(([combos, description]) => {
    const keys = document.createElement("span");
    keys.className = "pyodide-help__keys";

    combos.forEach((combo, index) => {
      if (index > 0) keys.append(" / ");
      keys.append(piggyCreateKeyCombo(combo));
    });

    const text = document.createElement("span");
    text.textContent = description;

    shortcuts.append(keys, text);
  });

  help.append(shortcutsTitle, shortcuts);
  return help;
}

// Same markup as pymdownx.keys (++ctrl+enter++), so markdown-keys.css styles it
function piggyCreateKeyCombo(combo) {
  const keys = document.createElement("span");
  keys.className = "keys";

  combo.forEach((key, index) => {
    if (index > 0) {
      const separator = document.createElement("span");
      separator.textContent = "+";
      keys.append(separator);
    }

    const kbd = document.createElement("kbd");
    kbd.textContent = key;
    keys.append(kbd);
  });

  return keys;
}

function piggyPositionPyodideHelp(help, button) {
  const gap = 6;
  const margin = 8;
  const anchor = button.getBoundingClientRect();
  const left = Math.max(
    margin,
    Math.min(anchor.left, window.innerWidth - help.offsetWidth - margin),
  );
  const fitsBelow =
    anchor.bottom + gap + help.offsetHeight <= window.innerHeight - margin;
  const fitsAbove = anchor.top - gap - help.offsetHeight >= margin;
  const preferredTop =
    fitsBelow || !fitsAbove
      ? anchor.bottom + gap
      : anchor.top - gap - help.offsetHeight;
  // If it fits neither below nor above, keep it on screen anyway
  const top = Math.max(
    margin,
    Math.min(preferredTop, window.innerHeight - help.offsetHeight - margin),
  );

  help.style.left = `${left}px`;
  help.style.top = `${top}px`;
}

const PIGGY_CODE_SELECTION_HIGHLIGHT =
  window.CSS?.highlights && typeof Highlight === "function"
    ? new Highlight()
    : null;
const piggyPyodideSelectionRanges = new WeakMap();

if (PIGGY_CODE_SELECTION_HIGHLIGHT) {
  CSS.highlights.set("piggy-code-selection", PIGGY_CODE_SELECTION_HIGHLIGHT);
}

function piggyHighlightPyodideSelection(editor) {
  const lineCells = editor.renderer.$textLayer?.$lines?.cells;
  if (!PIGGY_CODE_SELECTION_HIGHLIGHT || !lineCells) return;

  editor.container.classList.add("piggy-code-selection-highlight");
  editor.renderer.on("afterRender", () => {
    const previousRanges = piggyPyodideSelectionRanges.get(editor) || [];
    previousRanges.forEach((range) =>
      PIGGY_CODE_SELECTION_HIGHLIGHT.delete(range),
    );

    const ranges = editor.selection
      .getAllRanges()
      .flatMap((range) => piggyGetAceSelectionTextRanges(editor, range));
    ranges.forEach((range) => PIGGY_CODE_SELECTION_HIGHLIGHT.add(range));
    piggyPyodideSelectionRanges.set(editor, ranges);
  });
}

function piggyGetAceSelectionTextRanges(editor, selectionRange) {
  if (selectionRange.isEmpty()) return [];

  const session = editor.session;
  const { start, end } = selectionRange;
  const textRanges = [];

  editor.renderer.$textLayer.$lines.cells.forEach(({ row, element }) => {
    if (row < start.row || row > end.row) return;

    const screenLines = element.classList.contains("ace_line_group")
      ? [...element.children]
      : [element];
    const firstScreenRow = session.documentToScreenRow(row, 0);
    const from = session.documentToScreenPosition(
      row,
      row === start.row ? start.column : 0,
    );
    const to = session.documentToScreenPosition(
      row,
      row === end.row ? end.column : Infinity,
    );

    for (let screenRow = from.row; screenRow <= to.row; screenRow++) {
      const textRange = piggyCreateColumnTextRange(
        screenLines[screenRow - firstScreenRow],
        screenRow === from.row
          ? from.column
          : session.getRowWrapIndent(screenRow),
        screenRow === to.row ? to.column : Infinity,
      );
      if (textRange) textRanges.push(textRange);
    }
  });

  return textRanges;
}

function piggyCreateColumnTextRange(lineElement, startColumn, endColumn) {
  if (!lineElement) return null;

  const walker = document.createTreeWalker(lineElement, NodeFilter.SHOW_TEXT);
  const range = document.createRange();
  let column = 0;
  let lastNode = null;
  let started = false;

  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    const nextColumn = column + node.length;

    if (!started && startColumn < nextColumn) {
      range.setStart(node, startColumn - column);
      started = true;
    }
    if (started && endColumn <= nextColumn) {
      range.setEnd(node, endColumn - column);
      return range;
    }

    column = nextColumn;
    lastNode = node;
  }

  if (!started) return null;
  range.setEnd(lastNode, lastNode.length);
  return range;
}

function piggySyncPyodideEditorWrapping() {
  const wrap = piggyIsCodeWrapEnabled();

  piggyGetPyodideEditors().forEach((editor) => {
    editor.session.setUseWrapMode(wrap);
  });
}
