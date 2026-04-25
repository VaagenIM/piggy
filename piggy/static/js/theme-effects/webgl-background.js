(() => {
  const DEFAULT_VERTEX_SHADER_SOURCE = `
  precision mediump float;

  attribute vec2 a_position;
  varying vec2 v_uv;

  void main() {
    v_uv = a_position * 0.5 + 0.5;
    gl_Position = vec4(a_position, 0.0, 1.0);
  }
  `;

  function createShader(gl, type, source) {
    const shader = gl.createShader(type);

    gl.shaderSource(shader, source);
    gl.compileShader(shader);

    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      console.error("Shader compile error:", gl.getShaderInfoLog(shader));
      gl.deleteShader(shader);
      return null;
    }

    return shader;
  }

  function createProgram(gl, vertexShaderSource, fragmentShaderSource) {
    const vertexShader = createShader(gl, gl.VERTEX_SHADER, vertexShaderSource);
    const fragmentShader = createShader(
      gl,
      gl.FRAGMENT_SHADER,
      fragmentShaderSource,
    );

    if (!vertexShader || !fragmentShader) {
      return null;
    }

    const program = gl.createProgram();

    gl.attachShader(program, vertexShader);
    gl.attachShader(program, fragmentShader);
    gl.linkProgram(program);

    gl.deleteShader(vertexShader);
    gl.deleteShader(fragmentShader);

    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.error("Program linking error:", gl.getProgramInfoLog(program));
      gl.deleteProgram(program);
      return null;
    }

    return program;
  }

  function createDummyTexture(gl, color) {
    const texture = gl.createTexture();

    gl.bindTexture(gl.TEXTURE_2D, texture);

    const pixel = new Uint8Array(color);

    gl.texImage2D(
      gl.TEXTURE_2D,
      0,
      gl.RGBA,
      1,
      1,
      0,
      gl.RGBA,
      gl.UNSIGNED_BYTE,
      pixel,
    );

    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);

    return texture;
  }

  function resizeCanvasToWindow(canvas, gl) {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
  }

  function createCanvas({ canvasId, overlaySelector }) {
    const overlay = document.querySelector(overlaySelector);

    if (!overlay) {
      console.error(`${overlaySelector} element not found`);
      return null;
    }

    let canvas = document.getElementById(canvasId);

    if (!canvas) {
      canvas = document.createElement("canvas");
      canvas.id = canvasId;
      canvas.style.position = "absolute";
      canvas.style.top = "0";
      canvas.style.left = "0";
      canvas.style.width = "100%";
      canvas.style.height = "100%";
      canvas.style.zIndex = "0";
      canvas.style.pointerEvents = "none";

      overlay.appendChild(canvas);
    }

    return canvas;
  }

  function create({
    canvasId,
    fragmentShaderSource,
    vertexShaderSource = DEFAULT_VERTEX_SHADER_SOURCE,
    overlaySelector = ".background-overlay",
    clearColor = [0, 0, 0, 1],
    dummyTextureColor = [0, 0, 0, 255],
  }) {
    let animationId = null;
    let canvas = null;
    let gl = null;
    let program = null;
    let startTime = null;

    let iTimeLocation = null;
    let iResolutionLocation = null;

    function start() {
      if (animationId) return;

      canvas = createCanvas({ canvasId, overlaySelector });
      if (!canvas) return;

      gl = canvas.getContext("webgl");

      if (!gl) {
        console.error("WebGL not supported");
        return;
      }

      resizeCanvasToWindow(canvas, gl);

      program = createProgram(gl, vertexShaderSource, fragmentShaderSource);
      if (!program) return;

      gl.useProgram(program);

      const positionBuffer = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);

      const positions = new Float32Array([
        -1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1,
      ]);

      gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);

      const aPositionLocation = gl.getAttribLocation(program, "a_position");

      gl.enableVertexAttribArray(aPositionLocation);
      gl.vertexAttribPointer(aPositionLocation, 2, gl.FLOAT, false, 0, 0);

      iTimeLocation = gl.getUniformLocation(program, "iTime");
      iResolutionLocation = gl.getUniformLocation(program, "iResolution");

      const iChannel0Location = gl.getUniformLocation(program, "iChannel0");

      if (iChannel0Location !== null) {
        const dummyTexture = createDummyTexture(gl, dummyTextureColor);

        gl.activeTexture(gl.TEXTURE0);
        gl.bindTexture(gl.TEXTURE_2D, dummyTexture);
        gl.uniform1i(iChannel0Location, 0);
      }

      startTime = performance.now();

      render();
    }

    function render() {
      if (!gl || !program) return;

      gl.clearColor(clearColor[0], clearColor[1], clearColor[2], clearColor[3]);
      gl.clear(gl.COLOR_BUFFER_BIT);

      const currentTime = performance.now();
      const elapsedTime = (currentTime - startTime) / 1000.0;

      if (iTimeLocation) {
        gl.uniform1f(iTimeLocation, elapsedTime);
      }

      if (iResolutionLocation) {
        gl.uniform2f(
          iResolutionLocation,
          gl.drawingBufferWidth,
          gl.drawingBufferHeight,
        );
      }

      gl.drawArrays(gl.TRIANGLES, 0, 6);

      animationId = requestAnimationFrame(render);
    }

    function stop() {
      if (animationId) {
        cancelAnimationFrame(animationId);
        animationId = null;
      }

      if (canvas) {
        canvas.remove();
      }

      canvas = null;
      gl = null;
      program = null;
      startTime = null;
      iTimeLocation = null;
      iResolutionLocation = null;
    }

    function resize() {
      if (!canvas || !gl) return;
      resizeCanvasToWindow(canvas, gl);
    }

    window.addEventListener("resize", resize);

    return {
      start,
      stop,
      resize,
    };
  }

  window.PiggyWebGLBackground = {
    create,
  };
})();
