(() => {
  const fragmentShaderSource = `
  precision mediump float;

  uniform float iTime;
  uniform vec2 iResolution;

  float hash(vec2 p) {
      return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
  }

  float snowLayer(vec2 uv, float scale, float speed, float size, float density) {
      vec2 grid = uv * scale;

      grid.y += iTime * speed;
      grid.x += sin(iTime * 0.35 + grid.y * 0.12) * 0.25;

      vec2 cell = floor(grid);
      vec2 local = fract(grid);

      float rnd = hash(cell);

      vec2 flakePos = vec2(
          rnd,
          hash(cell + 19.37)
      );

      float dist = distance(local, flakePos);

      float flake = smoothstep(size, 0.0, dist);
      flake *= step(1.0 - density, rnd);

      return flake;
  }

  void mainImage(out vec4 fragColor, in vec2 fragCoord) {
      vec2 uv = fragCoord / iResolution.xy;

      vec3 topColor = vec3(0.90, 0.98, 1.00);
      vec3 bottomColor = vec3(0.72, 0.88, 0.95);
      vec3 glowColor = vec3(0.55, 0.90, 1.00);

      vec3 col = mix(bottomColor, topColor, uv.y);

      // Very cheap diagonal frost bands
      float band = sin((uv.x * 1.4 + uv.y * 1.8 + iTime * 0.025) * 18.0);
      band = smoothstep(0.82, 1.0, band);
      col += glowColor * band * 0.045;

      // Cheap snow, two layers only
      float snow = 0.0;
      snow += snowLayer(uv, 24.0, 0.10, 0.045, 0.050);
      snow += snowLayer(uv + vec2(0.37, 0.0), 42.0, 0.17, 0.032, 0.035);

      col = mix(col, vec3(1.0), clamp(snow, 0.0, 1.0) * 0.75);

      // Very cheap vignette
      vec2 centered = uv - 0.5;
      float vignette = 1.0 - dot(centered, centered) * 0.28;
      col *= vignette;

      fragColor = vec4(col, 1.0);
  }

  void main() {
      vec4 c;
      mainImage(c, gl_FragCoord.xy);
      gl_FragColor = c;
  }
  `;

  const frostyEffect = window.PiggyWebGLBackground.create({
    canvasId: "frostyShader",
    fragmentShaderSource,
    clearColor: [238 / 255, 250 / 255, 255 / 255, 1],
    dummyTextureColor: [238, 250, 255, 255],
    renderScale: 0.5,
  });

  window.startFrostyShaderAnimation = frostyEffect.start;
  window.stopFrostyShaderAnimation = frostyEffect.stop;
})();
