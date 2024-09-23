// Get elements
const settingsMenu = document.getElementById('settings-menu');
const settingsBtn = document.getElementById('settings-btn');
const closeBtn = document.querySelector('.settings-menu .closebtn');
const themeSelect = document.getElementById('theme-select');
const currentTheme = localStorage.getItem('theme') || 'dark';

// Function to open the settings menu
function openSettingsMenu() {
    settingsMenu.classList.add('open');
}

// Function to close the settings menu
function closeSettingsMenu() {
    settingsMenu.classList.remove('open');
}

// Set the current theme on page load
document.documentElement.setAttribute('data-theme', currentTheme);

// Set the selected option based on the current theme
themeSelect.value = currentTheme;

// Event listener for the Settings button
settingsBtn.addEventListener('click', openSettingsMenu);

// Event listener for the Close button inside the menu
closeBtn.addEventListener('click', closeSettingsMenu);

// Event listener for theme selection change
themeSelect.addEventListener('change', function() {
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