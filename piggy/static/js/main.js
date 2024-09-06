const modal = document.getElementById('theme-modal');
const currentTheme = localStorage.getItem('theme') || 'dark'; // Default to dark mode

// Function to close the modal
const closeModal = () => {
    modal.style.display = 'none';
};

// Set the current theme on page load
document.documentElement.setAttribute('data-theme', currentTheme);

document.getElementById('theme-modal-btn').addEventListener('click', function() {
    document.getElementById('theme-modal').style.display = 'block'; // Show the modal
});

// Optional: Close modal if user clicks outside the modal content
window.addEventListener('click', function(event) {
    if (event.target === modal) {
        closeModal();
    }
});

const themeButtons = document.querySelectorAll('.theme-option');
themeButtons.forEach(button => {
    button.addEventListener('click', function() {
        const selectedTheme = button.getAttribute('data-theme');
        document.documentElement.setAttribute('data-theme', selectedTheme);
        localStorage.setItem('theme', selectedTheme); // Save theme to localStorage
        document.getElementById('theme-modal').style.display = 'none'; // Hide modal
    });
});