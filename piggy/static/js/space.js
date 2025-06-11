// Global variables
let spaceIntervalId;
let stars = [];
const starCount = 200;            // Total number of stars
const starSpeed = 0.5;            // Base speed for star movement

function startSpaceAnimation() {
  // Get the background overlay container
  let overlay = document.querySelector(".background-overlay");
  if (!overlay) {
    console.error("background-overlay element not found");
    return;
  }
  
  // Create the canvas if it doesn't already exist
  let canvas = document.getElementById("space");
  if (!canvas) {
    canvas = document.createElement("canvas");
    canvas.id = "space";
    // Position the canvas absolutely within the overlay
    canvas.style.position = "absolute";
    canvas.style.top = "0";
    canvas.style.left = "0";
    canvas.style.width = "100%";
    canvas.style.height = "100%";
    canvas.style.zIndex = "0";
    canvas.style.pointerEvents = "none"; // Let clicks pass through
    overlay.appendChild(canvas);
  }
  
  const ctx = canvas.getContext("2d");
  
  // Set the canvas dimensions to the window size
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  
  // Initialize stars array with random positions, sizes, and speeds
  stars = Array.from({ length: starCount }, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    radius: Math.random() * 1.5 + 0.5, // Radius between 0.5 and 2.0
    speed: Math.random() * starSpeed + 0.2  // Speed between 0.2 and starSpeed+0.2
  }));
  
  function draw() {
    // Clear the canvas with a deep black background
    ctx.fillStyle = "rgba(0, 0, 0, 1)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Draw each star as a small white circle
    ctx.fillStyle = "rgba(255, 255, 255, 0.8)";
    stars.forEach(star => {
      ctx.beginPath();
      ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
      ctx.fill();
      
      // Update star position: stars drift downward
      star.y += star.speed;
      // Add slight horizontal drift for a natural feel
      star.x += (Math.random() - 0.5) * 0.5;
      
      // If the star moves off the bottom, respawn it at the top with a new random x position
      if (star.y > canvas.height) {
        star.y = 0;
        star.x = Math.random() * canvas.width;
      }
      // Wrap horizontally if necessary
      if (star.x < 0) star.x = canvas.width;
      else if (star.x > canvas.width) star.x = 0;
    });
  }
  
  // Start the animation at roughly 30 frames per second
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

// Adjust the canvas on window resize to keep it full-screen
window.addEventListener('resize', () => {
  let canvas = document.getElementById("space");
  if (canvas) {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
});
