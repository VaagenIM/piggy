// Global variables
(() => {
  let spaceIntervalId;
  let stars = [];
  const starCount = 200;
  const starSpeed = 0.5;

  function startSpaceAnimation() {
    let overlay = document.querySelector(".background-overlay");
    if (!overlay) {
      console.error("background-overlay element not found");
      return;
    }
    
    let canvas = document.getElementById("space");

    if (!canvas) {
      canvas = document.createElement("canvas");
      canvas.id = "space";
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
    
    // Set the canvas dimensions to the window size
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    // Initialize stars with random attributes
    stars = Array.from({ length: starCount }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      radius: Math.random() * 1.5 + 0.5,
      speed: Math.random() * starSpeed + 0.2
    }));
    
    function draw() {
      ctx.fillStyle = "rgba(0, 0, 0, 1)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      ctx.fillStyle = "rgba(255, 255, 255, 0.8)";
      stars.forEach(star => {
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
        ctx.fill();
        
        star.y += star.speed;
        star.x += (Math.random() - 0.5) * 0.5;
        
        // If the star moves off the bottom, respawn it at the top with a new random x position
        if (star.y > canvas.height) {
          star.y = 0;
          star.x = Math.random() * canvas.width;
        }
        if (star.x < 0) star.x = canvas.width;
        else if (star.x > canvas.width) star.x = 0;
      });
    }
    
    // 30 fps
    spaceIntervalId = setInterval(draw, 33);
  }

  function stopSpaceAnimation() {
    if (spaceIntervalId) {
      clearInterval(spaceIntervalId);
      spaceIntervalId = null;
    }
    const canvas = document.getElementById("space");
    if (canvas) {
      canvas.remove();
    }
  }

  window.addEventListener('resize', () => {
    let canvas = document.getElementById("space");
    if (canvas) {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }
  });
  window.startSpaceAnimation = startSpaceAnimation;
  window.stopSpaceAnimation = stopSpaceAnimation;
})();