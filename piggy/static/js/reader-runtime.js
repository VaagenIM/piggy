(function () {
  const SCROLL_KEY = "piggy.readerScrollPositions.v1";
  const AUDIO_BLOCK_SELECTOR = [
    "p",
    "li",
    "dt",
    "dd",
    "figcaption",
    "td",
    "th",
  ].join(",");
  const AUDIO_NESTED_CONTAINER_SELECTOR = [
    "p",
    "ul",
    "ol",
    "table",
    "pre",
    "details",
    ".highlight",
  ].join(",");
  const AUDIO_HEADING_SELECTOR = "h1, h2, h3, h4, h5, h6";
  const AUDIO_SKIP_SELECTOR = [
    "a",
    "button",
    "script",
    "style",
    "pre",
    ".highlight",
    ".MathJax",
    ".md-code__nav",
  ].join(",");
  const AUDIO_TEXT_SKIP_SELECTOR = [
    "button",
    "script",
    "style",
    "pre",
    ".highlight",
    ".MathJax",
    ".md-code__nav",
  ].join(",");
  const AUDIO_INTERACTIVE_SELECTOR = [
    "a",
    "button",
    "input",
    "select",
    "textarea",
    "label",
    "summary",
    "[contenteditable='true']",
  ].join(",");
  const SENTENCE_BOUNDARY_CHARS = ".!?";
  const SENTENCE_CLOSING_CHARS = "\"')]}»”’";
  const ABBREVIATIONS = new Set([
    "adm",
    "bl.a",
    "ca",
    "dvs",
    "e.g",
    "etc",
    "f.eks",
    "fig",
    "i.e",
    "kap",
    "m.m",
    "mr",
    "mrs",
    "ms",
    "nr",
    "osv",
    "prof",
    "st",
    "vs",
  ]);
  const CODE_FILE_EXTENSIONS = new Set([
    "bat",
    "c",
    "cpp",
    "cs",
    "css",
    "csv",
    "db",
    "env",
    "gif",
    "go",
    "html",
    "java",
    "jpeg",
    "jpg",
    "js",
    "json",
    "jsx",
    "log",
    "m4a",
    "md",
    "mp3",
    "ogg",
    "opus",
    "pdf",
    "php",
    "png",
    "py",
    "rb",
    "rs",
    "sh",
    "sql",
    "svg",
    "toml",
    "ts",
    "tsx",
    "txt",
    "wav",
    "webm",
    "webp",
    "yaml",
    "yml",
    "zip",
  ]);
  const DOCTYPE_PATTERN = /^<!\s*doctype\s+html\s*>$/i;
  const DOCTYPE_TEXT_PATTERN = /<!\s*doctype\s+html\s*>/gi;
  const HTML_TAG_PATTERN = /^<\s*(\/)?\s*([a-zA-Z][\w:-]*)(?:\s+[^<>]*)?>$/;
  const HTML_TAG_TEXT_PATTERN = /<\s*(\/)?\s*([a-zA-Z][\w:-]*)(?:\s+[^<>]*)?>/g;
  const LATEX_INLINE_PATTERN = /\\\((.*?)\\\)|\\\[(.*?)\\\]/g;
  const LATEX_COMMAND_REPLACEMENTS = [
    ["\\cdot", " times "],
    ["\\times", " times "],
    ["\\lfloor", "floor of "],
    ["\\rfloor", ""],
    ["\\left", ""],
    ["\\right", ""],
  ];
  const LATEX_BACKSLASH_COMMAND_PATTERN = /\\([A-Za-z]+)/g;
  const FUNCTION_CALL_PATTERN = /\b([A-Za-z_][\w-]*)\s*\(\)/g;
  const FUNCTION_ARGS_PATTERN = /\b([A-Za-z_][\w-]*)\(\s*([^()]{1,32})\s*\)/g;
  const SHELL_POSITIONAL_ARG_PATTERN = /\$(\d+)/g;
  const PYTHON_REVERSE_SLICE_PATTERN =
    /\b([A-Za-z_][\w-]*)\s*\[\s*::\s*-1\s*\]/g;
  const INDEX_ACCESS_PATTERN =
    /\b([A-Za-z_][\w-]*)\[\s*([A-Za-z_][\w-]*|\d+)\s*\]/g;
  const EMPTY_BRACKETS_PATTERN = /\[\s*\]/g;
  const BRACKETED_LIST_PATTERN = /\[([^[\]]*,[^[\]]*)\]/g;
  const CITATION_LABEL_PATTERN = /\s*\[[A-Za-z]\]\s*/g;
  const SIMPLE_BRACKETS_PATTERN = /\[([^[\]]{1,48})\]/g;
  const QUOTED_CODE_TOKEN_PATTERN = /["“”']([A-Za-z0-9_]+)["“”']/g;
  const SPACE_BEFORE_PUNCTUATION_PATTERN = /\s+([,.;:!?])/g;
  const DUPLICATE_COMMA_PATTERN = /,\s*,+/g;
  const FILE_EXTENSION_PATTERN =
    /\b([A-Za-z0-9][A-Za-z0-9_-]*)\.([A-Za-z0-9]{1,8})\b/g;
  const STANDALONE_EXTENSION_PATTERN = /(^|[^\w.])\.([A-Za-z0-9]{1,8})\b/g;
  const SPACED_ASCII_ARROW_PATTERN = /\s+-\s+>\s*/g;
  const INLINE_ARROW_PATTERN = /(?<=\S)\s*(?:->|→|⇒|⟶)\s*(?=\S)/g;
  const LEADING_ARROW_PATTERN = /(^|\s)(?:->|→|⇒|⟶)\s*/g;
  const COMPARISON_REPLACEMENTS = [
    [/!=/g, " is not equal to "],
    [/==/g, " equals "],
    [/>=/g, " greater than or equal to "],
    [/<=/g, " less than or equal to "],
    [/(?<=\S)\s+>\s+(?=\S)/g, " greater than "],
    [/(?<=\S)\s+<\s+(?=\S)/g, " less than "],
  ];
  const SPACED_MULTIPLY_PATTERN = /\s+\*\s+/g;
  const SPACED_PLUS_PATTERN = /\s+\+\s+/g;
  const SPACED_EQUALS_PATTERN = /\s+=\s+/g;
  const SPACED_NUMERIC_MINUS_PATTERN = /(?<=\d)\s+-\s+(?=\d)/g;
  const NUMERIC_FACTORIAL_PATTERN =
    /(?<=\d)!(?=\s*(?:$|=|,|\)|\]|}|\*|·|times))/g;
  const EMOJI_PATTERN =
    /[\u2600-\u27bf\ufe0f]|\ud83c[\udf00-\udfff]|\ud83d[\udc00-\udeff]|\ud83e[\udd00-\uddff]/g;

  let preferencesApi = null;
  let settingsPageApi = null;
  let settingsPage = null;
  let readerRuler = null;
  let markdownContent = null;
  let audioReaderRoot = null;
  let audioReaderBaseUrl = "";
  let audioReaderLanguage = "";
  let audioReaderLevel = "00";
  let lastPreferences = null;
  let scrollSaveTimeout = null;
  let initialized = false;
  let audioReaderPrepared = false;
  let audioReaderEnabled = false;
  let audioReaderLiveRegion = null;
  let audioElement = null;
  let audioPlayback = null;
  let activeAudioSource = null;
  let sentenceCounter = 0;
  let paragraphCounter = 0;
  let sectionCounter = 0;
  let audioItems = new Map();

  function initialize(nextPreferencesApi, options = {}) {
    if (initialized) return;
    initialized = true;

    preferencesApi = nextPreferencesApi;
    settingsPageApi = options.settingsPageApi || null;
    settingsPage = document.getElementById("settings-page");
    readerRuler = document.getElementById("reader-ruler");
    markdownContent = document.querySelector(
      "main .md-content:not(.settings-reader-preview)",
    );
    audioReaderRoot = document.querySelector("[data-reader-audio-root]");
    audioReaderBaseUrl = audioReaderRoot?.dataset.readerAudioBaseUrl || "";
    audioReaderLanguage = audioReaderRoot?.dataset.readerAudioLanguage || "";
    audioReaderLevel = formatAudioLevel(
      audioReaderRoot?.dataset.readerAudioLevel || "0",
    );
    lastPreferences = preferencesApi.getPreferences();

    updateThemeEffects(lastPreferences);
    initializeReaderRuler();
    initializeRememberedPosition();
    initializeScrollTracking();
    initializeReducedMotionListener();
    initializeAudioReader();

    document.addEventListener("piggy:preferenceschange", (event) => {
      const nextPreferences = event.detail.preferences;
      const changedKey = event.detail.changedKey;

      updateThemeEffects(nextPreferences, changedKey);

      if (changedKey === "rememberPosition" && isSettingsCurrentlyActive()) {
        saveSourceScrollPosition();
      } else if (changedKey === "rememberPosition") {
        saveScrollPosition();
      }

      if (changedKey === "audioReader" || changedKey === "multiple") {
        syncAudioReaderState(nextPreferences);
      }

      lastPreferences = nextPreferences;
    });
  }

  function initializeScrollTracking() {
    window.addEventListener(
      "scroll",
      () => {
        if (isSettingsCurrentlyActive()) return;
        if (preferencesApi.getPreferences().rememberPosition !== "on") return;

        window.clearTimeout(scrollSaveTimeout);
        scrollSaveTimeout = window.setTimeout(saveScrollPosition, 160);
      },
      { passive: true },
    );

    window.addEventListener("pagehide", () => {
      if (!isSettingsCurrentlyActive()) saveScrollPosition();
    });
  }

  function initializeReducedMotionListener() {
    window
      .matchMedia?.("(prefers-reduced-motion: reduce)")
      .addEventListener?.("change", () => {
        updateThemeEffects(preferencesApi.getPreferences(), "reduceMotion");
      });
  }

  function updateThemeEffects(preferences, changedKey = "") {
    const themeChanged =
      changedKey === "theme" ||
      (changedKey === "readerPreset" &&
        preferences.theme !== lastPreferences?.theme);

    if (themeChanged && shouldAnimatePreferenceChange(preferences)) {
      pageTransition();
    }

    stopAllAnimations();

    if (shouldSuppressThemeEffects(preferences)) {
      return;
    }

    switch (preferences.theme) {
      case "matrix":
        callIfFunction("startMatrixAnimation");
        break;
      case "space":
        callIfFunction("startSpaceAnimation");
        break;
      case "ocean":
        callIfFunction("startOceanShaderAnimation");
        break;
      case "desert":
        callIfFunction("startDesertShaderAnimation");
        break;
      case "golden":
        callIfFunction("startGoldenShaderAnimation");
        break;
    }
  }

  function shouldSuppressThemeEffects(preferences) {
    if (preferences.hideDecorations === "on") return true;
    if (preferences.reduceMotion === "reduce") return true;

    return (
      preferences.reduceMotion === "system" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
    );
  }

  function shouldAnimatePreferenceChange(preferences) {
    return !shouldSuppressThemeEffects(preferences);
  }

  function pageTransition() {
    document.body.classList.add("transition");
    window.setTimeout(() => {
      document.body.classList.remove("transition");
    }, 400);
  }

  function callIfFunction(name) {
    if (typeof window[name] === "function") {
      window[name]();
    }
  }

  function stopAllAnimations() {
    callIfFunction("stopMatrixAnimation");
    callIfFunction("stopSpaceAnimation");
    callIfFunction("stopOceanShaderAnimation");
    callIfFunction("stopDesertShaderAnimation");
    callIfFunction("stopGoldenShaderAnimation");
  }

  function initializeReaderRuler() {
    if (!readerRuler || !markdownContent) return;

    const updateRuler = (clientY) => {
      if (preferencesApi.getPreferences().readingRuler !== "on") return;

      syncReaderRulerBounds();
      document.documentElement.style.setProperty(
        "--piggy-reader-ruler-top",
        `${clientY}px`,
      );
      readerRuler.classList.add("is-visible");
    };

    markdownContent.addEventListener("mousemove", (event) => {
      updateRuler(event.clientY);
    });

    markdownContent.addEventListener(
      "touchmove",
      (event) => {
        const touch = event.touches[0];
        if (touch) updateRuler(touch.clientY);
      },
      { passive: true },
    );

    markdownContent.addEventListener("mouseleave", () => {
      readerRuler.classList.remove("is-visible");
    });

    document.addEventListener("piggy:preferenceschange", (event) => {
      if (event.detail.preferences.readingRuler !== "on") {
        readerRuler.classList.remove("is-visible");
        return;
      }

      syncReaderRulerBounds();
    });

    window.addEventListener("resize", syncReaderRulerBounds);
  }

  function syncReaderRulerBounds() {
    if (!markdownContent) return;

    const rect = markdownContent.getBoundingClientRect();
    document.documentElement.style.setProperty(
      "--piggy-reader-ruler-left",
      `${Math.max(0, rect.left)}px`,
    );
    document.documentElement.style.setProperty(
      "--piggy-reader-ruler-width",
      `${Math.max(0, rect.width)}px`,
    );
  }

  function initializeAudioReader() {
    if (!audioReaderRoot || !markdownContent || !audioReaderBaseUrl) return;

    syncAudioReaderState(lastPreferences);
  }

  function syncAudioReaderState(preferences) {
    if (!audioReaderRoot || !markdownContent || !audioReaderBaseUrl) return;

    audioReaderEnabled = preferences.audioReader === "on";

    if (audioReaderEnabled) {
      prepareAudioReader();
      updateAudioTargetTabIndex(true);
      return;
    }

    stopAudioPlayback();
    updateAudioTargetTabIndex(false);
  }

  function prepareAudioReader() {
    if (!audioReaderRoot || !markdownContent || !audioReaderBaseUrl) return;
    if (audioReaderPrepared) return;

    audioReaderPrepared = true;
    audioElement = new Audio();
    audioElement.preload = "none";
    audioElement.addEventListener("ended", playNextAudioItem);
    audioElement.addEventListener("error", handleAudioError);

    audioReaderLiveRegion = document.createElement("div");
    audioReaderLiveRegion.className = "reader-audio-live";
    audioReaderLiveRegion.setAttribute("aria-live", "polite");
    audioReaderLiveRegion.setAttribute("aria-atomic", "true");
    audioReaderRoot.append(audioReaderLiveRegion);

    buildAudioTargets();
    audioReaderRoot.addEventListener("click", handleAudioReaderClick);
    audioReaderRoot.addEventListener("keydown", handleAudioReaderKeydown);
  }

  function buildAudioTargets() {
    audioItems = new Map();
    sentenceCounter = 0;
    paragraphCounter = 0;
    sectionCounter = 0;

    const pageHeading = audioReaderRoot.querySelector(".assignment-heading");
    if (pageHeading) {
      getHeadingSentenceIds(pageHeading);
    }

    getReadableAudioTargets(markdownContent).forEach((element) => {
      if (element.matches(AUDIO_HEADING_SELECTOR)) {
        getHeadingSentenceIds(element);
        return;
      }

      prepareAudioBlock(element);
    });

    prepareAudioSections();
  }

  function getReadableAudioTargets(root) {
    return [
      ...root.querySelectorAll(
        `${AUDIO_HEADING_SELECTOR}, ${AUDIO_BLOCK_SELECTOR}`,
      ),
    ].filter((element) =>
      element.matches(AUDIO_HEADING_SELECTOR)
        ? isReadableAudioHeading(element)
        : isReadableAudioBlock(element),
    );
  }

  function isReadableAudioHeading(element) {
    if (!(element instanceof HTMLElement)) return false;
    if (!normalizeReaderText(element.textContent)) return false;
    if (element.closest(".settings-reader-preview")) return false;
    if (element.closest(AUDIO_SKIP_SELECTOR)) return false;

    return true;
  }

  function isReadableAudioBlock(element) {
    if (!(element instanceof HTMLElement)) return false;
    if (!getElementAudioText(element, { includeNestedContainers: false })) {
      return false;
    }
    if (element.closest(".settings-reader-preview")) return false;
    if (element.closest(AUDIO_SKIP_SELECTOR)) return false;
    if (element.matches(AUDIO_HEADING_SELECTOR)) return false;

    return true;
  }

  function prepareAudioBlock(block) {
    if (block.dataset.readerAudioPrepared === "true") return;

    const textEntries = getAudioTextEntries(block, {
      includeNestedContainers: false,
    });
    const readableText = textEntries.map((entry) => entry.text).join("");
    const normalizedBlockText = normalizeReaderText(readableText);

    if (!normalizedBlockText) return;

    const sentenceSegments = splitReaderSentences(readableText)
      .map((segment) => ({
        ...segment,
        text: normalizeReaderText(segment.text),
        audioText: prepareSentenceAudioText(segment.text),
      }))
      .filter((segment) => segment.text && segment.audioText);

    if (!sentenceSegments.length) {
      const audioText = prepareSentenceAudioText(normalizedBlockText);
      if (audioText) {
        sentenceSegments.push({
          start: 0,
          end: readableText.length,
          text: normalizedBlockText,
          audioText,
        });
      }
    }

    if (!sentenceSegments.length) return;

    sentenceSegments.forEach((segment) => {
      segment.id = createAudioId("s", ++sentenceCounter);
      audioItems.set(segment.id, {
        id: segment.id,
        kind: "sentence",
        text: segment.audioText,
      });
    });

    wrapAudioTextEntries(textEntries, sentenceSegments);

    const paragraphId = createAudioId("p", ++paragraphCounter);
    const sentenceIds = sentenceSegments.map((segment) => segment.id);

    block.dataset.readerAudioPrepared = "true";
    block.dataset.readerAudioParagraph = paragraphId;
    block.dataset.readerAudioSequence = sentenceIds.join(" ");
    block.dataset.readerAudioSentenceIds = sentenceIds.join(" ");
    block.tabIndex = audioReaderEnabled ? 0 : -1;

    audioItems.set(paragraphId, {
      id: paragraphId,
      kind: "paragraph",
      text: normalizedBlockText,
      sequence: sentenceIds,
      element: block,
    });
  }

  function getAudioTextEntries(root, options = {}) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        if (!node.nodeValue) return NodeFilter.FILTER_REJECT;
        if (node.parentElement?.closest(AUDIO_TEXT_SKIP_SELECTOR)) {
          return NodeFilter.FILTER_REJECT;
        }
        if (
          options.includeNestedContainers === false &&
          isInsideNestedAudioContainer(node, root)
        ) {
          return NodeFilter.FILTER_REJECT;
        }
        return NodeFilter.FILTER_ACCEPT;
      },
    });

    const entries = [];
    let offset = 0;
    let node = walker.nextNode();

    while (node) {
      const text = node.nodeValue || "";
      entries.push({
        node,
        text,
        start: offset,
        end: offset + text.length,
        wrappable: !node.parentElement?.closest(AUDIO_INTERACTIVE_SELECTOR),
      });
      offset += text.length;
      node = walker.nextNode();
    }

    return entries;
  }

  function isInsideNestedAudioContainer(node, root) {
    let current = node.parentElement;

    while (current && current !== root) {
      if (current.matches(AUDIO_NESTED_CONTAINER_SELECTOR)) {
        return true;
      }
      current = current.parentElement;
    }

    return false;
  }

  function wrapAudioTextEntries(textEntries, sentenceSegments) {
    textEntries.forEach((entry) => {
      if (!entry.wrappable) return;

      const fragment = document.createDocumentFragment();
      let localOffset = 0;

      sentenceSegments.forEach((segment) => {
        const overlapStart = Math.max(entry.start, segment.start);
        const overlapEnd = Math.min(entry.end, segment.end);

        if (overlapEnd <= overlapStart) return;

        const localStart = overlapStart - entry.start;
        const localEnd = overlapEnd - entry.start;

        if (localStart > localOffset) {
          fragment.append(
            document.createTextNode(entry.text.slice(localOffset, localStart)),
          );
        }

        const textPart = entry.text.slice(localStart, localEnd);

        if (normalizeReaderText(textPart)) {
          fragment.append(createSentenceSpan(textPart, segment.id));
        } else {
          fragment.append(document.createTextNode(textPart));
        }

        localOffset = localEnd;
      });

      if (localOffset < entry.text.length) {
        fragment.append(document.createTextNode(entry.text.slice(localOffset)));
      }

      if (fragment.childNodes.length) {
        entry.node.replaceWith(fragment);
      }
    });
  }

  function createSentenceSpan(text, sentenceId) {
    const span = document.createElement("span");
    span.className = "reader-audio-sentence";
    span.dataset.readerAudioSentence = sentenceId;
    span.tabIndex = audioReaderEnabled ? 0 : -1;
    span.textContent = text;
    return span;
  }

  function prepareAudioSections() {
    const pageHeading = audioReaderRoot.querySelector(".assignment-heading");
    const headings = [
      ...markdownContent.querySelectorAll(AUDIO_HEADING_SELECTOR),
    ];

    if (pageHeading) {
      getHeadingSentenceIds(pageHeading);
    }

    headings.forEach(getHeadingSentenceIds);

    if (pageHeading) {
      prepareAudioSection(pageHeading, getAllSentenceIds(markdownContent));
    }

    headings.forEach((heading) => {
      prepareAudioSection(heading, getSectionSentenceIds(heading));
    });
  }

  function prepareAudioSection(heading, bodySentenceIds) {
    if (!(heading instanceof HTMLElement)) return;

    const headingText = getElementAudioText(heading);
    const headingSentenceIds = getHeadingSentenceIds(heading);
    const sequence = [...headingSentenceIds, ...bodySentenceIds];

    if (!sequence.length) return;

    const sectionId = createAudioId("sec", ++sectionCounter);

    heading.dataset.readerAudioSection = sectionId;
    heading.dataset.readerAudioSequence = sequence.join(" ");
    heading.tabIndex = audioReaderEnabled ? 0 : -1;

    audioItems.set(sectionId, {
      id: sectionId,
      kind: "section",
      text: headingText,
      sequence,
      element: heading,
    });
  }

  function getAllSentenceIds(root) {
    const ids = [];
    collectSentenceIds(root, ids);
    return ids;
  }

  function getSectionSentenceIds(heading) {
    const ids = [];
    const headingLevel = getHeadingLevel(heading);
    let element = heading.nextElementSibling;

    while (element) {
      if (
        element.matches(AUDIO_HEADING_SELECTOR) &&
        getHeadingLevel(element) <= headingLevel
      ) {
        break;
      }

      collectSentenceIds(element, ids);
      element = element.nextElementSibling;
    }

    return ids;
  }

  function getHeadingSentenceIds(heading) {
    if (!(heading instanceof HTMLElement)) return [];

    if (heading.dataset.readerAudioHeadingSentenceIds) {
      return splitAudioSequence(heading.dataset.readerAudioHeadingSentenceIds);
    }

    const headingText = getElementAudioText(heading);
    const ids = headingText
      ? splitReaderSentences(headingText)
          .map((segment) => prepareSentenceAudioText(segment.text))
          .filter(Boolean)
          .map((text) => {
            const id = createAudioId("s", ++sentenceCounter);
            audioItems.set(id, {
              id,
              kind: "sentence",
              text,
            });
            return id;
          })
      : [];

    heading.dataset.readerAudioHeadingSentenceIds = ids.join(" ");
    return ids;
  }

  function getElementAudioText(element, options = {}) {
    return normalizeReaderText(
      getAudioTextEntries(element, options)
        .map((entry) => entry.text)
        .join(""),
    );
  }

  function collectSentenceIds(root, output) {
    if (!(root instanceof HTMLElement)) return;

    if (root.matches(AUDIO_HEADING_SELECTOR)) {
      output.push(...getHeadingSentenceIds(root));
      return;
    }

    if (root.dataset.readerAudioSentenceIds) {
      output.push(...splitAudioSequence(root.dataset.readerAudioSentenceIds));
    }

    root
      .querySelectorAll(
        "[data-reader-audio-heading-sentence-ids], [data-reader-audio-sentence-ids]",
      )
      .forEach((element) => {
        if (element.matches(AUDIO_HEADING_SELECTOR)) {
          output.push(...getHeadingSentenceIds(element));
          return;
        }

        output.push(
          ...splitAudioSequence(element.dataset.readerAudioSentenceIds),
        );
      });
  }

  function getHeadingLevel(heading) {
    const match = heading.tagName.match(/^H([1-6])$/i);
    return match ? Number(match[1]) : 1;
  }

  function handleAudioReaderClick(event) {
    if (!audioReaderEnabled) return;

    const target = event.target;
    if (!(target instanceof Element)) return;

    const sentence = target.closest("[data-reader-audio-sentence]");
    if (sentence && audioReaderRoot.contains(sentence)) {
      event.preventDefault();
      event.stopPropagation();
      playAudioIds([sentence.dataset.readerAudioSentence], sentence);
      return;
    }

    if (target.closest(AUDIO_INTERACTIVE_SELECTOR)) return;

    const section = target.closest("[data-reader-audio-section]");
    if (section && audioReaderRoot.contains(section)) {
      event.preventDefault();
      playAudioSource(section.dataset.readerAudioSection, section);
      return;
    }

    const paragraph = target.closest("[data-reader-audio-paragraph]");
    if (paragraph && audioReaderRoot.contains(paragraph)) {
      event.preventDefault();
      playAudioSource(paragraph.dataset.readerAudioParagraph, paragraph);
    }
  }

  function handleAudioReaderKeydown(event) {
    if (!audioReaderEnabled || !["Enter", " "].includes(event.key)) return;

    const target = event.target;
    if (!(target instanceof Element)) return;

    const sentence = target.closest("[data-reader-audio-sentence]");
    if (sentence && audioReaderRoot.contains(sentence)) {
      event.preventDefault();
      playAudioIds([sentence.dataset.readerAudioSentence], sentence);
      return;
    }

    const section = target.closest("[data-reader-audio-section]");
    if (section && audioReaderRoot.contains(section)) {
      event.preventDefault();
      playAudioSource(section.dataset.readerAudioSection, section);
      return;
    }

    const paragraph = target.closest("[data-reader-audio-paragraph]");
    if (paragraph && audioReaderRoot.contains(paragraph)) {
      event.preventDefault();
      playAudioSource(paragraph.dataset.readerAudioParagraph, paragraph);
    }
  }

  function playAudioSource(sourceId, sourceElement) {
    const source = audioItems.get(sourceId);
    if (!source) return;

    const sequence = source.sequence?.length ? source.sequence : [source.id];
    playAudioIds(sequence, sourceElement || source.element);
  }

  function playAudioIds(ids, sourceElement = null) {
    const queue = ids.filter(Boolean);
    if (!queue.length) return;

    if (isCurrentAudioRequest(queue, sourceElement)) {
      stopAudioPlayback({ keepLiveStatus: true });
      updateAudioLiveRegion("Audio stopped.");
      return;
    }

    prepareAudioReader();
    stopAudioPlayback({ keepLiveStatus: true });

    audioPlayback = {
      queue,
      index: 0,
      sourceElement,
    };

    setActiveAudioSource(sourceElement);
    playCurrentAudioItem();
  }

  function isCurrentAudioRequest(queue, sourceElement) {
    if (!audioPlayback) return false;

    if (
      sourceElement instanceof HTMLElement &&
      sourceElement.dataset.readerAudioState === "playing"
    ) {
      return true;
    }

    return (
      audioPlayback.sourceElement === sourceElement &&
      areAudioQueuesEqual(audioPlayback.queue, queue)
    );
  }

  function areAudioQueuesEqual(left, right) {
    if (!Array.isArray(left) || !Array.isArray(right)) return false;
    if (left.length !== right.length) return false;

    return left.every((id, index) => id === right[index]);
  }

  function playCurrentAudioItem() {
    if (!audioPlayback || !audioElement) return;

    const audioId = audioPlayback.queue[audioPlayback.index];
    if (!audioId) {
      finishAudioPlayback();
      return;
    }

    setActiveAudioId(audioId);
    updateAudioLiveRegion(`Playing ${getAudioLabel(audioId)}.`);

    audioElement.src = getAudioUrl(audioId);
    audioElement.load();

    const playPromise = audioElement.play();
    if (playPromise?.catch) {
      playPromise.catch(() => {
        updateAudioLiveRegion("Could not start the audio.");
        finishAudioPlayback();
      });
    }
  }

  function playNextAudioItem() {
    if (!audioPlayback) return;

    audioPlayback.index += 1;
    playCurrentAudioItem();
  }

  function handleAudioError() {
    if (!audioPlayback) return;

    const audioId = audioPlayback.queue[audioPlayback.index];
    markAudioIdState(audioId, "missing");
    audioPlayback.index += 1;

    if (audioPlayback.index >= audioPlayback.queue.length) {
      updateAudioLiveRegion("No audio file was found for this text.");
      finishAudioPlayback();
      return;
    }

    playCurrentAudioItem();
  }

  function stopAudioPlayback(options = {}) {
    if (audioElement) {
      audioElement.pause();
      audioElement.removeAttribute("src");
      audioElement.load();
    }

    audioPlayback = null;
    clearActiveAudioStates();
    setActiveAudioSource(null);

    if (!options.keepLiveStatus) {
      updateAudioLiveRegion("");
    }
  }

  function finishAudioPlayback() {
    if (audioElement) {
      audioElement.pause();
      audioElement.removeAttribute("src");
    }

    audioPlayback = null;
    clearActiveAudioStates();
    setActiveAudioSource(null);
  }

  function setActiveAudioSource(sourceElement) {
    if (activeAudioSource && activeAudioSource !== sourceElement) {
      if (activeAudioSource.dataset.readerAudioState === "playing") {
        delete activeAudioSource.dataset.readerAudioState;
      }
    }

    activeAudioSource =
      sourceElement instanceof HTMLElement ? sourceElement : null;

    if (activeAudioSource) {
      activeAudioSource.dataset.readerAudioState = "playing";
    }
  }

  function setActiveAudioId(audioId) {
    clearActiveAudioStates();
    markAudioIdState(audioId, "playing");
  }

  function clearActiveAudioStates() {
    audioReaderRoot
      ?.querySelectorAll('[data-reader-audio-state="playing"]')
      .forEach((element) => {
        if (element !== activeAudioSource) {
          delete element.dataset.readerAudioState;
        }
      });
  }

  function markAudioIdState(audioId, state) {
    if (!audioId) return;

    audioReaderRoot
      ?.querySelectorAll(`[data-reader-audio-sentence="${audioId}"]`)
      .forEach((element) => {
        element.dataset.readerAudioState = state;
      });
  }

  function updateAudioTargetTabIndex(enabled) {
    if (!audioReaderPrepared) return;

    audioReaderRoot
      ?.querySelectorAll(
        "[data-reader-audio-sentence], [data-reader-audio-paragraph], [data-reader-audio-section]",
      )
      .forEach((element) => {
        element.tabIndex = enabled ? 0 : -1;
      });
  }

  function updateAudioLiveRegion(message) {
    if (audioReaderLiveRegion) {
      audioReaderLiveRegion.textContent = message;
    }
  }

  function getAudioUrl(audioId) {
    const url = new URL(
      `${audioReaderBaseUrl.replace(/\/$/, "")}/${encodeURIComponent(audioId)}`,
      window.location.origin,
    );

    if (audioReaderLanguage) {
      url.searchParams.set("lang", audioReaderLanguage);
    }

    return `${url.pathname}${url.search}`;
  }

  function getAudioLabel(audioId) {
    const item = audioItems.get(audioId);
    if (!item) return "audio";

    return item.kind;
  }

  function splitAudioSequence(value) {
    return String(value || "")
      .split(/\s+/)
      .filter(Boolean);
  }

  function splitReaderSentences(text) {
    if (!text) return [];

    const segments = [];
    let start = 0;
    let index = 0;

    while (index < text.length) {
      const boundaryEnd = getSentenceBoundaryEnd(text, index);
      if (boundaryEnd === -1) {
        index += 1;
        continue;
      }

      appendSentenceSegment(segments, text, start, boundaryEnd);
      start = skipWhitespace(text, boundaryEnd);
      index = start;
    }

    appendSentenceSegment(segments, text, start, text.length);
    return segments;
  }

  function appendSentenceSegment(segments, text, start, end) {
    const normalized = normalizeReaderText(text.slice(start, end));
    if (!normalized) return;

    segments.push({
      start,
      end,
      text: normalized,
    });
  }

  function getSentenceBoundaryEnd(text, index) {
    const char = text[index];
    if (!SENTENCE_BOUNDARY_CHARS.includes(char)) return -1;
    if (isInsideAngleToken(text, index)) return -1;
    if (isInsideFunctionToken(text, index)) return -1;
    if (char === "!" && isFactorialMarker(text, index)) return -1;
    if (char === "." && !isPeriodSentenceBoundary(text, index)) return -1;
    if ((char === "!" || char === "?") && text[index - 1] === "<") return -1;

    let end = index + 1;
    while (end < text.length && SENTENCE_BOUNDARY_CHARS.includes(text[end])) {
      end += 1;
    }

    while (end < text.length && SENTENCE_CLOSING_CHARS.includes(text[end])) {
      end += 1;
    }

    if (end >= text.length) return end;
    if (!/\s/.test(text[end])) return -1;

    return end;
  }

  function isPeriodSentenceBoundary(text, index) {
    const previousChar = index > 0 ? text[index - 1] : "";
    const nextChar = index + 1 < text.length ? text[index + 1] : "";

    if (previousChar === "." || nextChar === ".") {
      return nextChar !== ".";
    }

    if (isDigit(previousChar) && isDigit(nextChar)) return false;
    if (isAlphaNumeric(previousChar) && isAlphaNumeric(nextChar)) return false;
    if (isSpacedInitialPeriod(text, index)) return false;
    if (isKnownAbbreviation(text, index)) return false;

    return true;
  }

  function isSpacedInitialPeriod(text, index) {
    let tokenStart = index;
    while (tokenStart > 0 && isAlpha(text[tokenStart - 1])) {
      tokenStart -= 1;
    }

    const token = text.slice(tokenStart, index);
    if (token.length !== 1 || !isAlpha(token)) return false;

    const nextIndex = skipWhitespace(text, index + 1);
    if (
      nextIndex + 1 < text.length &&
      isAlpha(text[nextIndex]) &&
      text[nextIndex + 1] === "."
    ) {
      return true;
    }

    let previousIndex = tokenStart - 1;
    while (previousIndex >= 0 && /\s/.test(text[previousIndex])) {
      previousIndex -= 1;
    }

    if (previousIndex < 0 || text[previousIndex] !== ".") return false;

    const previousTokenEnd = previousIndex;
    let previousTokenStart = previousTokenEnd;
    while (previousTokenStart > 0 && isAlpha(text[previousTokenStart - 1])) {
      previousTokenStart -= 1;
    }

    const previousToken = text.slice(previousTokenStart, previousTokenEnd);
    return previousToken.length === 1 && isAlpha(previousToken);
  }

  function isKnownAbbreviation(text, index) {
    let tokenStart = index;
    while (tokenStart > 0 && isAbbreviationTokenChar(text[tokenStart - 1])) {
      tokenStart -= 1;
    }

    const token = text
      .slice(tokenStart, index)
      .replace(/^\.+|\.+$/g, "")
      .toLowerCase();
    if (ABBREVIATIONS.has(token)) return true;

    const parts = token.split(".").filter(Boolean);
    return (
      parts.length > 1 &&
      parts.every((part) => part.length === 1 && isAlpha(part))
    );
  }

  function isInsideAngleToken(text, index) {
    const tokenStart = text.lastIndexOf("<", index);
    if (tokenStart === -1) return false;

    const previousClose = text.lastIndexOf(">", index);
    if (previousClose > tokenStart) return false;

    const tokenEnd = text.indexOf(">", index + 1);
    if (tokenEnd === -1) return false;

    const token = text.slice(tokenStart, tokenEnd + 1);
    return DOCTYPE_PATTERN.test(token) || HTML_TAG_PATTERN.test(token);
  }

  function isInsideFunctionToken(text, index) {
    const tokenStart = text.lastIndexOf("(", index);
    if (tokenStart <= 0) return false;

    const previousClose = text.lastIndexOf(")", index);
    if (previousClose > tokenStart) return false;

    const tokenEnd = text.indexOf(")", index + 1);
    if (tokenEnd === -1) return false;
    if (!/[\w-]/.test(text[tokenStart - 1])) return false;

    const tokenPrefix =
      text.slice(0, tokenStart).trimEnd().split(/\s+/).pop() || "";
    return /^[A-Za-z_][\w-]*$/.test(tokenPrefix);
  }

  function isFactorialMarker(text, index) {
    if (index <= 0 || !/[\w)]/.test(text[index - 1])) return false;

    const nextIndex = skipWhitespace(text, index + 1);
    if (nextIndex >= text.length) return false;

    return ["=", ",", ")", "]", "}", "·", "*"].includes(text[nextIndex]);
  }

  function skipWhitespace(text, index) {
    while (index < text.length && /\s/.test(text[index])) {
      index += 1;
    }

    return index;
  }

  function normalizeReaderText(text) {
    return String(text || "")
      .replace(/\s+/g, " ")
      .trim();
  }

  function prepareSentenceAudioText(text) {
    return normalizeLatexAudioText(normalizeReaderText(text))
      .replace(EMOJI_PATTERN, "")
      .replace(DOCTYPE_TEXT_PATTERN, "DOCTYPE html")
      .replace(HTML_TAG_TEXT_PATTERN, formatHtmlTagForAudio)
      .replace(SHELL_POSITIONAL_ARG_PATTERN, "argument $1")
      .replace(PYTHON_REVERSE_SLICE_PATTERN, "$1 reverse slice")
      .replace(INDEX_ACCESS_PATTERN, "$1 index $2")
      .replace(EMPTY_BRACKETS_PATTERN, "empty list")
      .replace(BRACKETED_LIST_PATTERN, "$1")
      .replace(CITATION_LABEL_PATTERN, " ")
      .replace(SIMPLE_BRACKETS_PATTERN, "$1")
      .replace(QUOTED_CODE_TOKEN_PATTERN, "$1")
      .replace(FUNCTION_CALL_PATTERN, "$1 function")
      .replace(FUNCTION_ARGS_PATTERN, formatFunctionArgsForAudio)
      .replace(FILE_EXTENSION_PATTERN, formatFileExtensionForAudio)
      .replace(STANDALONE_EXTENSION_PATTERN, formatStandaloneExtensionForAudio)
      .replace(SPACED_ASCII_ARROW_PATTERN, ", ")
      .replace(INLINE_ARROW_PATTERN, " to ")
      .replace(LEADING_ARROW_PATTERN, "$1")
      .replace(COMPARISON_REPLACEMENTS[0][0], COMPARISON_REPLACEMENTS[0][1])
      .replace(COMPARISON_REPLACEMENTS[1][0], COMPARISON_REPLACEMENTS[1][1])
      .replace(COMPARISON_REPLACEMENTS[2][0], COMPARISON_REPLACEMENTS[2][1])
      .replace(COMPARISON_REPLACEMENTS[3][0], COMPARISON_REPLACEMENTS[3][1])
      .replace(COMPARISON_REPLACEMENTS[4][0], COMPARISON_REPLACEMENTS[4][1])
      .replace(COMPARISON_REPLACEMENTS[5][0], COMPARISON_REPLACEMENTS[5][1])
      .replace(NUMERIC_FACTORIAL_PATTERN, " factorial")
      .replace(SPACED_MULTIPLY_PATTERN, " times ")
      .replace(SPACED_PLUS_PATTERN, " plus ")
      .replace(SPACED_EQUALS_PATTERN, " equals ")
      .replace(SPACED_NUMERIC_MINUS_PATTERN, " minus ")
      .replace(DUPLICATE_COMMA_PATTERN, ",")
      .replace(SPACE_BEFORE_PUNCTUATION_PATTERN, "$1")
      .replace(/\s+/g, " ")
      .trim();
  }

  function normalizeLatexAudioText(text) {
    let output = String(text || "").replace(
      LATEX_INLINE_PATTERN,
      (match, inlineMath, displayMath) => inlineMath || displayMath || "",
    );

    LATEX_COMMAND_REPLACEMENTS.forEach(([source, replacement]) => {
      output = output.replaceAll(source, replacement);
    });

    return output.replace(LATEX_BACKSLASH_COMMAND_PATTERN, "$1");
  }

  function formatHtmlTagForAudio(match, closingSlash, tagName) {
    const readableTag = String(tagName || "").replace(/-/g, " ");
    return closingSlash ? `closing ${readableTag}` : readableTag;
  }

  function formatFileExtensionForAudio(match, stem, extension) {
    if (!CODE_FILE_EXTENSIONS.has(String(extension || "").toLowerCase())) {
      return match;
    }

    return `${stem} dot ${extension}`;
  }

  function formatFunctionArgsForAudio(match, functionName, args) {
    const readableArgs = normalizeReaderText(
      String(args || "")
        .replace(/!/g, " factorial")
        .replace(/\^/g, " to the power of "),
    );
    return `${functionName} of ${readableArgs}`;
  }

  function formatStandaloneExtensionForAudio(match, prefix, extension) {
    if (!CODE_FILE_EXTENSIONS.has(String(extension || "").toLowerCase())) {
      return match;
    }

    return `${prefix}dot ${extension}`;
  }

  function isDigit(char) {
    return /^[0-9]$/.test(char);
  }

  function isAlpha(char) {
    return /^[A-Za-z]$/.test(char);
  }

  function isAlphaNumeric(char) {
    return /^[A-Za-z0-9]$/.test(char);
  }

  function isAbbreviationTokenChar(char) {
    return /^[A-Za-z0-9_.]$/.test(char);
  }

  function createAudioId(kind, index) {
    return `${kind}-${audioReaderLevel}-${String(index).padStart(4, "0")}`;
  }

  function formatAudioLevel(value) {
    const parsed = Number.parseInt(String(value || "").trim(), 10);
    if (Number.isFinite(parsed)) {
      return String(Math.max(0, parsed)).padStart(2, "0");
    }

    const digits = String(value || "").replace(/\D+/g, "");
    return digits ? digits.padStart(2, "0") : "00";
  }

  function getAudioInventory() {
    if (!audioReaderRoot || !markdownContent || !audioReaderBaseUrl) {
      return {
        page: window.location.pathname,
        language: "",
        audioRoot: "",
        items: [],
      };
    }

    prepareAudioReader();

    return {
      page: window.location.pathname,
      language: audioReaderLanguage,
      audioRoot: audioReaderBaseUrl,
      items: [...audioItems.values()].map((item) => ({
        id: item.id,
        kind: item.kind,
        text: item.text,
        sequence: item.sequence ? [...item.sequence] : undefined,
      })),
    };
  }

  function initializeRememberedPosition() {
    if (isDirectSettingsPage()) return;

    if (preferencesApi.getPreferences().rememberPosition === "on") {
      restoreScrollPosition();
    }
  }

  function restoreScrollPosition() {
    if (window.location.hash) return;

    const positions = window.PiggyStorage?.readLocalMap(SCROLL_KEY) || {};
    const savedPosition = positions[getCurrentPageKey()];

    if (!Number.isFinite(savedPosition) || savedPosition <= 0) return;

    window.setTimeout(() => {
      window.scrollTo({
        top: savedPosition,
        behavior: shouldSuppressThemeEffects(preferencesApi.getPreferences())
          ? "auto"
          : "smooth",
      });
    }, 120);
  }

  function saveScrollPosition() {
    if (preferencesApi.getPreferences().rememberPosition !== "on") return;

    const positions = window.PiggyStorage?.readLocalMap(SCROLL_KEY) || {};
    positions[getCurrentPageKey()] = Math.max(0, Math.round(window.scrollY));
    window.PiggyStorage?.writeLocalMap(SCROLL_KEY, positions);
  }

  function saveSourceScrollPosition() {
    if (preferencesApi.getPreferences().rememberPosition !== "on") return;

    const sourceContext = settingsPageApi?.getSourceContext?.();
    if (!sourceContext?.pageKey) return;
    if (!sourceContext.capturedAt) return;
    if (!Number.isFinite(sourceContext.scrollY)) return;

    const positions = window.PiggyStorage?.readLocalMap(SCROLL_KEY) || {};
    positions[sourceContext.pageKey] = Math.max(
      0,
      Math.round(sourceContext.scrollY),
    );
    window.PiggyStorage?.writeLocalMap(SCROLL_KEY, positions);
  }

  function getCurrentPageKey() {
    return `${window.location.pathname}${window.location.search}`;
  }

  function isDirectSettingsPage() {
    return (
      Boolean(settingsPage) && settingsPage.dataset.settingsInline !== "true"
    );
  }

  function isSettingsCurrentlyActive() {
    return (
      Boolean(settingsPageApi?.isSettingsActive?.()) || isDirectSettingsPage()
    );
  }

  window.PiggyReaderRuntime = {
    initialize,
  };

  window.PiggyAudioReader = {
    getInventory: getAudioInventory,
    stop: stopAudioPlayback,
  };
})();
