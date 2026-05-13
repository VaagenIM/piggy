# Assignment Audio Reader

Piggy can play recorded audio for assignment text when a student enables
**Settings -> Support -> Audio reader**. Audio is not loaded with the page. The
browser only requests a file after the student clicks a sentence, paragraph, or
section heading. Clicking the same active sentence, paragraph, or heading again
stops playback.

## Where Audio Files Live

Place audio next to the assignment markdown:

```text
piggybank/<year>/<class>/<subject>/<topic>/audio/
```

For translated assignments, place language-specific audio next to the translated
markdown:

```text
piggybank/<year>/<class>/<subject>/<topic>/translations/<language>/audio/
```

Example:

```text
piggybank/VG1/IM/Programmering/Web - HTML 1/audio/s-001-0f82j4q.mp3
piggybank/VG1/IM/Programmering/Web - HTML 1/translations/eng/audio/s-001-18x0a7f.mp3
```

Supported file types are `.mp3`, `.m4a`, `.ogg`, `.opus`, `.wav`, and `.webm`.
Prefer `.mp3` for broad browser support.

## File Names

The reader generates deterministic IDs from the rendered text. Sentence files
are named with the sentence ID plus an audio extension:

```text
s-001-0f82j4q.mp3
```

Paragraphs and sections are playlists: Piggy plays the sentence files in order.
You normally only need to record the `sentence` items from the inventory.

To get the inventory for a page:

1. Open the assignment in a browser.
2. Enable **Settings -> Support -> Audio reader**.
3. Open DevTools Console.
4. Run:

```js
PiggyAudioReader.getInventory()
```

To copy only the sentence list:

```js
copy(
  JSON.stringify(
    PiggyAudioReader.getInventory().items.filter((item) => item.kind === "sentence"),
    null,
    2,
  ),
)
```

Each sentence item includes:

- `id`: the file stem to use.
- `text`: the text that should be recorded.

If assignment text changes, regenerate the inventory. IDs include the sentence
order and a hash of the text, so edits can change file names.

## How Playback Resolves Files

When a student clicks text, the browser requests:

```text
/main/<assignment-url>/reader-audio/<sentence-id>
```

The Flask route searches the assignment's `audio/` folder for the first matching
supported file extension. For translated pages it searches
`translations/<language>/audio/`.

The route validates the reader ID, rejects path traversal, and only serves files
inside the assignment audio folder. Flask serves the file conditionally, so
browsers can use range requests and do not download audio until playback starts.

## Practical Recording Flow

1. Finish editing the assignment text.
2. Generate the sentence inventory.
3. Record each sentence as a separate file.
4. Export files with the exact sentence IDs.
5. Put the files in the correct `audio/` folder.
6. Reload the assignment, enable the reader, and click sentences/headings to
   test playback.

Missing files are skipped during paragraph or section playback. If a section is
silent, check that the sentence IDs in the current inventory match the files on
disk.
