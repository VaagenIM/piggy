# Emotes (`:name:` shortcodes)

Assignment markdown supports the regular emoji shortcodes (`:smile:`,
`:tada:`, ... from twemoji), plus a few piggy-specific *emotes* that render as
images:

| Shortcode | Image |
|---|---|
| `:diff1:` … `:diff5:` | The difficulty icons (`piggy/static/img/difficulties/1.webp` … `5.webp`) |

So instead of copying `diff2.webp` into a topic's `attachments/` folder and
writing `![Medium|48](attachments/diff2.webp#center)`, write `:diff2:`.

Emotes are sized to the surrounding text. Like any other emoji they are left
alone inside inline code and code blocks.

## Adding an emote

Drop an image into `piggy/static/img/emotes/`, named after the shortcode:
`piggy/static/img/emotes/party.png` becomes `:party:`. The list is built once
at startup (`piggy/emotes.py`), so restart the app after adding one. An emote
named like a twemoji shortcode replaces that emoji.

The shortcodes are rendered by turtleconverter's `emojis` option
(`piggy/caching.py`), which piggy fills with these emotes.
