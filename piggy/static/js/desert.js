// desert.js

(() => {
  let desertShaderAnimationId;
  let gl, program, startTime;
  let iTimeLocation, iResolutionLocation;

  // ---------- helpers ----------
  function createShader(gl, type, source) {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl. COMPILE_STATUS)) {
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
    // Create a 1x1 texture filled with the specified RGBA color.
    const texture = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, texture);
    const pixel = new Uint8Array(color); // e.g. [R, G, B, A]
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, pixel);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    return texture;
  }

  // ---------- shaders ----------
  const vertexShaderSource = `
  precision mediump float;
  attribute vec2 a_position;
  varying vec2 v_uv;
  void main() {
    v_uv = a_position * 0.5 + 0.5;
    gl_Position = vec4(a_position, 0.0, 1.0);
  }
  `;

  // Desert fragment shader
  // based on the following shade by klk: https://www.shadertoy.com/view/Ndy3DV
  // Attribution-ShareAlike CC License.
  const fragmentShaderSource = `

  precision mediump float;

  uniform float iTime;
  uniform vec2  iResolution;

  // ---------------- Desert palette ----------------
  const vec3 SAND_LIGHT = vec3(244.0/255.0, 231.0/255.0, 211.0/255.0);
  const vec3 SAND_TAN = vec3(210.0/255.0, 180.0/255.0, 140.0/255.0);
  const vec3 SAND_MID = vec3(184.0/255.0, 165.0/255.0, 140.0/255.0);
  const vec3 SAND_DARK = vec3(166.0/255.0, 124.0/255.0, 82.0/255.0);

  // ---------------- Original helper ----------------
  #define MAX_OCTAVES 24
  void wave(inout float x, inout float y, inout float z, float T, int octaves, float a)
  {
      float R = 8.0;
      float S = 0.03;
      float W = -0.05;
      #define RRRRS R*=0.72; S*=1.27; W*=1.21;

      for (int s = 0; s < MAX_OCTAVES; s++) {
          if (s >= octaves) break;
          float da = 1.8 + (sin(T * 0.021) * 0.1 + 0.41 * sin(float(s) * 0.71 + T * 0.02)) * a;
          float dx = cos(da);
          float dy = sin(da);
          float t  = -dot(vec2(x - 320.0, y - 240.0), vec2(dx, dy));
          float sa = sin(T * W + t * S) * R;
          float ca = cos(T * W + t * S) * R;

          x -= ca * dx * 2.0;
          y -= ca * dy * 2.0;
          z -= sa;
          RRRRS
      }
  }

  // ---------------- Main ----------------
  void mainImage( out vec4 fragColor, in vec2 fragCoord )
  {
      vec2 uv  = fragCoord / iResolution.xy * vec2(640.0, 480.0);
      vec2 uv0 = uv;

      float z = 0.0;
      wave(uv.x, uv.y, z, iTime * 15.0, 17, 1.0);

      z = (z + 22.0) * 0.018;

      float h = smoothstep(0.05, 0.95, clamp(z, 0.0, 1.0));

      vec3 col = mix(SAND_DARK, SAND_MID, h);
          col = mix(col,       SAND_TAN, h*h);
          col = mix(col,     SAND_LIGHT, h*h*h);

      fragColor = vec4(col, 1.0);
  }

  void main() {
      vec4 c;
      mainImage(c, gl_FragCoord.xy);
      gl_FragColor = c;
  }
  `;

  // ---------- runtime ----------
  function startDesertShaderAnimation() {
    const overlay = document.querySelector(".background-overlay");
    if (!overlay) {
      console.error("background-overlay element not found");
      return;
    }

    let canvas = document.getElementById("desertShader");
    if (!canvas) {
      canvas = document.createElement("canvas");
      canvas.id = "desertShader";
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

    const positionBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, positionBuffer);
    const positions = new Float32Array([
      -1, -1,  1, -1,  -1,  1,
      -1,  1,  1, -1,   1,  1
    ]);
    gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);
    const aPositionLocation = gl.getAttribLocation(program, "a_position");
    gl.enableVertexAttribArray(aPositionLocation);
    gl.vertexAttribPointer(aPositionLocation, 2, gl.FLOAT, false, 0, 0);

    iTimeLocation = gl.getUniformLocation(program, "iTime");
    iResolutionLocation = gl.getUniformLocation(program, "iResolution");
    const iChannel0Location = gl.getUniformLocation(program, "iChannel0");

    const dummyTexture = createDummyTexture(gl, [205, 170, 125, 255]);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, dummyTexture);
    gl.uniform1i(iChannel0Location, 0);

    startTime = performance.now();

    function render() {
      gl.clearColor(205/255, 170/255, 125/255, 1.0);
      gl.clear(gl.COLOR_BUFFER_BIT);

      const currentTime = performance.now();
      const elapsedTime = (currentTime - startTime) / 1000.0;
      gl.uniform1f(iTimeLocation, elapsedTime);
      gl.uniform2f(iResolutionLocation, gl.drawingBufferWidth, gl.drawingBufferHeight);

      gl.drawArrays(gl.TRIANGLES, 0, 6);
      desertShaderAnimationId = requestAnimationFrame(render);
    }
    render();
  }

  function stopDesertShaderAnimation() {
    if (desertShaderAnimationId) {
      cancelAnimationFrame(desertShaderAnimationId);
      desertShaderAnimationId = null;
    }
    const canvas = document.getElementById("desertShader");
    if (canvas) {
      canvas.remove();
    }
  }

  window.addEventListener("resize", () => {
    const canvas = document.getElementById("desertShader");
    if (canvas && gl) {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
    }
  });
  
  window.startDesertShaderAnimation = startDesertShaderAnimation;
  window.stopDesertShaderAnimation = stopDesertShaderAnimation;
})();
