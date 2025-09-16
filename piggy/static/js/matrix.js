// Global variables
(() => {
  let matrixIntervalId;
  let drops = [];
  const fontSize = 16;
  const colSpacing = fontSize * 0.8;

  function startMatrixAnimation() {
    let overlay = document.querySelector(".background-overlay");
    if (!overlay) {
      console.error("background-overlay element not found");
      return;
    }
    
    let canvas = document.getElementById("matrix");
    if (!canvas) {
      canvas = document.createElement("canvas");
      canvas.id = "matrix";
      canvas.style.position = "absolute";
      canvas.style.top = "0";
      canvas.style.left = "0";
      canvas.style.width = "100%";
      canvas.style.height = "100%";
      canvas.style.zIndex = "0";
      canvas.style.pointerEvents = "none";
      overlay.appendChild(canvas);
    }
    
    const ctx = canvas.getContext("2d");
    
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    ctx.font = fontSize + 'px monospace';
    ctx.textAlign = "center";
    
    let columns = Math.floor(canvas.width / colSpacing);

    // Initialize with random starting positions
    drops = Array.from({length: columns}, () => 
      Math.floor(Math.random() * (canvas.height / fontSize))
    );
    
    function draw() {
      // fading effect
      ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      ctx.fillStyle = 'rgba(0, 180, 0, 0.8)';
      
      // Draw random characters for each column with a mirrored effect
      for (let i = 0; i < drops.length; i++) {
        // Randomly pick a character
        const text = "日ｦｲｸｺｿﾁﾄﾉﾌﾔﾖﾙﾚﾛﾝ012345789Z:・.\"=*+-<></>¦｜╌çﾘｸ二コソヤｦｱｳｴｵｶｷｹｺｻｼｽｾｿﾀﾂﾃﾅﾆﾇﾈﾊﾋﾎﾏﾐﾑﾒﾓﾔﾕﾗﾘﾜ".charAt(Math.floor(Math.random() * 85));
        // Compute coordinates: center each character in its column cell
        const x = i * colSpacing + colSpacing / 2;
        const y = drops[i] * fontSize;
        
        // Save the current context state, apply mirror transformation, then draw the character
        ctx.save();
        ctx.translate(x, y);
        ctx.scale(-1, 1); // mirror
        ctx.fillText(text, 0, 0);
        ctx.restore();
        
        // Reset drop to the top
        if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
          drops[i] = 0;
        }
        
        drops[i]++;
      }
    }
    
    // 30 fps
    matrixIntervalId = setInterval(draw, 33);
  }

  function stopMatrixAnimation() {
    if (matrixIntervalId) {
      clearInterval(matrixIntervalId);
      matrixIntervalId = null;
    }

    const canvas = document.getElementById("matrix");
    if (canvas) {
      canvas.remove();
    }
  }

  window.addEventListener('resize', () => {
    let canvas = document.getElementById("matrix");
    if (canvas) {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      let columns = Math.floor(canvas.width / colSpacing);
      drops = Array.from({length: columns}, () => 
        Math.floor(Math.random() * (canvas.height / fontSize))
      );
    }
  });

  window.startMatrixAnimation = startMatrixAnimation;
  window.stopMatrixAnimation = stopMatrixAnimation;
})();