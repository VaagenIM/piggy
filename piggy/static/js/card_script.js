const COLOR_PRESETS = {
  python: "#0022aa",
  javascript: "#ff4400",
  java: "#4400ff",
};

// Function to generate a color from a string (tag text)
function stringToColor(str, transparency = "FF") {
  str = str.toLowerCase();

  if (COLOR_PRESETS.hasOwnProperty(str)) {
    return COLOR_PRESETS[str] + transparency;
  }

  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  let color = "#";
  for (let i = 0; i < 3; i++) {
    let value = (hash >> (i * 8)) & 0xff;
    color += ("00" + value.toString(16)).slice(-2);
  }

  color += transparency;

  return color;
}

const tags = document.querySelectorAll(".tag-box");

tags.forEach((tag) => {
  const tagText = tag.getAttribute("data-tag");
  tag.style.backgroundColor = stringToColor(tagText, "88");
  tag.style.borderColor = stringToColor(tagText);
});
