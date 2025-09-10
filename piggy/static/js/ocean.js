// ocean.js

(() => {
  let oceanShaderAnimationId;
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

  // Shader based on "A simple water shader." by Ajarus, viktor@ajarus.com.
  //
  // Attribution-ShareAlike CC License.
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
  #define PI 3.1415926535897932

  // Water shader parameters
  const float speed = 0.1;
  const float speed_x = 0.02;
  const float speed_y = 0.02;

  const float emboss = 0.5;
  const float intensity = 3.0;
  const int steps = 10;
  const float frequency = 5.0;
  const int angle = 7;

  const float delta = 60.0;
  const float gain = 700.0;
  const float reflectionCutOff = 0.015;
  const float reflectionIntensity = 2000000.0;

  uniform float iTime;
  uniform vec2 iResolution;
  uniform sampler2D iChannel0;

  float col(vec2 coord, float time) {
    float delta_theta = 2.0 * PI / float(angle);
    float c = 0.0;
    float theta = 0.0;
    for (int i = 0; i < steps; i++) {
      vec2 adjc = coord;
      theta = delta_theta * float(i);
      adjc.x += cos(theta) * time * speed + time * speed_x;
      adjc.y -= sin(theta) * time * speed - time * speed_y;
      c += cos((adjc.x * cos(theta) - adjc.y * sin(theta)) * frequency) * intensity;
    }
    return cos(c);
  }

  void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    float time = iTime * 1.3;
    vec2 p = fragCoord.xy / iResolution.xy;
    vec2 c1 = p;
    vec2 c2 = p;
    float cc1 = col(c1, time);
    
    c2.x += iResolution.x / delta;
    float dx = emboss * (cc1 - col(c2, time)) / delta;
    
    c2.x = p.x;
    c2.y += iResolution.y / delta;
    float dy = emboss * (cc1 - col(c2, time)) / delta;
    
    c1.x += dx * 2.0;
    c1.y = -(c1.y + dy * 2.0);
    
    float alpha = 1.0 + (dx * dy) * gain;
    float ddx = dx - reflectionCutOff;
    float ddy = dy - reflectionCutOff;
    if (ddx > 0.0 && ddy > 0.0) {
      alpha = pow(alpha, ddx * ddy * reflectionIntensity);
    }
    
    vec4 colr = texture2D(iChannel0, c1) * alpha;
    fragColor = colr;
  }

  void main() {
    mainImage(gl_FragColor, gl_FragCoord.xy);
  }
  `;

  function startOceanShaderAnimation() {
    const overlay = document.querySelector(".background-overlay");
    if (!overlay) {
      console.error("background-overlay element not found");
      return;
    }
    
    let canvas = document.getElementById("oceanShader");
    if (!canvas) {
      canvas = document.createElement("canvas");
      canvas.id = "oceanShader";
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
      oceanShaderAnimationId = requestAnimationFrame(render);
    }
    render();
  }

  function stopOceanShaderAnimation() {
    if (oceanShaderAnimationId) {
      cancelAnimationFrame(oceanShaderAnimationId);
      oceanShaderAnimationId = null;
    }
    const canvas = document.getElementById("oceanShader");
    if (canvas) {
      canvas.remove();
    }
  }

  window.addEventListener("resize", () => {
    const canvas = document.getElementById("oceanShader");
    if (canvas && gl) {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      gl.viewport(0, 0, gl.drawingBufferWidth, gl.drawingBufferHeight);
    }
  });
  
  window.startOceanShaderAnimation = startOceanShaderAnimation;
  window.stopOceanShaderAnimation = stopOceanShaderAnimation;
})();