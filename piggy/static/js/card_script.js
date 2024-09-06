function checkTagsVisibility() {
    const tagsContainers = document.querySelectorAll('.tags-container');
    tagsContainers.forEach(container => {
        const seeMoreButton = container.nextElementSibling;
        if (container.scrollHeight > container.clientHeight) {
            seeMoreButton.style.display = 'block';
            container.classList.add('fade');
        } else {
            seeMoreButton.style.display = 'none';
            container.classList.remove('fade');
        }
    });
}

function toggleTags(button) {
    const tagsContainer = button.previousElementSibling;
    tagsContainer.classList.toggle('expanded');
    button.textContent = tagsContainer.classList.contains('expanded') ? 'Se færre' : 'Se flere';
}

// Function to generate a color from a string (tag text)
function stringToColor(str, transparency = 'FF') {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    let color = '#';
    for (let i = 0; i < 3; i++) {
        let value = (hash >> (i * 8)) & 0xFF;
        color += ('00' + value.toString(16)).slice(-2);
    }

    color += transparency;

    return color;
}

const tags = document.querySelectorAll('.tag-box');

tags.forEach(tag => {
    const tagText = tag.getAttribute('data-tag');
    tag.style.backgroundColor = stringToColor(tagText, '88');
    tag.style.borderColor = stringToColor(tagText);
});

