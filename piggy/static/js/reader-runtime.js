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
  const AUDIO_HEADING_SELECTOR = "h1, h2, h3, h4, h5, h6";
  const AUDIO_SKIP_SELECTOR = [
    "a",
    "button",
    "script",
    "style",
    "pre",
    ".highlight",
    ".MathJax",
    ".arithmatex",
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

  let preferencesApi = null;
  let settingsPageApi = null;
  let settingsPage = null;
  let readerRuler = null;
  let markdownContent = null;
  let audioReaderRoot = null;
  let audioReaderBaseUrl = "";
  let audioReaderLanguage = "";
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

    getReadableAudioBlocks(markdownContent).forEach(prepareAudioBlock);
    prepareAudioSections();
  }

  function getReadableAudioBlocks(root) {
    return [...root.querySelectorAll(AUDIO_BLOCK_SELECTOR)].filter(
      isReadableAudioBlock,
    );
  }

  function isReadableAudioBlock(element) {
    if (!(element instanceof HTMLElement)) return false;
    if (!normalizeReaderText(element.textContent)) return false;
    if (element.closest(".settings-reader-preview")) return false;
    if (element.closest(AUDIO_SKIP_SELECTOR)) return false;
    if (element.matches(AUDIO_HEADING_SELECTOR)) return false;
    if (
      element.querySelector(
        ":scope > p, :scope > ul, :scope > ol, :scope > table, :scope > pre, :scope > details, :scope > .highlight",
      )
    ) {
      return false;
    }

    return true;
  }

  function prepareAudioBlock(block) {
    if (block.dataset.readerAudioPrepared === "true") return;

    const textEntries = getAudioTextEntries(block);
    const readableText = textEntries.map((entry) => entry.text).join("");
    const normalizedBlockText = normalizeReaderText(readableText);

    if (!normalizedBlockText) return;

    const sentenceSegments = splitReaderSentences(readableText)
      .map((segment) => ({
        ...segment,
        text: normalizeReaderText(segment.text),
      }))
      .filter((segment) => segment.text);

    if (!sentenceSegments.length) {
      sentenceSegments.push({
        start: 0,
        end: readableText.length,
        text: normalizedBlockText,
      });
    }

    sentenceSegments.forEach((segment) => {
      segment.id = createAudioId("s", ++sentenceCounter, segment.text);
      audioItems.set(segment.id, {
        id: segment.id,
        kind: "sentence",
        text: segment.text,
      });
    });

    wrapAudioTextEntries(textEntries, sentenceSegments);

    const paragraphId = createAudioId(
      "p",
      ++paragraphCounter,
      normalizedBlockText,
    );
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

  function getAudioTextEntries(root) {
    const walker = document.createTreeWalker(
      root,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode(node) {
          if (!node.nodeValue) return NodeFilter.FILTER_REJECT;
          if (node.parentElement?.closest(AUDIO_SKIP_SELECTOR)) {
            return NodeFilter.FILTER_REJECT;
          }
          return NodeFilter.FILTER_ACCEPT;
        },
      },
    );

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
      });
      offset += text.length;
      node = walker.nextNode();
    }

    return entries;
  }

  function wrapAudioTextEntries(textEntries, sentenceSegments) {
    textEntries.forEach((entry) => {
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
    const headings = [...markdownContent.querySelectorAll(AUDIO_HEADING_SELECTOR)];

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

    const sectionId = createAudioId("sec", ++sectionCounter, headingText);

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
          .map((segment) => normalizeReaderText(segment.text))
          .filter(Boolean)
          .map((text) => {
            const id = createAudioId("s", ++sentenceCounter, text);
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

  function getElementAudioText(element) {
    return normalizeReaderText(
      getAudioTextEntries(element)
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

        output.push(...splitAudioSequence(element.dataset.readerAudioSentenceIds));
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

    activeAudioSource = sourceElement instanceof HTMLElement ? sourceElement : null;

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

    if (window.Intl?.Segmenter) {
      const segmenter = new Intl.Segmenter(undefined, {
        granularity: "sentence",
      });

      return [...segmenter.segment(text)]
        .map((segment) => ({
          start: segment.index,
          end: segment.index + segment.segment.length,
          text: segment.segment,
        }))
        .filter((segment) => normalizeReaderText(segment.text));
    }

    const segments = [];
    const sentencePattern = /[^.!?]+(?:[.!?]+["')\]]*)?|\S+/g;
    let match = sentencePattern.exec(text);

    while (match) {
      segments.push({
        start: match.index,
        end: match.index + match[0].length,
        text: match[0],
      });
      match = sentencePattern.exec(text);
    }

    return segments.filter((segment) => normalizeReaderText(segment.text));
  }

  function normalizeReaderText(text) {
    return String(text || "")
      .replace(/\s+/g, " ")
      .trim();
  }

  function createAudioId(kind, index, text) {
    return `${kind}-${String(index).padStart(3, "0")}-${hashReaderText(text)}`;
  }

  function hashReaderText(text) {
    const normalized = normalizeReaderText(text).toLowerCase();
    let hash = 2166136261;

    for (let i = 0; i < normalized.length; i += 1) {
      hash ^= normalized.charCodeAt(i);
      hash = Math.imul(hash, 16777619);
    }

    return (hash >>> 0).toString(36).padStart(7, "0").slice(0, 9);
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
