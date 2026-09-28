// Piggy's pyodide editor. utils.override_pyodide_js() copies it over markdown-exec's
// _markdown_exec_pyodide.js at startup, so edits need a restart.
// markdown-exec's inline scripts call setupPyodide(idPrefix, install=..., session=...),
// which makes those names globals: don't declare them at the top level here.
// markdown-overrides.js loads after this file, so only use its helpers in functions.

/****************************************\
|* LOADING PYTHON                       *|
\****************************************/
const pyodidePromise = piggyLoadPyodide();

async function piggyLoadPyodide() {
  try {
    const pyodide = await loadPyodide();
    await pyodide.loadPackage("micropip");
    return pyodide;
  } catch {
    return null;
  }
}

// Blocks with the same session share their variables
const piggyPyodideSessions = {};

function piggyGetPyodideSession(name, pyodide) {
  piggyPyodideSessions[name] ??= pyodide.globals.get("dict")();
  return piggyPyodideSessions[name];
}

/****************************************\
|* EDITOR SETUP                         *|
\****************************************/
const piggyPyodideEditors = new Set();

document.addEventListener("piggy:preferenceschange", () => {
  piggyPyodideEditors.forEach((editor) =>
    editor.session.setUseWrapMode(piggyIsCodeWrapEnabled()),
  );
});

// Called by markdown-exec's inline script for every ```pyodide block
async function setupPyodide(
  idPrefix,
  installPackages = null,
  themeLight = null, // unused: piggy's CSS styles the editor
  themeDark = null,
  sessionName = null,
  minLines = 5,
  maxLines = 30,
) {
  const editor = ace.edit(`${idPrefix}editor`);
  const runButton = document.getElementById(`${idPrefix}run`);
  const clearButton = document.getElementById(`${idPrefix}clear`);
  const output = document.getElementById(`${idPrefix}output`);
  const block = output.closest(".pyodide");

  editor.session.setMode("ace/mode/python");
  // Grow with the code (for automatic height markdown-exec sets min = max lines)
  editor.setOptions({
    maxLines: Infinity,
    minLines: minLines === maxLines ? 1 : minLines,
  });
  editor.session.setUseWrapMode(piggyIsCodeWrapEnabled());
  // Whole-pixel gutter, or Ace overlaps it with the code by a fraction of a pixel
  editor.session.gutterRenderer = {
    getWidth: (session, lastLineNumber, config) =>
      Math.ceil(String(lastLineNumber).length * config.characterWidth),
    getText: (session, row) => row + 1,
  };
  piggyPyodideEditors.add(editor);
  piggyHighlightPyodideSelection(editor);
  piggyFocusPyodideEditorFromPadding(editor);

  piggyAddPyodideCopyButtons(block, editor, output);
  piggyAddPyodideResetButton(editor, runButton);
  piggyAddPyodideHelp(block);

  output.dataset.hint = PIGGY_PYODIDE_OUTPUT_HINTS.idle;
  output.replaceChildren(
    piggyCreatePyodideStatus(PIGGY_PYODIDE_STATUS.loading),
  );
  const pyodide = await pyodidePromise;
  output.replaceChildren();
  if (!pyodide) {
    piggyWritePyodideOutput(
      output,
      `${PIGGY_PYODIDE_STATUS.failed}\n`,
      "pyodide-output__error",
    );
    return;
  }

  if (installPackages?.length) {
    try {
      const micropip = pyodide.pyimport("micropip");
      for (const name of installPackages) await micropip.install(name);
    } catch (error) {
      piggyWritePyodideOutput(
        output,
        `Kunne ikke installere ${installPackages.join(", ")}:\n${error}\n`,
        "pyodide-output__error",
      );
    }
  }

  const run = () =>
    piggyRunPyodide(pyodide, editor, output, sessionName ?? "default");
  runButton.addEventListener("click", run);
  clearButton.addEventListener("click", () => piggyClearPyodideOutput(output));
  block.addEventListener("keydown", (event) => {
    if (event.ctrlKey && event.key.toLowerCase() === "enter") {
      event.preventDefault();
      run();
    }
  });
}

// Shown while the output is empty (.pyodide-output:empty::before)
const PIGGY_PYODIDE_OUTPUT_HINTS = {
  idle: 'Trykk "Run" for å kjøre koden - resultatet skrives ut her.',
  noOutput: "Koden kjørte, men skrev ikke ut noe.",
};

