from flask_babel import gettext


def build_js_i18n() -> dict:
    """
    Translated display strings for the JS-driven reader-preferences panel
    (piggy/static/js/preferences.js, settings-controls.js).

    Keyed by the same stable `value` identifiers those files already use, so
    preferences.js/settings-controls.js can merge this in without touching
    option ordering, storage keys, or any other logic - only display text.
    """
    return {
        "readerPreset": {
            "default": {"label": gettext("Standard"), "detail": gettext("Standard utseende på piggy")},
            "balanced": {"label": gettext("Balansert"), "detail": gettext("Komfortabel med moderne tekst")},
            "dyslexia": {
                "label": gettext("Dysleksivennlig"),
                "detail": gettext("Mer mellomrom og en vennligere form"),
            },
            "lowVision": {"label": gettext("Nedsatt syn"), "detail": gettext("Stor tekst og sterke kontraster")},
            "projector": {
                "label": gettext("Prosjektor"),
                "detail": gettext("For å vises på skjerm i klasserommet"),
            },
            "lowGlare": {"label": gettext("Lav blending"), "detail": gettext("Dempede farger og mindre bevegelse")},
            "focus": {"label": gettext("Fokus"), "detail": gettext("Stille side med en smal leser")},
            "compact": {"label": gettext("Kompakt"), "detail": gettext("Tett visning")},
            "randomized": {"label": gettext("Tilfeldig"), "detail": gettext("Gjør alt tilfeldig")},
            "custom": {"label": gettext("Egendefinert"), "detail": gettext("Dine nåværende innstillinger")},
        },
        "contrast": {
            "standard": {"label": gettext("Standard")},
            "soft": {"label": gettext("Myk")},
            "strong": {"label": gettext("Sterke")},
        },
        "accentColor": {
            "0": {"label": gettext("Standard")},
            "1": {"label": gettext("Rosé")},
            "2": {"label": gettext("Grønn")},
            "3": {"label": gettext("Rav")},
            "4": {"label": gettext("Fiolett")},
            "5": {"label": gettext("Blågrønn")},
            "6": {"label": gettext("Crimson")},
            "7": {"label": gettext("Lime")},
        },
        "readerFont": {
            "default": {"detail": gettext("Standard")},
            "atkinson": {"detail": gettext("Lesbare bokstaver")},
            "lexend": {"detail": gettext("Tekst med mye mellomrom")},
            "lexia": {"detail": gettext("Dysleksivennlig")},
            "open-dyslexic": {"detail": gettext("Dysleksivennlig")},
            "nunito": {"detail": gettext("Rund skrifttype")},
            "lato": {"detail": gettext("Humanist sans")},
            "quicksand": {"detail": gettext("Myk og rund skrifttype")},
            "arial": {"detail": gettext("System")},
            "verdana": {"detail": gettext("Bred skrift")},
            "bitter": {"detail": gettext("Serif skrift")},
            "georgia": {"detail": gettext("Serif skrift")},
        },
        "codeFont": {
            "default": {"detail": gettext("Default")},
            "atkinson-mono": {"detail": gettext("Lesbare symboler")},
            "fira-code": {"detail": gettext("Ligaturer")},
            "roboto-mono": {"detail": gettext("Clean")},
            "jetbrains-mono": {"detail": gettext("Utvikler")},
            "dm-mono": {"detail": gettext("Light")},
            "ubuntu-mono": {"detail": gettext("Klassisk")},
            "kode-mono": {"detail": gettext("Teknisk")},
            "lucida": {"detail": gettext("System")},
            "courier": {"detail": gettext("System")},
        },
        "readerFontSize": {
            "xx-small": {"label": gettext("Bitteliten")},
            "x-small": {"label": gettext("Mindre")},
            "small": {"label": gettext("Liten")},
            "default": {"label": gettext("Vanlig")},
            "large": {"label": gettext("Stor")},
            "x-large": {"label": gettext("Større")},
            "xx-large": {"label": gettext("Massiv")},
            "xxx-large": {"label": gettext("Gigantisk")},
        },
        "fontSizeAffectsUi": {
            "off": {"label": gettext("Bare innhold")},
            "on": {"label": gettext("Innhold og UI")},
        },
        "readerLineHeight": {
            "original": {"label": gettext("Standard")},
            "compact": {"label": gettext("Kompakt")},
            "comfortable": {"label": gettext("Behagelig")},
            "spacious": {"label": gettext("Mye mellomrom")},
            "extra": {"label": gettext("Ekstra mellomrom")},
        },
        "readerLetterSpacing": {
            "default": {"label": gettext("Standard")},
            "wide": {"label": gettext("Bred")},
            "extra": {"label": gettext("Ekstra bred")},
        },
        "readerWordSpacing": {
            "default": {"label": gettext("Standard")},
            "wide": {"label": gettext("Bred")},
            "extra": {"label": gettext("Ekstra bred")},
        },
        "readerParagraphSpacing": {
            "original": {"label": gettext("Standard")},
            "compact": {"label": gettext("Kompakt")},
            "comfortable": {"label": gettext("Behagelig")},
            "spacious": {"label": gettext("Mye mellomrom")},
            "extra": {"label": gettext("Ekstra mellomrom")},
        },
        "readerWidth": {
            "narrow": {"label": gettext("Smal")},
            "medium": {"label": gettext("Standard")},
            "wide": {"label": gettext("Bred")},
            "full": {"label": gettext("Full bredde")},
        },
        "reduceMotion": {
            "system": {"label": gettext("System")},
            "reduce": {"label": gettext("Lite")},
            "allow": {"label": gettext("Animert")},
        },
        "focusMode": {
            "off": {"label": gettext("Av")},
            "on": {"label": gettext("På")},
        },
        "readingRuler": {
            "off": {"label": gettext("Av")},
            "on": {"label": gettext("På")},
        },
        "rememberPosition": {
            "off": {"label": gettext("Av")},
            "on": {"label": gettext("På")},
        },
        "controlLabels": {
            "contrast": gettext("Kontrast"),
            "readerFont": gettext("Skrifttype"),
            "codeFont": gettext("Skrifttype for kode"),
            "readerFontSize": gettext("Tekststørrelse"),
            "fontSizeAffectsUi": gettext("Tekststørrelse omfang"),
            "readerLineHeight": gettext("Linjehøyde"),
            "readerLetterSpacing": gettext("Bokstavavstand"),
            "readerWordSpacing": gettext("Ordavstand"),
            "readerParagraphSpacing": gettext("Paragrafavstand"),
            "readerWidth": gettext("Innholdsbredde"),
            "focusMode": gettext("Fokus modus"),
            "readingRuler": gettext("Linjal"),
            "reduceMotion": gettext("Bevegelse og effekter"),
            "rememberPosition": gettext("Husk posisjon"),
        },
        "toggleLabels": {
            "focusMode": gettext("Demp navigasjonsmenyen i fokus modus"),
            "fontSizeAffectsUi": gettext("Bruk tekststørrelse på UI"),
            "readingRuler": gettext("Vis linjal"),
            "rememberPosition": gettext("Husk hvor du stopte å lese"),
        },
        "preview": {
            "lineOne": gettext("Line one"),
            "lineTwo": gettext("Line two"),
            "spacing": gettext("Spacing"),
            "wordSpacing": gettext("Word spacing"),
            "firstParagraph": gettext("First paragraph"),
            "secondParagraph": gettext("Second paragraph"),
            "quiet": gettext("Quiet"),
            "animated": gettext("Animated"),
            "system": gettext("System"),
        },
    }
