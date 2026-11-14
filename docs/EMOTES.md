# Emotes (`:name:` shortcodes)

Assignment markdown supports the regular emoji shortcodes (`:smile:`,
`:tada:`, ... from twemoji), plus piggy's own *emotes*: every image in
`piggy/static/img/emotes/`, named after the file. These ship with piggy:

| Shortcode | Image |
|---|---|
| `:diff1:` … `:diff5:` | The difficulty icons (`diff1.webp` … `diff5.webp`), also shown on cards and in the level selector |

So instead of copying `diff2.webp` into a topic's `attachments/` folder and
writing `![Medium|48](attachments/diff2.webp#center)`, write `:diff2:`.

Emotes are sized to the surrounding text. Like any other emoji they are left
alone inside inline code and code blocks.

## Adding an emote

Drop an image into `piggy/static/img/emotes/`, named after the shortcode:
`party.webp` becomes `:party:`. Any image format works (WebP, PNG, SVG, GIF,
...); keep one file per name. The alt text is the name with `_` as spaces,
unless `EMOTE_ALT_TEXT` in `piggy/emotes.py` gives a better one. The list is
built once at startup, so restart the app after adding one. An emote named
like a twemoji shortcode replaces that emoji.

The shortcodes are rendered by turtleconverter's `emojis` option
(`piggy/caching.py`), which piggy fills with these emotes.