// Spinner text while waiting (.pyodide-output__status)
const PIGGY_PYODIDE_STATUS = {
  loading: "Laster inn Python …",
  running: "Kjører koden …",
  failed:
    "Kunne ikke laste inn Python. Sjekk nettet og last inn siden på nytt.",
};

function piggyClearPyodideOutput(output) {
  // Also quietly stops this editor's run (e.g. one waiting for input())
  if (piggyActivePyodideRun?.output === output) {
    piggyActivePyodideRun.stop({ silent: true });
  }
  const height = output.offsetHeight;
  output.replaceChildren();
  output.dataset.hint = PIGGY_PYODIDE_OUTPUT_HINTS.idle;
  piggyResizePyodideOutput(output, height);
}

function piggyCreatePyodideStatus(text) {
  const status = document.createElement("span");
  status.className = "pyodide-output__status";
  status.setAttribute("role", "status");
  status.textContent = text;
  return status;
}

// Slide the output from its old height to what its content needs now
function piggyResizePyodideOutput(output, fromHeight) {
  output.getAnimations().forEach((animation) => animation.cancel());
  output.style.removeProperty("min-height"); // set while running
  const toHeight = output.offsetHeight;
  if (Math.abs(toHeight - fromHeight) < 1 || piggyShouldReduceMotion()) return;

  output.style.setProperty("overflow", "hidden", "important"); // no scrollbar flash
  const animation = output.animate(
    [{ height: `${fromHeight}px` }, { height: `${toHeight}px` }],
    { duration: 220, easing: "ease-out" },
  );
  const done = () => output.style.removeProperty("overflow");
  animation.onfinish = done;
  animation.oncancel = done;
}

// Resolves once the browser has painted the current DOM (or after 100 ms)
function piggyAfterNextPaint() {
  return new Promise((resolve) => {
    requestAnimationFrame(() => setTimeout(resolve));
    setTimeout(resolve, 100);
  });
}

/****************************************\
|* RUNNING CODE                         *|
\****************************************/
// Runs the code with a time limit, Stop, input() and tracebacks without Pyodide's frames
const PIGGY_PYODIDE_RUNNER = `
import builtins
import sys
import time
import traceback
from pyodide.code import eval_code_async

try:
    from pyodide.ffi import can_run_sync, run_sync
except ImportError:  # Pyodide without stack switching (JSPI)
    def can_run_sync():
        return False

M = sys.monitoring


class Stopped(KeyboardInterrupt):
    """Stop was pressed, or the code ran past the time limit."""


def watch(control):
    """Called on loop back-edges and function starts, so no loop runs forever."""
    start = time.monotonic()
    deadline = start + control.timeout
    next_pause = start + 0.1
    events = 0

    def check(*_):
        nonlocal events, next_pause
        events += 1
        if events & 255:  # only look at the clock every 256th event (cheap)
            return
        now = time.monotonic()
        if now > deadline:
            raise Stopped("timeout")
        if now > next_pause and can_run_sync():
            run_sync(control.pause())  # lets the page repaint and Stop get through
            if control.shouldStop():
                raise Stopped("stopped")
            next_pause = time.monotonic() + 0.1

    def extend(seconds):
        nonlocal deadline
        deadline += seconds

    return check, extend


def make_input(control, extend_deadline):
    """input() that reads the answer in the output, like a terminal."""

    def input(prompt=""):
        sys.stdout.write(str(prompt))
        sys.stdout.flush()
        if not can_run_sync():  # can't wait for the page without JSPI: use a dialog
            import js

            answer = js.prompt(str(prompt))
            if answer is None:
                raise EOFError
            print(answer)
            return answer

        waiting_since = time.monotonic()
        try:
            return run_sync(control.readLine())
        except Exception:  # cancelled by Stop or Clear
            raise Stopped("stopped") from None
        finally:  # waiting for the student doesn't count towards the time limit
            extend_deadline(time.monotonic() - waiting_since)

    return input


async def run(code, namespace, control):
    tool = next(i for i in (3, 4) if M.get_tool(i) is None)  # ids no one else uses
    check, extend_deadline = watch(control)
    original_input = builtins.input
    builtins.input = make_input(control, extend_deadline)
    M.use_tool_id(tool, "piggy")
    M.register_callback(tool, M.events.JUMP, check)
    M.register_callback(tool, M.events.PY_START, check)
    M.set_events(tool, M.events.JUMP | M.events.PY_START)
    try:
        return await eval_code_async(code, namespace, filename="main.py")
    except Stopped as exc:
        control.stopped(exc.args[0])
    except SystemExit as exc:  # like CPython: exit("message") is printed, codes aren't
        if exc.code is not None and not isinstance(exc.code, int):
            print(exc.code, file=sys.stderr)
    except BaseException as exc:
        tb = exc.__traceback__
        while tb and tb.tb_frame.f_code.co_filename != "main.py":
            tb = tb.tb_next
        text = "".join(traceback.format_exception(type(exc), exc, tb))
        if tb is None:  # e.g. SyntaxError: drop the indent meant for a "Traceback" header
            text = "".join(line.removeprefix("  ") for line in text.splitlines(keepends=True))
        print(text, end="", file=sys.stderr)
    finally:
        M.set_events(tool, 0)
        M.free_tool_id(tool)
        builtins.input = original_input
        sys.stdout.flush()  # e.g. a last print(..., end="")
        sys.stderr.flush()

run
`;
let piggyPyodideRunner = null;

