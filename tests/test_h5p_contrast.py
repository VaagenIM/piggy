"""Contrast regression checks using the shipped H5P and default theme tokens."""

import re
import unittest
from pathlib import Path


STATIC = Path(__file__).resolve().parents[1] / "piggy" / "static"


def declarations(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    return dict(re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", css))


def rule(css, selector):
    for selectors, body in re.findall(r"([^{}]+)\{([^{}]*)\}", re.sub(r"/\*.*?\*/", "", css, flags=re.S)):
        if selector in [entry.strip() for entry in selectors.split(",")]:
            return body
    raise ValueError(f"Missing rule: {selector}")


def color(expression, tokens):
    """Evaluate only the sRGB expressions used by these tokens; reject new syntax."""
    expression = expression.strip()
    if expression.startswith("var(") and expression.endswith(")"):
        name, _, fallback = expression[4:-1].partition(",")
        return color(tokens.get(name.strip(), fallback), tokens)
    if expression.startswith("#"):
        value = expression[1:]
        if len(value) == 3:
            value = "".join(character * 2 for character in value)
        if len(value) == 6:
            return (*[int(value[i : i + 2], 16) for i in (0, 2, 4)], 1)
    rgb = re.fullmatch(r"rgba?\(([^)]+)\)", expression)
    if rgb:
        channels = [float(channel.strip()) for channel in rgb[1].split(",")]
        return tuple(channels if len(channels) == 4 else channels + [1])
    mixed = re.fullmatch(r"color-mix\(in srgb,\s*(.+)\s+([\d.]+)%,\s*transparent\)", expression)
    if mixed:
        red, green, blue, alpha = color(mixed[1], tokens)
        return red, green, blue, alpha * float(mixed[2]) / 100
    raise ValueError(f"Unsupported color expression: {expression}")


def over(foreground, background):
    alpha = foreground[3]
    return tuple(f * alpha + b * (1 - alpha) for f, b in zip(foreground[:3], background[:3])) + (1,)


def luminance(value):
    def linear(channel):
        channel /= 255
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    return sum(linear(channel) * weight for channel, weight in zip(value[:3], (0.2126, 0.7152, 0.0722)))


def contrast(first, second):
    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


class H5PContrastTest(unittest.TestCase):
    def test_keyboard_focus_contrasts_with_default_theme_surfaces(self):
        h5p = declarations((STATIC / "css/components/h5p.css").read_text())
        # Read the actual shared ring, also used on the inner multiple-choice control.
        ring = re.fullmatch(r"0 0 0 (\d+)px (.+)", h5p["--q-focus-ring"].strip())
        self.assertIsNotNone(ring)
        self.assertGreaterEqual(int(ring[1]), 3)
        for theme in ("light", "dark"):
            tokens = declarations((STATIC / f"css/themes/{theme}.css").read_text()) | h5p
            page = color(tokens["--piggy-main"], tokens)
            surface = over(color(tokens["--q-surface"], tokens), page)
            for token in ("--q-surface", "--q-raised", "--q-bar", "--q-button", "--q-selected-bg"):
                with self.subTest(theme=theme, adjacent=token):
                    background = surface if token == "--q-surface" else over(color(tokens[token], tokens), surface)
                    visible_ring = over(color(ring[2], tokens), background)
                    self.assertGreaterEqual(contrast(visible_ring, background), 3)

    def test_normal_text_contrasts_with_default_quiz_surface(self):
        h5p = declarations((STATIC / "css/components/h5p.css").read_text())
        for theme in ("light", "dark"):
            with self.subTest(theme=theme):
                tokens = declarations((STATIC / f"css/themes/{theme}.css").read_text()) | h5p
                page = color(tokens["--piggy-main"], tokens)
                surface = over(color(tokens["--q-surface"], tokens), page)
                text = over(color(tokens["--q-text"], tokens), surface)
                self.assertGreaterEqual(contrast(text, surface), 4.5)

    def test_category_description_and_action_icons_in_both_default_themes(self):
        css = (STATIC / "css/components/h5p.css").read_text()
        h5p = declarations(css)
        category = declarations(rule(css, ".h5p-content .h5p-category-task"))
        actions = rule(css, ".h5p-content .h5p-category-task .h5p-category-task-argument-actions")
        # The library has more specific rules: these overrides must win the cascade.
        action_text = re.search(r"\bcolor:\s*(.+?)\s*!important;", actions)[1]
        action_background = re.search(r"\bbackground:\s*(.+?)\s*!important;", actions)[1]
        for theme in ("light", "dark"):
            with self.subTest(theme=theme):
                tokens = declarations((STATIC / f"css/themes/{theme}.css").read_text()) | h5p | category
                background = color(tokens["--color-background"], tokens)
                text = over(color(tokens["--piggy-text-main"], tokens), background)
                self.assertGreaterEqual(contrast(text, background), 4.5)
                # CategoryTask's cards use --h5p-theme-alternative-base -> --piggy-main.
                card = color(tokens["--piggy-main"], tokens)
                button = over(color(action_background, tokens), card)
                icon = over(color(action_text, tokens), button)
                self.assertGreaterEqual(contrast(icon, button), 3)


if __name__ == "__main__":
    unittest.main()
