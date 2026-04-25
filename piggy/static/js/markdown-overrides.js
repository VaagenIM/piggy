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
