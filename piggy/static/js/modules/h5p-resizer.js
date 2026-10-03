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

  var copyFontStylesheets = function (documentRoot) {
    var links = document.querySelectorAll('link[rel="stylesheet"]');

    for (var i = 0; i < links.length; i++) {
      var href = links[i].href;
      if (href.indexOf('fonts.googleapis.com') === -1 && href.indexOf('/css/fonts/') === -1) {
        continue;
      }
      if (documentRoot.querySelector('link[data-piggy-font][href="' + href + '"]')) {
        continue;
      }
      var link = documentRoot.createElement('link');
      link.rel = 'stylesheet';
      link.href = href;
      link.setAttribute('data-piggy-font', '');
      documentRoot.head.appendChild(link);
    }
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

  var fitIframeToContent = function (iframe) {
    try {
      var documentRoot = iframe.contentDocument;
      var content = documentRoot && documentRoot.querySelector('.h5p-content');
      if (!content) {
        return;
      }
      var scroller = documentRoot.scrollingElement || documentRoot.documentElement;
      var height = Math.ceil(content.getBoundingClientRect().bottom + scroller.scrollTop);
      if (height > 0) {
        iframe.style.height = height + 'px';
        scroller.scrollTop = 0;
      }
    }
    catch (error) {
      // Cross-origin frames keep the height H5P asked for.
    }
  };

  var observeContentSize = function (iframe) {
    if (iframe.piggyContentObserver) {
      return;
    }
    try {
      var content = iframe.contentDocument.querySelector('.h5p-content');
      if (!content || !iframe.contentWindow.ResizeObserver) {
        return;
      }
      iframe.piggyContentObserver = new iframe.contentWindow.ResizeObserver(function () {
        fitIframeToContent(iframe);
      });
      iframe.piggyContentObserver.observe(content);
    }
    catch (error) {
      // Cross-origin frames are resized by H5P's messages only.
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

    // Lets the page give the quiz frame spacing (see h5p.css).
    iframe.classList.add('piggy-h5p-frame');
    observeContentSize(iframe);

    // Same-origin H5P files can be themed immediately, without waiting for
    // the embedded document to implement a message handler.
    try {
      var root = iframe.contentDocument?.documentElement;
      if (root) {
        // Drop variables the new theme doesn't define
        for (var i = root.style.length - 1; i >= 0; i--) {
          var property = root.style[i];
          if (property.indexOf('--piggy-') === 0 && !(property in variables)) {
            root.style.removeProperty(property);
          }
        }
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
        var pageRoot = document.documentElement;
        var pageStyle = getComputedStyle(pageRoot);

        documentRoot.documentElement.setAttribute(
          'data-piggy-theme',
          pageRoot.getAttribute('data-theme') || ''
        );

        documentRoot.documentElement.style.fontSize = pageStyle.fontSize;
        documentRoot.documentElement.style.colorScheme = pageStyle.colorScheme;
        copyFontStylesheets(documentRoot);

        var link = documentRoot.getElementById('piggy-h5p-theme');
        if (!link) {
          link = documentRoot.createElement('link');
          link.id = 'piggy-h5p-theme';
          link.rel = 'stylesheet';
          documentRoot.head.appendChild(link);
        }
        link.href = '/static/css/components/h5p.css';
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
    fitIframeToContent(iframe);
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
  var themeUpdateQueued = false;
  new MutationObserver(function () {
    if (themeUpdateQueued) {
      return;
    }
    themeUpdateQueued = true;
    requestAnimationFrame(function () {
      themeUpdateQueued = false;
      applyThemeToH5PIframes();
    });
  }).observe(document.documentElement, {
    attributes: true
  });

})();
