// Get elements
const settingsMenu = document.getElementById('settings-menu');
const settingsBtn = document.getElementById('settings-btn');
const closeBtn = document.querySelector('.settings-menu .closebtn');
const themeSelect = document.getElementById('theme-select');
const dyslexiaBtn = document.getElementById('dyslexia-button');

const currentTheme = localStorage.getItem('theme') || 'dark';
const fontTheme = localStorage.getItem('data-font-theme') || 'default';

function pageTransition() {
    document.body.classList.add("transition");
    setTimeout(() => {
        document.body.classList.remove("transition");
    }, 1000);
}

// Function to open the settings menu
function openSettingsMenu() {
    settingsMenu.classList.add('open');
}

// Function to close the settings menu
function closeSettingsMenu() {
    settingsMenu.classList.remove('open');
}

function toggleDyslexia() {
    // Retrieve the current theme from the data attribute
    let fontTheme = document.documentElement.getAttribute('data-font-theme');

    // Toggle between 'default' and 'dyslexia'
    if (fontTheme === "default") {
        document.documentElement.setAttribute('data-font-theme', 'dyslexia');
        localStorage.setItem('data-font-theme', 'dyslexia'); // Save theme to localStorage
        dyslexiaBtn.innerHTML = "Dyslexia Friendly Mode [✅]"
    } else {
        document.documentElement.setAttribute('data-font-theme', 'default');
        localStorage.setItem('data-font-theme', 'default'); // Save theme to localStorage
        dyslexiaBtn.innerHTML = "Dyslexia Friendly Mode"
    }

    pageTransition();
}

// Set the current theme on page load
document.documentElement.setAttribute('data-theme', currentTheme);
document.documentElement.setAttribute('data-font-theme', fontTheme);

if (fontTheme === "default") {
    dyslexiaBtn.innerHTML = "Dyslexia Friendly Mode"
} else {
    dyslexiaBtn.innerHTML = "Dyslexia Friendly Mode [✔]"
}

// Set the selected option based on the current theme
themeSelect.value = currentTheme;

// Event listener for the Settings button
settingsBtn.addEventListener('click', openSettingsMenu);

// Event listener for the Close button inside the menu
closeBtn.addEventListener('click', closeSettingsMenu);

dyslexiaBtn.addEventListener('click', toggleDyslexia);

// Event listener for theme selection change
themeSelect.addEventListener('change', function() {
    pageTransition();

    const selectedTheme = themeSelect.value;
    document.documentElement.setAttribute('data-theme', selectedTheme);
    localStorage.setItem('theme', selectedTheme); // Save theme to localStorage
});

// Close settings menu when clicking outside of it
window.addEventListener('click', function(event) {
    if (
        settingsMenu.classList.contains('open') && // Only if the menu is open
        !settingsMenu.contains(event.target) && // Click is outside the menu
        event.target !== settingsBtn // Click is not on the settings button
    ) {
        closeSettingsMenu();
    }
});