const PIGGY_PYODIDE_TIMEOUT_SECONDS = 60;
const PIGGY_PYODIDE_STOP_AFTER_MS = 2000; // Run turns into Stop after this long
const PIGGY_PYODIDE_STOPPED = {
  stopped: "Koden ble stoppet.",
  timeout: `Koden ble stoppet etter ${PIGGY_PYODIDE_TIMEOUT_SECONDS} sekunder. Har den en løkke som aldri blir ferdig?`,
};

// One run at a time on the page, since all runs share Pyodide's stdout/stderr
let piggyActivePyodideRun = null;

// Run button and Ctrl+Enter
async function piggyRunPyodide(pyodide, editor, output, sessionName) {
  const active = piggyActivePyodideRun;
  if (active) {
    // Run is the running editor's Stop button once stoppable; other clicks are ignored
    if (active.output === output && active.stoppable) active.stop();
    return;
  }

  const block = output.closest(".pyodide");
  const runButton = block?.querySelector('[id$="--run"]');
  const run = {
    output,
    stoppable: false,
    stopRequested: false,
    silent: false, // stopped by Clear: no "Koden ble stoppet." note
    cancelInput: null, // set while input() waits for an answer
    makeStoppable() {
      if (this.stoppable) return;
      this.stoppable = true;
      piggyShowPyodideStopButton(runButton, true);
    },
    stop({ silent = false } = {}) {
      this.stopRequested = true;
      this.silent ||= silent;
      this.cancelInput?.();
    },
  };
  piggyActivePyodideRun = run;
  document.documentElement.dataset.pyodideRunning = "";
  if (block) block.dataset.running = "";
  const stopTimer = setTimeout(
    () => run.makeStoppable(),
    PIGGY_PYODIDE_STOP_AFTER_MS,
  );

  try {
    await piggyRunPyodideCode(pyodide, editor, output, sessionName, run);
  } finally {
    clearTimeout(stopTimer);
    piggyShowPyodideStopButton(runButton, false);
    piggyActivePyodideRun = null;
    delete document.documentElement.dataset.pyodideRunning;
    if (block) delete block.dataset.running;
  }
}

// Swap the Run label for "■ Stop" and back (same element and click)
const piggyRunButtonContent = new WeakMap();

