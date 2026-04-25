(() => {
  let animationId = null;
  let canvas = null;
  let ctx = null;
  let stars = [];
  let lastFrameTime = 0;

  const canvasId = "space";
  const overlaySelector = ".background-overlay";

  const starCount = 220;
  const baseStarSpeed = 0.45;
  const targetFrameDuration = 1000 / 30;

  function createCanvas() {
    const overlay = document.querySelector(overlaySelector);

    if (!overlay) {
      console.error(`${overlaySelector} element not found`);
      return null;
    }

    let existingCanvas = document.getElementById(canvasId);

    if (!existingCanvas) {
      existingCanvas = document.createElement("canvas");
      existingCanvas.id = canvasId;
      existingCanvas.style.position = "absolute";
      existingCanvas.style.top = "0";
      existingCanvas.style.left = "0";
      existingCanvas.style.width = "100%";
      existingCanvas.style.height = "100%";
      existingCanvas.style.zIndex = "0";
      existingCanvas.style.pointerEvents = "none";

      overlay.appendChild(existingCanvas);
    }

    return existingCanvas;
  }

  function createStar(width, height, startAtTop = false) {
    return {
      x: Math.random() * width,
      y: startAtTop ? Math.random() * -height * 0.15 : Math.random() * height,
      radius: Math.random() * 1.35 + 0.35,
      speed: Math.random() * baseStarSpeed + 0.18,
      alpha: Math.random() * 0.55 + 0.35,
      drift: Math.random() * 0.22 - 0.11,
      twinkleOffset: Math.random() * Math.PI * 2,
    };
  }

  function resizeCanvas() {
    if (!canvas || !ctx) return;

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const width = window.innerWidth;
    const height = window.innerHeight;

    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);

    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    stars = Array.from({ length: starCount }, () => createStar(width, height));
  }

  function draw(timestamp) {
    if (!ctx || !canvas) return;

    const elapsed = timestamp - lastFrameTime;

    if (elapsed < targetFrameDuration) {
      animationId = requestAnimationFrame(draw);
      return;
    }

    lastFrameTime = timestamp;

    const width = window.innerWidth;
    const height = window.innerHeight;

    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, "#02040a");
    gradient.addColorStop(0.55, "#070b18");
    gradient.addColorStop(1, "#0b0c10");

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);

    for (const star of stars) {
      const twinkle =
        0.72 + Math.sin(timestamp * 0.0015 + star.twinkleOffset) * 0.28;
      const alpha = star.alpha * twinkle;

      ctx.beginPath();
      ctx.fillStyle = `rgba(198, 255, 250, ${alpha})`;
      ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
      ctx.fill();

      star.y += star.speed;
      star.x += star.drift;

      if (star.y > height + 4) {
        Object.assign(star, createStar(width, height, true));
        star.y = -4;
      }

      if (star.x < -4) {
        star.x = width + 4;
      } else if (star.x > width + 4) {
        star.x = -4;
      }
    }

    animationId = requestAnimationFrame(draw);
  }

  function startSpaceAnimation() {
    if (animationId) return;

    canvas = createCanvas();
    if (!canvas) return;

    ctx = canvas.getContext("2d");

    if (!ctx) {
      console.error("2D canvas context not supported");
      return;
    }

    resizeCanvas();

    lastFrameTime = performance.now();
    animationId = requestAnimationFrame(draw);
  }

  function stopSpaceAnimation() {
    if (animationId) {
      cancelAnimationFrame(animationId);
      animationId = null;
    }

    if (canvas) {
      canvas.remove();
    }

    canvas = null;
    ctx = null;
    stars = [];
    lastFrameTime = 0;
  }

  window.addEventListener("resize", resizeCanvas);

  window.startSpaceAnimation = startSpaceAnimation;
  window.stopSpaceAnimation = stopSpaceAnimation;
})();
