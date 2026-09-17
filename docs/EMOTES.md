# Emotes (`:name:` shortcodes)

Any assignment markdown body can reference a shared image by name, e.g.
`:diff1:`, instead of embedding a copy of that image in the assignment's own
`attachments/` folder. This exists because a handful of icons (the old
`diff1.png` … `diff5.png` difficulty icons) used to be duplicated into every
single assignment folder that needed them.

Emotes are separate from the `difficulty` frontmatter field and the
card-facing difficulty badge (`static/img/difficulties/1.png`…`5.png`) - see
[ASSIGNMENT_FRONTMATTER.md](ASSIGNMENT_FRONTMATTER.md). This mechanism is only
for images referenced inline from within a markdown body.

## Adding a new emote

1. Drop an image file into `piggybank/piggybank/emotes/`, named after the
   shortcode you want, e.g. `emotes/party.png` for `:party:`.
2. Optionally add an entry to the sibling `piggybank/piggybank/emotes.json`
   for alt text:
   ```json
   {
     "party": {"alt": "Party!"}
   }
   ```
   If omitted, the alt text falls back to a title-cased version of the
   filename.
3. Use it anywhere in an assignment body: `:party:`.

There is **no schema validation** for `emotes.json` - a missing file, or a
name with no entry, just falls back gracefully (`piggy/piggybank.py`,
`discover_emotes`). The set of available emotes is rebuilt once at app
startup from whatever image files exist in the `emotes/` folder at that time.

## How it renders

`:name:` is only ever substituted if `name` matches a discovered emote -
anything else (including real emoji shortcodes like `:smile:`, which mkdocs'
own emoji extension already handles) is left untouched. The substitution
happens as a post-processing pass over the rendered HTML
(`piggy/caching.py`, `replace_emotes`), after the markdown-to-HTML conversion,
and explicitly skips text inside `<pre>`/`<code>` blocks so a code sample
containing literal `:name:`-shaped text isn't rewritten.