function piggyShowPyodideStopButton(runButton, showStop) {
  if (!runButton) return;

  if (!showStop) {
    const original = piggyRunButtonContent.get(runButton);
    if (!original) return;
    runButton.replaceChildren(...original.nodes);
    runButton.title = original.title;
    delete runButton.dataset.stop;
    piggyRunButtonContent.delete(runButton);
    return;
  }

  piggyRunButtonContent.set(runButton, {
    nodes: [...runButton.childNodes],
    title: runButton.title,
  });
  const icon = document.createElement("span");
  icon.className = "twemoji";
  const svg = document.createElementNS(PIGGY_SVG_NAMESPACE, "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  const square = document.createElementNS(PIGGY_SVG_NAMESPACE, "path");
  square.setAttribute("d", "M6 6h12v12H6z");
  svg.append(square);
  icon.append(svg);

  runButton.replaceChildren(icon, " Stop");
  runButton.title = "Stopp koden";
  runButton.dataset.stop = "";
}

async function piggyRunPyodideCode(pyodide, editor, output, sessionName, run) {
  // Raw writes, so an input() prompt stays on the answer's line (a tty's stdout
  // is still line buffered, so prints show up while the code runs)
  pyodide.setStdout({ write: piggyPyodideWriter(output), isatty: true });
  pyodide.setStderr({
    write: piggyPyodideWriter(output, "pyodide-output__error"),
  });
  const control = {
    timeout: PIGGY_PYODIDE_TIMEOUT_SECONDS,
    pause: () => new Promise((resolve) => setTimeout(resolve)),
    shouldStop: () => run.stopRequested,
    stopped: (reason) => {
      if (run.silent) return;
      const last = piggyLastPyodideOutput(output);
      const newline = last && !last.textContent.endsWith("\n") ? "\n" : "";
      piggyWritePyodideOutput(
        output,
        `${newline}${PIGGY_PYODIDE_STOPPED[reason]}\n`,
        "pyodide-output__note",
      );
    },
    readLine: () => piggyReadPyodideLine(output, run),
  };

  // Keep the height while running, then slide to the new size
  const startHeight = output.offsetHeight;
  output.getAnimations().forEach((animation) => animation.cancel());
  output.style.setProperty("min-height", `${startHeight}px`, "important");
  const status = piggyCreatePyodideStatus(PIGGY_PYODIDE_STATUS.running);
  output.replaceChildren(status);
  output.dataset.hint = "";
  // Python blocks the page, so paint the spinner first (it spins on the compositor)
  await piggyAfterNextPaint();

  try {
    piggyPyodideRunner ??= pyodide.runPython(PIGGY_PYODIDE_RUNNER, {
      globals: pyodide.globals.get("dict")(),
    });
    const result = await piggyPyodideRunner(
      editor.getValue(),
      piggyGetPyodideSession(sessionName, pyodide),
      control,
    );

    // Like markdown-exec: show the value of a trailing expression
    if (result) piggyWritePyodideOutput(output, `${result}\n`);
    result?.destroy?.();
  } catch (error) {
    piggyWritePyodideOutput(output, `${error}\n`, "pyodide-output__error");
  }

  const endHeight = output.offsetHeight;
  status.remove();
  output.dataset.hint = run.silent
    ? PIGGY_PYODIDE_OUTPUT_HINTS.idle
    : PIGGY_PYODIDE_OUTPUT_HINTS.noOutput;
  piggyResizePyodideOutput(output, endHeight);
}

// Pyodide stdout/stderr "write" handler
function piggyPyodideWriter(output, className = "") {
  const decoder = new TextDecoder(); // streaming: æøå may be split up
  return (bytes) => {
    const text = decoder.decode(bytes, { stream: true });
    if (text) piggyWritePyodideOutput(output, text, className);
    return bytes.length;
  };
}

// Plain text, or a span for errors and notes
function piggyWritePyodideOutput(output, text, className = "") {
  const last = piggyLastPyodideOutput(output);
  if (className && last?.className === className) {
    last.append(text);
    return;
  }

  let node = text;
  if (className) {
    node = document.createElement("span");
    node.className = className;
    node.textContent = text;
  }
  piggyInsertPyodideOutput(output, node);
}

// While the code runs, output goes above the spinner
function piggyPyodideStatusOf(output) {
  return output.querySelector(":scope > .pyodide-output__status");
}

function piggyLastPyodideOutput(output) {
  const status = piggyPyodideStatusOf(output);
  return status ? status.previousSibling : output.lastChild;
}

function piggyInsertPyodideOutput(output, node) {
  const status = piggyPyodideStatusOf(output);
  if (status) {
    status.before(node);
  } else {
    output.append(node);
  }
}

// input(): the answer is typed right after the prompt, and Enter sends it
function piggyReadPyodideLine(output, run) {
  return new Promise((resolve, reject) => {
    const field = document.createElement("input");
    field.type = "text";
    field.className = "pyodide-output__input";
    field.setAttribute("aria-label", "Svar til programmet");
    field.autocomplete = "off";
    field.spellcheck = false;
    field.enterKeyHint = "send";
    // As wide as the answer, plus room for the cursor
    const fit = () => {
      field.style.width = `${field.value.length + 1}ch`;
    };
    field.addEventListener("input", fit);
    fit();

    // Waiting for the student: no spinner, and Stop right away
    const status = piggyPyodideStatusOf(output);
    if (status) status.hidden = true;
    run.makeStoppable();
    const finish = () => {
      if (status) status.hidden = false;
      run.cancelInput = null;
    };

    run.cancelInput = () => {
      field.remove();
      finish();
      reject(new Error("cancelled"));
    };
    field.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" || event.isComposing) return;
      event.preventDefault();
      event.stopPropagation(); // not the block's Ctrl+Enter
      const line = field.value;
      field.replaceWith(`${line}\n`);
      finish();
      resolve(line);
    });

    piggyInsertPyodideOutput(output, field);
    field.focus({ preventScroll: true });
    field.scrollIntoView({ block: "nearest" });
  });
}

