// H5P iframe Resizer
(function () {
  if (!window.postMessage || !window.addEventListener || window.h5pResizerInitialized) {
    return; // Not supported
  }
  window.h5pResizerInitialized = true;

  var h5pThemeVariables = {
    '--h5p-theme-alternative-base': '--piggy-main',
    '--h5p-theme-alternative-dark': '--piggy-dark',
    '--h5p-theme-alternative-light': '--piggy-light',
    '--h5p-theme-contrast-cta': '--piggy-text-button',
    '--h5p-theme-contrast-cta-white': '--piggy-light',
    '--h5p-theme-font-name': '--piggy-ui-font-family',
    '--h5p-theme-font-size-m': 'calc(1rem * var(--piggy-font-scale))',
    '--h5p-theme-font-size-xl': 'calc(1.25rem * var(--piggy-font-scale))',
    '--h5p-theme-main-cta-base': '--piggy-button',
    '--h5p-theme-spacing-l': 'calc(1.5rem * var(--piggy-font-scale))',
    '--h5p-theme-spacing-m': 'calc(1rem * var(--piggy-font-scale))',
    '--h5p-theme-spacing-s': 'calc(0.5rem * var(--piggy-font-scale))',
    '--h5p-theme-spacing-xs': 'calc(0.25rem * var(--piggy-font-scale))',
    '--h5p-theme-stroke-1': '--piggy-button-border',
    '--h5p-theme-text-primary': '--piggy-text-main',
    '--h5p-theme-text-secondary': '--piggy-text-neutral',
    '--h5p-theme-text-third': '--piggy-text-neutral',
    '--h5p-theme-ui-base': '--piggy-light',
    '--h5p-theme-border-radius-medium': 'calc(0.25rem * var(--piggy-font-scale))',
    '--h5p-theme-border-radius-large': 'calc(0.5rem * var(--piggy-font-scale))'
  };

  var getPiggyTheme = function () {
    var computedStyle = getComputedStyle(document.documentElement);
    var variables = {};

    for (var i = 0; i < computedStyle.length; i++) {
      var name = computedStyle[i];
      if (name.indexOf('--piggy-') === 0) {
        variables[name] = computedStyle.getPropertyValue(name).trim();
      }
    }

    return variables;
  };

  var isH5PIframe = function (iframe) {
    if (iframe.src.indexOf('h5p') !== -1) {
      return true;
    }

    try {
      return iframe.contentDocument?.documentElement.classList.contains('h5p-iframe');
    }
    catch (error) {
      return false;
    }
  };

  var handleIframeLoad = function (iframe) {
    if (isH5PIframe(iframe)) {
      iframe.contentWindow.postMessage({
        context: 'h5p',
        action: 'ready'
      }, '*');
      applyThemeToH5PIframes();
    }
  };

  var applyTheme = function (iframe, variables) {
    var theme = {
      type: 'h5p-theme',
      variables: variables
    };

    // Same-origin H5P files can be themed immediately, without waiting for
    // the embedded document to implement a message handler.
    try {
      var root = iframe.contentDocument?.documentElement;
      if (root) {
        Object.keys(variables).forEach(function (name) {
          root.style.setProperty(name, variables[name]);
        });
        Object.keys(h5pThemeVariables).forEach(function (name) {
          var value = h5pThemeVariables[name];
          if (value.indexOf('--') === 0 && !variables[value]) {
            return;
          }
          root.style.setProperty(name, value.indexOf('--') === 0 ? 'var(' + value + ')' : value);
        });
      }
      var documentRoot = iframe.contentDocument;
      if (documentRoot) {
        documentRoot.documentElement.setAttribute(
          'data-piggy-theme',
          document.documentElement.getAttribute('data-theme') || ''
        );
        var style = documentRoot.getElementById('piggy-h5p-theme');
        if (!style) {
          style = documentRoot.createElement('style');
          style.id = 'piggy-h5p-theme';
          documentRoot.head.appendChild(style);
        }
        style.textContent =
          'html.h5p-iframe,html.h5p-iframe body{background:var(--piggy-main)!important;color:var(--piggy-text-main)!important;font-family:var(--piggy-ui-font-family)!important}' +
          '.h5p-content,.h5p-content .intro-page,.h5p-content .questionset,.h5p-content .questionset-results{background:var(--piggy-main)!important;border-color:var(--piggy-card-border)!important;color:var(--piggy-text-main)!important}' +
          '.h5p-content,.h5p-content p,.h5p-content h1,.h5p-content h2,.h5p-content h3,.h5p-content h4,.h5p-content h5,.h5p-content h6{color:var(--piggy-text-main)}' +
          '.h5p-content .intro-page .title>h1{display:table;margin-left:auto;margin-right:auto;background:var(--piggy-header-bg-h1)!important;color:var(--piggy-content-h1)!important;padding:calc(.55rem * var(--piggy-font-scale)) calc(1rem * var(--piggy-font-scale))!important;border-radius:calc(.5rem * var(--piggy-font-scale))!important;box-shadow:none!important}' +
          '.h5p-content .intro-page .introduction{background:var(--piggy-card-end)!important;color:var(--piggy-text-card,var(--piggy-text-main))!important;padding:calc(.75rem * var(--piggy-font-scale)) calc(1rem * var(--piggy-font-scale))!important;border:1px solid var(--piggy-card-border)!important;border-radius:calc(.5rem * var(--piggy-font-scale))!important;box-shadow:0 2px 8px var(--piggy-shadow-box)!important}' +
          '.h5p-content .questionset-results .result-header{color:var(--piggy-content-h1)!important}' +
          '.h5p-content button,.h5p-content .h5p-joubelui-button,.h5p-content .joubel-button,.h5p-content .h5p-core-button,.h5p-content .h5p-question-check-answer,.h5p-content .h5p-question-next,.h5p-content .h5p-question-prev{background:var(--piggy-button)!important;border-color:var(--piggy-button-border)!important;color:var(--piggy-text-button,var(--piggy-light))!important}' +
          '.h5p-content button:hover,.h5p-content .h5p-joubelui-button:hover,.h5p-content .joubel-button:hover,.h5p-content .h5p-core-button:hover{background:var(--piggy-button-hover)!important}' +
          '.h5p-content .h5p-question{background:var(--piggy-card-start)!important;border:1px solid var(--piggy-card-border)!important;border-radius:calc(.5rem * var(--piggy-font-scale)) calc(.5rem * var(--piggy-font-scale)) 0 0!important;padding:calc(1rem * var(--piggy-font-scale))!important;color:var(--piggy-text-card,var(--piggy-text-main));box-shadow:0 2px 8px var(--piggy-shadow-box)!important}' +
          '.h5p-content .h5p-multichoice>.h5p-question{background:linear-gradient(180deg,var(--piggy-card-start),var(--piggy-card-end))!important}' +
          '.h5p-content .h5p-multichoice .h5p-alternative-container{background:var(--piggy-card-end)!important;border-color:var(--piggy-card-border)!important;box-shadow:0 .1em 0 var(--piggy-shadow-box)!important;color:var(--piggy-text-card,var(--piggy-text-main))}' +
          '.h5p-content .h5p-multichoice .h5p-answer:not([aria-disabled=true]):hover .h5p-alternative-container{background:var(--piggy-card-start)!important}' +
          '.h5p-content .h5p-multichoice .h5p-answer[aria-checked=true] .h5p-alternative-container{background:var(--piggy-button-active)!important;border-color:var(--piggy-button-border)!important;color:var(--piggy-button-active-text,var(--piggy-text-button,var(--piggy-light)))!important;box-shadow:none!important}' +
          '.h5p-content .h5p-multichoice .h5p-answer.h5p-correct .h5p-alternative-container{background:var(--piggy-admonition-success-bg,var(--piggy-card-end))!important;color:var(--piggy-admonition-success-text,var(--piggy-text-main))}' +
          '.h5p-content .h5p-multichoice .h5p-answer.h5p-wrong .h5p-alternative-container{background:var(--piggy-admonition-danger-bg,var(--piggy-card-end))!important;color:var(--piggy-admonition-danger-text,var(--piggy-text-main))}' +
          '.h5p-content .h5p-drag-draggables-container{background:var(--piggy-card-start)!important;border:1px solid var(--piggy-card-border)!important;border-radius:calc(.35rem * var(--piggy-font-scale))!important;padding:calc(.5rem * var(--piggy-font-scale))!important}' +
          '.h5p-content .h5p-drag-text [aria-grabbed]{background:var(--piggy-button-active)!important;border:1px solid var(--piggy-button-border)!important;border-radius:calc(.35rem * var(--piggy-font-scale))!important;color:var(--piggy-button-active-text,var(--piggy-text-button,var(--piggy-light)))!important;box-shadow:0 2px 4px var(--piggy-shadow-box)!important}' +
          '.h5p-content .h5p-drag-text [aria-grabbed]:hover,.h5p-content .h5p-drag-text [aria-grabbed=true]{background:var(--piggy-button-hover)!important}' +
          '.h5p-content .h5p-drag-text [aria-dropeffect]{background:var(--piggy-card-end)!important;border:1px dashed var(--piggy-card-border)!important;border-radius:calc(.35rem * var(--piggy-font-scale))!important;color:var(--piggy-text-card,var(--piggy-text-main))!important}' +
          '.h5p-content .h5p-drag-text .h5p-drag-dropzone-container{background:var(--piggy-card-start)!important;border:1px solid var(--piggy-card-border)!important;border-radius:calc(.35rem * var(--piggy-font-scale))!important;padding:calc(.15rem * var(--piggy-font-scale)) calc(.25rem * var(--piggy-font-scale))!important;color:var(--piggy-text-card,var(--piggy-text-main))!important}' +
          '.h5p-content .h5p-drag-text .ui-droppable-hover{background:var(--piggy-button-hover)!important}' +
          '.h5p-content .h5p-drag-text [aria-dropeffect].h5p-drag-correct-feedback{background:var(--piggy-admonition-success-bg)!important;border-color:var(--piggy-admonition-success-border)!important}.h5p-content .h5p-drag-text [aria-dropeffect].h5p-drag-wrong-feedback{background:var(--piggy-admonition-danger-bg)!important;border-color:var(--piggy-admonition-danger-border)!important}' +
          '.h5p-content .h5p-drag-text [aria-grabbed].h5p-drag-dropped{background:var(--piggy-card-end)!important;border-color:var(--piggy-card-border)!important;color:var(--piggy-text-card,var(--piggy-text-main))!important}' +
          '.h5p-content .h5p-drag-text .h5p-drag-dropped.h5p-drag-draggable-correct{color:var(--piggy-admonition-success-text)!important}.h5p-content .h5p-drag-text .h5p-drag-dropped.h5p-drag-draggable-wrong{color:var(--piggy-admonition-danger-text)!important}' +
          '.h5p-content .h5p-multichoice .h5p-answer .h5p-alternative-container:before,.h5p-content .h5p-multichoice .h5p-radio-or-checkbox{color:var(--piggy-text-card,var(--piggy-text-main))}' +
          '.h5p-content .h5p-multichoice .h5p-correct .h5p-answer-icon:before{color:var(--piggy-admonition-success-text,var(--piggy-text-main))}.h5p-content .h5p-multichoice .h5p-wrong .h5p-answer-icon:before{color:var(--piggy-admonition-danger-text,var(--piggy-text-main))}' +
          '.h5p-content .h5p-multichoice .feedback-text,.h5p-content .h5p-multichoice .feedback-text.h5p-passed{color:var(--piggy-admonition-success-text,var(--piggy-text-main))}.h5p-content .h5p-multichoice .feedback-text.h5p-failed{color:var(--piggy-admonition-danger-text,var(--piggy-text-main))}' +
          '.h5p-content .h5p-true-false-answer{background:var(--piggy-card-end)!important;border:2px solid var(--piggy-card-border)!important;border-radius:calc(.35rem * var(--piggy-font-scale))!important;color:var(--piggy-text-card,var(--piggy-text-main))!important;box-shadow:0 2px 4px var(--piggy-shadow-box)!important}' +
          '.h5p-content .h5p-true-false-answer:hover,.h5p-content .h5p-true-false-answer:focus{background:var(--piggy-card-start)!important;border-color:var(--piggy-button-hover)!important;box-shadow:0 0 0 2px var(--piggy-button-focus,var(--piggy-button-hover))!important}' +
          '.h5p-content .h5p-true-false-answer[aria-checked=true]{background:var(--piggy-button-active)!important;border-color:var(--piggy-button-border)!important;color:var(--piggy-button-active-text,var(--piggy-text-button,var(--piggy-light)))!important}' +
          '.h5p-content .h5p-true-false-answer.correct{background:var(--piggy-admonition-success-bg)!important;border-color:var(--piggy-admonition-success-border)!important;color:var(--piggy-admonition-success-text)!important;box-shadow:none!important}' +
          '.h5p-content .h5p-true-false-answer.wrong{background:var(--piggy-admonition-danger-bg)!important;border-color:var(--piggy-admonition-danger-border)!important;color:var(--piggy-admonition-danger-text)!important;box-shadow:none!important}' +
          '.h5p-content .h5p-true-false-answer.correct:after{background:var(--piggy-admonition-success-border)!important;color:var(--piggy-admonition-success-text)!important}.h5p-content .h5p-true-false-answer.wrong:after{background:var(--piggy-admonition-danger-border)!important;color:var(--piggy-admonition-danger-text)!important}' +
          '.h5p-content .dots-container{line-height:2.5em!important;padding:calc(.3rem * var(--piggy-font-scale)) calc(.5rem * var(--piggy-font-scale))!important;background:var(--piggy-card-end)!important;border:1px solid var(--piggy-card-border)!important;border-radius:0 0 calc(.35rem * var(--piggy-font-scale)) calc(.35rem * var(--piggy-font-scale))!important}.h5p-content .progress-dot{width:.7em!important;height:.7em!important;border:2px solid var(--piggy-card-border)!important;background:transparent!important}.h5p-content .progress-dot.answered{background:var(--piggy-button-active)!important;border-color:var(--piggy-button-active)!important}.h5p-content .progress-dot.current:before{border-color:var(--piggy-button-hover)!important}' +
          '.h5p-content .h5p-question-feedback-container,.h5p-content .h5p-question-feedback-content,.h5p-content .h5p-question-explanation-container,.h5p-content .feedback-section{background:var(--piggy-card-end)!important;color:var(--piggy-text-main)!important;border-color:var(--piggy-card-border)!important}' +
          '.h5p-content a{color:var(--piggy-text-hyperlink,var(--piggy-button))!important}' +
          'html[data-piggy-theme="high-contrast"] .h5p-content .h5p-drag-draggables-container{background:var(--piggy-main)!important;border:2px solid var(--piggy-card-border)!important}' +
          'html[data-piggy-theme="high-contrast"] .h5p-content .h5p-drag-text [aria-grabbed]{background:var(--piggy-content-h2)!important;border:2px solid var(--piggy-card-border)!important;color:var(--piggy-main)!important;box-shadow:none!important}' +
          'html[data-piggy-theme="high-contrast"] .h5p-content .h5p-drag-text [aria-grabbed]:hover,html[data-piggy-theme="high-contrast"] .h5p-content .h5p-drag-text [aria-grabbed=true]{background:var(--piggy-content-h2)!important;color:var(--piggy-main)!important}' +
          'html[data-piggy-theme="high-contrast"] .h5p-content .h5p-true-false-answer{background:var(--piggy-content-h2)!important;border:2px solid var(--piggy-card-border)!important;color:var(--piggy-main)!important;box-shadow:none!important}' +
          'html[data-piggy-theme="high-contrast"] .h5p-content .h5p-true-false-answer:hover,html[data-piggy-theme="high-contrast"] .h5p-content .h5p-true-false-answer:focus{background:var(--piggy-content-h2)!important;color:var(--piggy-main)!important}' +
          'html[data-piggy-theme="high-contrast"] .h5p-content .h5p-true-false-answer[aria-checked=true]{background:var(--piggy-content-h2)!important;border-color:var(--piggy-button-focus)!important;color:var(--piggy-main)!important}' +
          'html[data-piggy-theme="high-contrast"] .h5p-content .h5p-true-false-answer.correct{background:var(--piggy-main)!important;border-color:var(--piggy-admonition-success-border)!important;color:var(--piggy-light)!important}' +
          'html[data-piggy-theme="high-contrast"] .h5p-content .h5p-true-false-answer.wrong{background:var(--piggy-main)!important;border-color:var(--piggy-admonition-danger-border)!important;color:var(--piggy-light)!important}' +
          'html[data-piggy-theme="high-contrast"] .h5p-content .dots-container{background:var(--piggy-main)!important;border:2px solid var(--piggy-card-border)!important}' +
          'html[data-piggy-theme="high-contrast"] .h5p-content .progress-dot{border:3px solid var(--piggy-card-border)!important;background:transparent!important}' +
          'html[data-piggy-theme="high-contrast"] .h5p-content .progress-dot.answered{background:var(--piggy-content-h2)!important;border-color:var(--piggy-card-border)!important}' +
          'html[data-piggy-theme="high-contrast"] .h5p-content .progress-dot.current{background:transparent!important;border-color:var(--piggy-button-focus)!important}' +
          'html[data-piggy-theme="high-contrast"] .h5p-content .progress-dot.current.answered{background:var(--piggy-content-h2)!important}' +
          'html[data-piggy-theme="high-contrast"] .h5p-content .progress-dot.current:before{border-color:var(--piggy-button-focus)!important}';
      }
    }
    catch (error) {
      // Cross-origin frames still receive the theme through postMessage.
    }

    if (iframe.contentWindow) {
      iframe.contentWindow.postMessage(theme, '*');
    }
  };

  var applyThemeToH5PIframes = function () {
    var variables = getPiggyTheme();
    var iframes = document.getElementsByTagName('iframe');

    for (var i = 0; i < iframes.length; i++) {
      if (isH5PIframe(iframes[i])) {
        applyTheme(iframes[i], variables);
      }
    }
  };

  // Map actions to handlers
  var actionHandlers = {};

  /**
   * Prepare iframe resize.
   *
   * @private
   * @param {Object} iframe Element
   * @param {Object} data Payload
   * @param {Function} respond Send a response to the iframe
   */
  actionHandlers.hello = function (iframe, data, respond) {
    // Make iframe responsive
    iframe.style.width = '100%';

    // Bugfix for Chrome: Force update of iframe width. If this is not done the
    // document size may not be updated before the content resizes.
    iframe.getBoundingClientRect();

    // Tell iframe that it needs to resize when our window resizes
    var resize = function () {
      if (iframe.contentWindow) {
        // Limit resize calls to avoid flickering
        respond('resize');
      }
      else {
        // Frame is gone, unregister.
        window.removeEventListener('resize', resize);
      }
    };
    window.addEventListener('resize', resize, false);

    // Respond to let the iframe know we can resize it
    respond('hello');
  };

  /**
   * Prepare iframe resize.
   *
   * @private
   * @param {Object} iframe Element
   * @param {Object} data Payload
   * @param {Function} respond Send a response to the iframe
   */
  actionHandlers.prepareResize = function (iframe, data, respond) {
    // Do not resize unless page and scrolling differs
    if (iframe.clientHeight !== data.scrollHeight ||
        data.scrollHeight !== data.clientHeight) {

      // Reset iframe height, in case content has shrinked.
      iframe.style.height = data.clientHeight + 'px';
      respond('resizePrepared');
    }
  };

  /**
   * Resize parent and iframe to desired height.
   *
   * @private
   * @param {Object} iframe Element
   * @param {Object} data Payload
   * @param {Function} respond Send a response to the iframe
   */
  actionHandlers.resize = function (iframe, data) {
    // Resize iframe so all content is visible. Use scrollHeight to make sure we get everything
    iframe.style.height = data.scrollHeight + 'px';
  };

  /**
   * Keyup event handler. Exits full screen on escape.
   *
   * @param {Event} event
   */
  var escape = function (event) {
    if (event.keyCode === 27) {
      exitFullScreen();
    }
  };

  // Listen for messages from iframes
  window.addEventListener('message', function receiveMessage(event) {
    if (event.data.context !== 'h5p') {
      return; // Only handle h5p requests.
    }

    // Find out who sent the message
    var iframe, iframes = document.getElementsByTagName('iframe');
    for (var i = 0; i < iframes.length; i++) {
      if (iframes[i].contentWindow === event.source) {
        iframe = iframes[i];
        break;
      }
    }

    if (!iframe) {
      return; // Cannot find sender
    }

    // Find action handler handler
    if (actionHandlers[event.data.action]) {
      actionHandlers[event.data.action](iframe, event.data, function respond(action, data) {
        if (data === undefined) {
          data = {};
        }
        data.action = action;
        data.context = 'h5p';
        event.source.postMessage(data, event.origin);
      });
    }
  }, false);

  // Let h5p iframes know we're ready!
  var iframes = document.getElementsByTagName('iframe');
  var ready = {
    context: 'h5p',
    action: 'ready'
  };
  for (var i = 0; i < iframes.length; i++) {
    iframes[i].addEventListener('load', function () {
      handleIframeLoad(this);
    }, false);
    if (isH5PIframe(iframes[i])) {
      iframes[i].contentWindow.postMessage(ready, '*');
    }
  }

  applyThemeToH5PIframes();
  new MutationObserver(applyThemeToH5PIframes).observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['class', 'style', 'data-theme', 'data-theme-type']
  });

})();
