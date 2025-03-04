// Global variables
let matrixIntervalId;
let drops = [];
const fontSize = 16;             // Constant font size
const colSpacing = fontSize * 0.8; // Column spacing (80% of fontSize) for closer characters

function startMatrixAnimation() {
  // Get the background overlay container
  let overlay = document.querySelector(".background-overlay");
  if (!overlay) {
    console.error("background-overlay element not found");
    return;
  }
  
  // Create the canvas if it doesn't already exist
  let canvas = document.getElementById("matrix");
  if (!canvas) {
    canvas = document.createElement("canvas");
    canvas.id = "matrix";
    // Position the canvas absolutely within the overlay
    canvas.style.position = "absolute";
    canvas.style.top = "0";
    canvas.style.left = "0";
    canvas.style.width = "100%";
    canvas.style.height = "100%";
    canvas.style.zIndex = "0"; // Adjust z-index if needed relative to overlay content
    canvas.style.pointerEvents = "none"; // Prevent interactions affecting layout/scroll
    overlay.appendChild(canvas);
  }
  
  const ctx = canvas.getContext("2d");
  
  // Set the canvas dimensions to the window size
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  
  // Set the font and text alignment for center alignment
  ctx.font = fontSize + 'px monospace';
  ctx.textAlign = "center";
  
  // Calculate the number of columns based on colSpacing and initialize drops array
  let columns = Math.floor(canvas.width / colSpacing);
  drops = Array(columns).fill(0);
  
  // The draw function for animation
  function draw() {
    // Create a fading effect by drawing a translucent black rectangle
    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Set text color to a softer green (adjust the rgba values as desired)
    ctx.fillStyle = 'rgba(0, 180, 0, 0.8)';
    
    // Draw random characters for each column with a mirrored effect
    for (let i = 0; i < drops.length; i++) {
      // Randomly pick a character from our set
      const text = "日ｦｲｸｺｿﾁﾄﾉﾌﾔﾖﾙﾚﾛﾝ012345789Z:・.\"=*+-<></>¦｜╌çﾘｸ二コソヤｦｱｳｴｵｶｷｹｺｻｼｽｾｿﾀﾂﾃﾅﾆﾇﾈﾊﾋﾎﾏﾐﾑﾒﾓﾔﾕﾗﾘﾜ".charAt(Math.floor(Math.random() * 85));
      // Compute coordinates: center each character in its column cell
      const x = i * colSpacing + colSpacing / 2;
      const y = drops[i] * fontSize;
      
      // Save the current context state, apply mirror transformation, then draw the character
      ctx.save();
      ctx.translate(x, y);
      ctx.scale(-1, 1); // Mirror horizontally
      ctx.fillText(text, 0, 0);
      ctx.restore();
      
      // Reset drop to the top if it goes beyond the canvas height, with some randomness
      if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
        drops[i] = 0;
      }
      
      // Increment the drop's y-coordinate
      drops[i]++;
    }
  }
  
  // Start the animation at roughly 30 frames per second
  matrixIntervalId = setInterval(draw, 33);
}

function stopMatrixAnimation() {
  if (matrixIntervalId) {
    clearInterval(matrixIntervalId);
    matrixIntervalId = null;
  }
  // Remove the canvas if it exists
  const canvas = document.getElementById("matrix");
  if (canvas) {
    canvas.remove();
  }
}

// Adjust the canvas on window resize to keep it full-screen and recalc drops
window.addEventListener('resize', () => {
  let canvas = document.getElementById("matrix");
  if (canvas) {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    let columns = Math.floor(canvas.width / colSpacing);
    drops = Array(columns).fill(0);
  }
});