/****************************************\
|* EDITOR EXTRAS                        *|
\****************************************/
// Clicks on the padding around Ace focus it: above the code at the start, below at the end
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

function piggyAddPyodideCopyButtons(block, editor, output) {
  const [editorBar, outputBar] = block.querySelectorAll(
    ":scope > .pyodide-editor-bar",
  );
  if (!editorBar || !outputBar) return;

  const copyCode = piggyCreatePyodideCopyButton();
  copyCode.addEventListener("click", () => {
    const code = editor.getValue();

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

function piggyAddPyodideResetButton(editor, runButton) {
  const originalCode = editor.getValue();
  const reset = document.createElement("button");
  reset.type = "button";
  reset.className = "pyodide-reset-button";
  reset.title = "Tilbakestill koden";
  reset.setAttribute("aria-label", "Tilbakestill koden");
  reset.disabled = true;

  reset.addEventListener("click", () => {
    editor.setValue(originalCode, -1);
    editor.focus();
  });
  // Always shown (so Run never moves), but only usable once the code changed
  editor.session.on("change", () => {
    reset.disabled = editor.getValue() === originalCode;
  });

  runButton.before(reset);
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
    ["edit", "Rediger", "Endre koden fritt. Endringer lagres ikke."],
    ["reset", "Tilbakestill", "Setter koden tilbake til slik den var."],
    ["run", "Kjør", "Kjører koden og viser resultatet under Output."],
    ["copy", "Kopier", "Kopierer koden eller resultatet."],
  ],
  shortcutsTitle: "Hurtigtaster",
  // Ctrl+Enter is the block's own handler, which is Ctrl on Mac too
  shortcuts: [
    [[["Ctrl", "Enter"]], "Kjør koden"],
    [[["Tab"], ["Shift", "Tab"]], "Rykk inn / ut"],
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

function piggyAddPyodideHelp(block) {
  const editorBar = block.querySelector(":scope > .pyodide-editor-bar");
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
  block.append(help);

  // The popup lives in the top layer, so place it under the button ourselves
  const position = () => piggyPositionPyodideHelp(help, button);
  help.addEventListener("toggle", (event) => {
    const open = event.newState === "open";
    const method = open ? "addEventListener" : "removeEventListener";

    if (open) {
      const side = help.dataset.side;
      position();
      if (help.dataset.side !== side) {
        // Switch sides without animating, so it slides in from the new side
        help.style.transition = "none";
        help.getBoundingClientRect();
        help.style.removeProperty("transition");
      }
    }
    help.toggleAttribute("data-shown", open);
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
  const below = fitsBelow || !fitsAbove;
  const preferredTop = below
    ? anchor.bottom + gap
    : anchor.top - gap - help.offsetHeight;
  // If it fits neither below nor above, keep it on screen anyway
  const top = Math.max(
    margin,
    Math.min(preferredTop, window.innerHeight - help.offsetHeight - margin),
  );

  help.style.left = `${left}px`;
  help.style.top = `${top}px`;
  help.dataset.side = below ? "below" : "above";
}

/* Selected text in the theme's selection colours, like ::selection elsewhere */
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
