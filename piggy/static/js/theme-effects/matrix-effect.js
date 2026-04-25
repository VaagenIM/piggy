(() => {
  let animationId = null;
  let canvas = null;
  let ctx = null;
  let drops = [];
  let lastFrameTime = 0;

  const canvasId = "matrix";
  const overlaySelector = ".background-overlay";

  const fontSize = 16;
  const columnSpacing = fontSize * 0.8;
  const targetFrameDuration = 1000 / 30;

  const characters =
    '日ｦｲｸｺｿﾁﾄﾉﾌﾔﾖﾙﾚﾛﾝ012345789Z:・."=*+-<></>¦｜╌çﾘｸ二コソヤｦｱｳｴｵｶｷｹｺｻｼｽｾｿﾀﾂﾃﾅﾆﾇﾈﾊﾋﾎﾏﾐﾑﾒﾓﾔﾕﾗﾘﾜ';

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
    ctx.font = `${fontSize}px monospace`;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";

    const columns = Math.ceil(width / columnSpacing);

    drops = Array.from({ length: columns }, () =>
      Math.floor(Math.random() * (height / fontSize)),
    );
  }

  function getRandomCharacter() {
    const index = Math.floor(Math.random() * characters.length);
    return characters[index];
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

    ctx.fillStyle = "rgba(0, 12, 0, 0.035)";
    ctx.fillRect(0, 0, width, height);

    ctx.fillStyle = "rgba(0, 190, 70, 0.70)";
    ctx.shadowColor = "rgba(0, 255, 120, 0.35)";
    ctx.shadowBlur = 6;

    for (let i = 0; i < drops.length; i++) {
      const text = getRandomCharacter();

      const x = i * columnSpacing + columnSpacing / 2;
      const y = drops[i] * fontSize;

      ctx.save();
      ctx.translate(x, y);
      ctx.scale(-1, 1);

      ctx.shadowColor = "rgba(0, 255, 120, 0.45)";
      ctx.shadowBlur = 7;

      ctx.fillStyle = "rgba(0, 255, 90, 0.18)";
      ctx.font = `${fontSize + 2}px monospace`;
      ctx.fillText(text, 0, 0);

      ctx.fillStyle = "rgba(0, 210, 80, 0.82)";
      ctx.font = `${fontSize}px monospace`;
      ctx.fillText(text, 0, 0);

      ctx.restore();

      if (y > height && Math.random() > 0.975) {
        drops[i] = 0;
      }

      drops[i]++;
    }

    ctx.shadowBlur = 0;

    animationId = requestAnimationFrame(draw);
  }

  function startMatrixAnimation() {
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

  function stopMatrixAnimation() {
    if (animationId) {
      cancelAnimationFrame(animationId);
      animationId = null;
    }

    if (canvas) {
      canvas.remove();
    }

    canvas = null;
    ctx = null;
    drops = [];
    lastFrameTime = 0;
  }

  window.addEventListener("resize", resizeCanvas);

  window.startMatrixAnimation = startMatrixAnimation;
  window.stopMatrixAnimation = stopMatrixAnimation;
})();
