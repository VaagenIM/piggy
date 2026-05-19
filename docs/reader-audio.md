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
piggybank/VG1/IM/Programmering/Web - HTML 1/audio/s-01-0001.mp3
piggybank/VG1/IM/Programmering/Web - HTML 1/translations/eng/audio/s-01-0001.mp3
```

Supported file types are `.mp3`, `.m4a`, `.ogg`, `.opus`, `.wav`, and `.webm`.
Prefer `.mp3` for broad browser support.

## File Names

Reader IDs are deterministic and no longer include a text hash. They use the
assignment level and a readable sequence number:

```text
s-<level>-<sentence>
```

For level 1, the first sentence audio file is:

```text
s-01-0001.mp3
```

The level is padded to two digits. The sentence number is padded to four digits.
Numbers are not truncated, so unusually large values continue naturally.

The prefixes are:

- `s`: sentence audio clip. These are the files you record.
- `p`: paragraph playlist. Piggy plays the paragraph's sentence files in order.
- `sec`: section playlist. Piggy plays a heading and the content below it.

Paragraphs and sections do not need their own audio files unless the reader is
changed to use full-paragraph recordings later. Today they are playlist IDs.

Older hash-style names such as `s-001-0f82j4q.mp3` are not resolved by the
current reader. Regenerate the audio map and rename or regenerate files with the
new ID format.

## Audio Map API

Use the audio map API to get the current IDs and recording text for an
assignment:

```text
/api/get-audio-map/<assignment-url>/?lang=<language>
```

The `<assignment-url>` is the assignment path without `/main/`. Passing `/main/`
at the front also works. `lang` is optional; omit it for the default assignment
language.

Example:

```text
/api/get-audio-map/VG1/IM/Programmering/Web_-_HTML_1/HTML_Level_1_-_Basic_HTML_Oppsett/
/api/get-audio-map/VG1/IM/Programmering/Web_-_HTML_1/HTML_Level_1_-_Basic_HTML_Oppsett/?lang=eng
```

The response is a JSON array:

```json
[
  { "id": "s-01-0001", "text": "Hello there, this is the first sentence!" },
  { "id": "s-01-0002", "text": "Howdy sir, this is the second sentence!" },
  { "id": "p-01-0001", "texts": ["s-01-0001", "s-01-0002"] }
]
```

Sentence entries use `text`. Playlist entries use `texts`, which is the ordered
list of sentence IDs they play. For audio generation, filter entries whose IDs
start with `s-` and export files named exactly `<id>.<extension>`.

## Browser Inventory

The browser exposes the same reader inventory for debugging:

```js
PiggyAudioReader.getInventory()
```

To copy only the sentence list from an open assignment:

```js
copy(
  JSON.stringify(
    PiggyAudioReader.getInventory().items.filter((item) => item.kind === "sentence"),
    null,
    2,
  ),
)
```

The API is preferred for recording and generation because it does not require
opening a browser page manually.

## How IDs Are Assigned

IDs are assigned from the rendered assignment, not from the raw markdown file.
The sequence starts with the assignment title, then continues through headings,
paragraphs, list items, table cells, description-list items, and captions in
reading order.

Inline links contribute their visible text to the sentence that should be
recorded, but Piggy does not wrap the link text as an audio click target. This
keeps links clickable while preserving complete spoken sentences.

If assignment text changes, regenerate the audio map. Existing sentence IDs stay
stable when text is edited without changing the rendered sentence order. Adding,
removing, or moving sentences can change the following sequence numbers.

## How Playback Resolves Files

When a student clicks text, the browser requests:

```text
/main/<assignment-url>/reader-audio/<sentence-id>
```

For translated pages the browser adds `?lang=<language>`.

The Flask route searches the assignment's `audio/` folder for the first matching
supported file extension. For translated pages it searches
`translations/<language>/audio/`.

The route validates the reader ID, rejects path traversal, and only serves files
inside the assignment audio folder. Flask serves the file conditionally, so
browsers can use range requests and do not download audio until playback starts.

## Practical Recording Flow

1. Finish editing the assignment text.
2. Request the audio map for the assignment and language.
3. Record each `s-` item as a separate file using its `text`.
4. Export files with the exact sentence IDs.
5. Put the files in the correct `audio/` folder.
6. Reload the assignment, enable the reader, and click sentences/headings to
   test playback.

Missing files are skipped during paragraph or section playback. If a section is
silent, check that the sentence IDs in the current audio map match the files on
disk.
