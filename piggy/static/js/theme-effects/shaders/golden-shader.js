(() => {
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

  const goldenEffect = window.PiggyWebGLBackground.create({
    canvasId: "goldenShader",
    fragmentShaderSource,
    clearColor: [11 / 255, 11 / 255, 14 / 255, 1],
    dummyTextureColor: [11, 11, 14, 255],
  });

  window.startGoldenShaderAnimation = goldenEffect.start;
  window.stopGoldenShaderAnimation = goldenEffect.stop;
})();
