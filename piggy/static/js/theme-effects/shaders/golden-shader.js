(() => {
  const fragmentShaderSource = `
  precision mediump float;

  uniform float iTime;
  uniform vec2 iResolution;

  #define LAYERS 18

  vec3 goldA = vec3(0.74, 0.56, 0.18);
  vec3 goldB = vec3(1.00, 0.86, 0.42);
  vec3 goldC = vec3(0.97, 0.92, 0.78);

  vec3 accentPink = vec3(0.96, 0.52, 0.66);
  vec3 accentViolet = vec3(0.80, 0.65, 1.00);
  vec3 accentCyan = vec3(0.36, 0.95, 1.00);

  float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
  }

  void main() {
    vec2 uv = gl_FragCoord.xy / iResolution.xy;

    vec2 p = uv * 2.0 - 1.0;
    p.x *= iResolution.x / iResolution.y;

    float globalYOffset = 0.08;
    p.y += globalYOffset;

    float time = iTime * 0.42;

    vec3 col = vec3(0.015, 0.012, 0.020);

    vec2 moonPos = vec2(0.52, 0.08);
    float r = length(p - moonPos);

    float moonRing = 1.0 - smoothstep(0.0, 0.026, abs(r - 0.42));
    float moonGlow = 1.0 - smoothstep(0.18, 0.70, r);

    col += goldB * moonRing * 0.085;
    col += vec3(0.18, 0.12, 0.04) * moonGlow * 0.065;

    for (int k = 0; k < LAYERS; k++) {
      float fi = float(k);
      float layer = fi / float(LAYERS - 1);

      vec2 q = p;

      q.y += (layer - 0.5) * 1.45;

      float wave =
          0.085 * sin(q.x * 2.4 + time * (0.95 + layer * 0.22) + fi * 0.65) +
          0.027 * sin(q.x * 6.4 - time * 1.20 + fi * 1.31) +
          0.014 * sin(q.x * 11.0 + time * 1.70 + fi * 2.07);

      float dist = abs(q.y + wave);

      float width = mix(0.014, 0.0045, layer);

      float core = 1.0 - smoothstep(width, width * 1.65, dist);
      float glow = 1.0 - smoothstep(width * 3.0, width * 7.0, dist);

      vec3 gold = mix(goldA, goldB, 0.35 + 0.65 * layer);

      float accentMix = 0.5 + 0.5 * sin(fi * 1.73 + time * 1.8);
      vec3 idolAccent = mix(accentPink, accentViolet, accentMix);

      float cyanPulse = pow(0.5 + 0.5 * sin(time * 2.4 + fi * 2.17), 10.0);
      idolAccent = mix(idolAccent, accentCyan, cyanPulse * 0.18);

      vec3 lineColor = mix(gold, idolAccent, 0.085);

      col += lineColor * core * 0.46;
      col += mix(gold, idolAccent, 0.14) * glow * 0.075;
    }

    vec2 sparkleGrid = floor((p + vec2(1.4, 1.0)) * vec2(18.0, 12.0));
    vec2 sparkleCell = fract((p + vec2(1.4, 1.0)) * vec2(18.0, 12.0)) - 0.5;

    float sparkleSeed = hash21(sparkleGrid);
    float sparkleGate = step(0.965, sparkleSeed);

    float sparklePulse = pow(
      0.5 + 0.5 * sin(time * 5.0 + sparkleSeed * 40.0),
      18.0
    );

    float sparkleShape =
      1.0 - smoothstep(0.0, 0.035, abs(sparkleCell.x + sparkleCell.y)) *
      smoothstep(0.0, 0.035, abs(sparkleCell.x - sparkleCell.y));

    float crossA = 1.0 - smoothstep(0.0, 0.018, abs(sparkleCell.x));
    float crossB = 1.0 - smoothstep(0.0, 0.018, abs(sparkleCell.y));
    float center = 1.0 - smoothstep(0.0, 0.055, length(sparkleCell));

    float sparkle = sparkleGate * sparklePulse * max(center, max(crossA, crossB) * 0.35);

    vec3 sparkleColor = mix(goldC, accentPink, 0.18 + 0.12 * sin(time * 2.0));
    col += sparkleColor * sparkle * 0.06;

    float shimmer = 0.5 + 0.5 * sin(p.x * 14.0 - time * 3.0);
    col += goldC * pow(shimmer, 10.0) * 0.01;

    float vignette = 1.0 - smoothstep(0.75, 1.55, length(p * vec2(0.9, 0.78)));
    col *= vignette;

    col = min(col, vec3(1.0));

    gl_FragColor = vec4(col, 1.0);
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
