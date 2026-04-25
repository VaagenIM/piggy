(() => {
  const fragmentShaderSource = `
  precision mediump float;

  uniform float iTime;
  uniform vec2  iResolution;

  // ---------------- Desert palette ----------------
  const vec3 SAND_LIGHT = vec3(244.0/255.0, 231.0/255.0, 211.0/255.0);
  const vec3 SAND_TAN = vec3(210.0/255.0, 180.0/255.0, 140.0/255.0);
  const vec3 SAND_MID = vec3(184.0/255.0, 165.0/255.0, 140.0/255.0);
  const vec3 SAND_DARK = vec3(166.0/255.0, 124.0/255.0, 82.0/255.0);

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

  void mainImage(out vec4 fragColor, in vec2 fragCoord)
  {
      vec2 uv = fragCoord / iResolution.xy * vec2(640.0, 480.0);

      float z = 0.0;
      wave(uv.x, uv.y, z, iTime * 15.0, 17, 1.0);

      z = (z + 22.0) * 0.018;

      float h = smoothstep(0.05, 0.95, clamp(z, 0.0, 1.0));

      vec3 col = mix(SAND_DARK, SAND_MID, h);
      col = mix(col, SAND_TAN, h * h);
      col = mix(col, SAND_LIGHT, h * h * h);

      fragColor = vec4(col, 1.0);
  }

  void main() {
      vec4 c;
      mainImage(c, gl_FragCoord.xy);
      gl_FragColor = c;
  }
  `;

  const desertEffect = window.PiggyWebGLBackground.create({
    canvasId: "desertShader",
    fragmentShaderSource,
    clearColor: [205 / 255, 170 / 255, 125 / 255, 1],
    dummyTextureColor: [205, 170, 125, 255],
  });

  window.startDesertShaderAnimation = desertEffect.start;
  window.stopDesertShaderAnimation = desertEffect.stop;
})();
