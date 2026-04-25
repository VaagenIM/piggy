(() => {
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

  const oceanEffect = window.PiggyWebGLBackground.create({
    canvasId: "oceanShader",
    fragmentShaderSource,
    clearColor: [0 / 255, 43 / 255, 54 / 255, 1],
    dummyTextureColor: [0, 43, 54, 255],
  });

  window.startOceanShaderAnimation = oceanEffect.start;
  window.stopOceanShaderAnimation = oceanEffect.stop;
})();
