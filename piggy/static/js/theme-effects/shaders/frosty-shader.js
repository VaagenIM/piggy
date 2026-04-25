(() => {
  const fragmentShaderSource = `
  precision mediump float;

  uniform float iTime;
  uniform vec2 iResolution;

  // credit: https://www.shadertoy.com/view/Mdt3Df

  vec3 hex(float r, float g, float b) {
    return vec3(r, g, b) / 255.0;
  }

  void mainImage(out vec4 fragColor, in vec2 fragCoord)
  {
      vec2 uv = fragCoord.xy / iResolution.xy;

      // Frosty palette from theme
      vec3 colTop    = hex(238.0, 250.0, 255.0);
      vec3 colMid    = hex(223.0, 247.0, 255.0);
      vec3 colBottom = hex(135.0, 230.0, 245.0);
      vec3 snowTint  = hex(255.0, 255.0, 255.0);
      vec3 glowTint  = hex(112.0, 219.0, 255.0);
      vec3 shadowTint= hex(111.0, 154.0, 170.0);

      float snow = 0.0;

      // Proper vertical gradient based on height, not width
      float gradientT = clamp(uv.y, 0.0, 1.0);
      vec3 background = mix(colBottom, colMid, smoothstep(0.0, 0.55, gradientT));
      background = mix(background, colTop, smoothstep(0.45, 1.0, gradientT));

      // Fine grain, very subtle
      float random = fract(sin(dot(fragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453);

      for (int k = 0; k < 6; k++) {
          for (int i = 0; i < 12; i++) {
              float fi = float(i) + 1.0; // avoid division by zero
              float fk = float(k);

              float cellSize = 2.0 + float(i) * 3.0;
              float downSpeed = 0.3 + (sin(iTime * 0.4 + float(k + i * 20)) + 1.0) * 0.00008;

              vec2 uvSnow =
                  (fragCoord.xy / iResolution.x) +
                  vec2(
                      0.01 * sin((iTime + float(k * 6185)) * 0.6 + float(i)) * (5.0 / fi),
                      downSpeed * (iTime + float(k * 1352)) * (1.0 / fi)
                  );

              vec2 uvStep = ceil(uvSnow * cellSize - vec2(0.5)) / cellSize;

              float x = fract(
                  sin(dot(uvStep.xy, vec2(12.9898 + fk * 12.0, 78.233 + fk * 315.156))) *
                  43758.5453 + fk * 12.0
              ) - 0.5;

              float y = fract(
                  sin(dot(uvStep.xy, vec2(62.2364 + fk * 23.0, 94.674 + fk * 95.0))) *
                  62159.8432 + fk * 12.0
              ) - 0.5;

              float randomMagnitude1 = sin(iTime * 2.5) * 0.7 / cellSize;
              float randomMagnitude2 = cos(iTime * 2.5) * 0.7 / cellSize;

              float d = 5.0 * distance(
                  uvStep.xy
                    + vec2(x * sin(y), y) * randomMagnitude1
                    + vec2(y, x) * randomMagnitude2,
                  uvSnow.xy
              );

              float omiVal = fract(sin(dot(uvStep.xy, vec2(32.4691, 94.615))) * 31572.1684);

              if (omiVal < 0.08) {
                  float newd =
                      (x + 1.0) * 0.4 *
                      clamp(1.9 - d * (15.0 + x * 6.3) * (cellSize / 1.4), 0.0, 1.0);

                  snow += newd * 0.25;
              }
          }
      }

      // Build snow color with gentle cyan glow
      vec3 snowColor = snow * mix(snowTint, glowTint, 0.35);

      // Soft frost haze toward the lower half
      float frostHaze = smoothstep(0.15, 0.95, 1.0 - uv.y);
      vec3 hazeColor = mix(vec3(0.0), glowTint, 0.06 * frostHaze);

      // Very soft top glow for icy air feel
      float topGlow = smoothstep(0.35, 1.0, uv.y);
      vec3 topGlowColor = glowTint * 0.08 * topGlow;

      // Slight vignette, very light, to avoid harsh edges
      vec2 centered = uv - 0.5;
      float vignette = 1.0 - dot(centered, centered) * 0.35;
      vignette = clamp(vignette, 0.88, 1.0);

      vec3 finalColor = background;
      finalColor += hazeColor;
      finalColor += topGlowColor;
      finalColor += snowColor;
      finalColor += random * 0.008;
      finalColor *= vignette;

      // Add a subtle cool shadow balance so it isn't too washed out
      finalColor = mix(finalColor, finalColor * shadowTint, 0.03);

      fragColor = vec4(finalColor, 1.0);
  }

  void main() {
      vec4 color;
      mainImage(color, gl_FragCoord.xy);
      gl_FragColor = color;
  }
  `;

  const frostyShaderEffect = window.PiggyWebGLBackground.create({
    canvasId: "frostyShader",
    fragmentShaderSource,
    clearColor: [238 / 255, 250 / 255, 255 / 255, 1.0],
    dummyTextureColor: [238, 250, 255, 255],
  });

  window.startFrostyShaderAnimation = frostyShaderEffect.start;
  window.stopFrostyShaderAnimation = frostyShaderEffect.stop;
})();
