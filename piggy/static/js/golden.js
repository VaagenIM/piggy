// golden.js

(() => {
  let goldenShaderAnimationId;
  let gl, program, startTime;
  let iTimeLocation, iResolutionLocation;

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
    const fragmentShader = createShader(gl, gl.FRAGMENT_SHADER, fragmentShaderSource);
    const prog = gl.createProgram();
    gl.attachShader(prog, vertexShader);
    gl.attachShader(prog, fragmentShader);
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
      console.error("Program linking error:", gl.getProgramInfoLog(prog));
      gl.deleteProgram(prog);
      return null;
    }
    return prog;
  }

  function createDummyTexture(gl, color) {
    const texture = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, texture);
    const pixel = new Uint8Array(color); // e.g. [R, G, B, A]
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, pixel);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    return texture;
  }

  // Shader based on "Crazy Waves" by Alkama: https://www.shadertoy.com/view/XtsXRX
  // Changes made to make it look like a golden veil
  const vertexShaderSource = `
  precision mediump float;
  attribute vec2 a_position;
  varying vec2 v_uv;
  void main() {
    v_uv = a_position * 0.5 + 0.5;
    gl_Position = vec4(a_position, 0.0, 1.0);
  }
  `;

  const fragmentShaderSource = `
  precision mediump float;

  uniform float iTime;
  uniform vec2 iResolution;

  const float WAVE_SPEED = 0.05;

  void main() {
    vec2 uv = gl_FragCoord.xy / iResolution.xy;

    vec3 wave_color = vec3(0.0);

    float wave_width = 1.0;
    uv = -3.0 + 2.0 * uv;

    float cosT = 0.35;

    for (int k = 0; k <= 28; k++) {
      float i = float(k);
      uv.y += (0.2 + (0.2 * sin(iTime * 0.071352671) * sin(uv.x + i / 3.0 + 3.0 * (iTime * 0.25 * WAVE_SPEED * 1.137))));
      uv.x += 1.7 * sin(iTime * WAVE_SPEED * 0.8739);

      float denom = 250.0 * cosT * max(abs(uv.y), 0.0025);
      wave_width = max(0.0005, abs(0.2 / denom));

      wave_color += vec3(
        wave_width * (0.4 + ((i + 1.0) / 18.0)) * 0.75,
        wave_width * (i / 9.0) * 0.65 * 0.75,
        wave_width * ((i + 1.0) / 8.0) * 0.2 * 0.75
      );
    }

    gl_FragColor = vec4(wave_color, 1.0);
  }
  `;

  function startGoldenShaderAnimation() {
    const overlay = document.querySelector(".background-overlay");
    if (!overlay) {
      console.error("background-overlay element not found");
      return;
    }
    
    let canvas = document.getElementById("goldenShader");
    if (!canvas) {
      canvas = document.createElement("canvas");
      canvas.id = "goldenShader";
      canvas.style.position = "absolute";
      canvas.style.top = "0";
      canvas.style.left = "0";
      canvas.style.width = "100%";
      canvas.style.height = "100%";
      canvas.style.zIndex = "0";
      canvas.style.pointerEvents = "none";
      overlay.appendChild(canvas);
    }
    
    gl = canvas.getContext("webgl");
    if (!gl) {
      console.error("WebGL not supported");
      return;
    }
    
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
    
    program = createProgram(gl, vertexShaderSource, fragmentShaderSource);
    if (!program) return;
    gl.useProgram(program);
    
    // Set up a full-screen quad
    const positionBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
    const positions = new Float32Array([
      -1, -1,
      1, -1,
      -1,  1,
      -1,  1,
      1, -1,
      1,  1
    ]);
    gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);
    const aPositionLocation = gl.getAttribLocation(program, "a_position");
    gl.enableVertexAttribArray(aPositionLocation);
    gl.vertexAttribPointer(aPositionLocation, 2, gl.FLOAT, false, 0, 0);
    
    // Get uniform locations
    iTimeLocation = gl.getUniformLocation(program, "iTime");
    iResolutionLocation = gl.getUniformLocation(program, "iResolution");
    const iChannel0Location = gl.getUniformLocation(program, "iChannel0");
    
    const dummyTexture = createDummyTexture(gl, [0, 43, 54, 255]);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, dummyTexture);
    gl.uniform1i(iChannel0Location, 0);
    
    startTime = performance.now();
    
    function render() {
      gl.clearColor(0.0, 43.0/255.0, 54.0/255.0, 1.0);
      gl.clear(gl.COLOR_BUFFER_BIT);
      
      const currentTime = performance.now();
      const elapsedTime = (currentTime - startTime) / 1000.0;
      gl.uniform1f(iTimeLocation, elapsedTime);
      gl.uniform2f(iResolutionLocation, gl.drawingBufferWidth, gl.drawingBufferHeight);
      
      gl.drawArrays(gl.TRIANGLES, 0, 6);
      goldenShaderAnimationId = requestAnimationFrame(render);
    }
    render();
  }

  function stopGoldenShaderAnimation() {
    if (goldenShaderAnimationId) {
      cancelAnimationFrame(goldenShaderAnimationId);
      goldenShaderAnimationId = null;
    }
    const canvas = document.getElementById("goldenShader");
    if (canvas) {
      canvas.remove();
    }
  }

  window.addEventListener("resize", () => {
    const canvas = document.getElementById("goldenShader");
    if (canvas && gl) {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
    }
  });
  
  window.startGoldenShaderAnimation = startGoldenShaderAnimation;
  window.stopGoldenShaderAnimation = stopGoldenShaderAnimation;
})();