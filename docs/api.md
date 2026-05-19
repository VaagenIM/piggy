# Piggy API Documentation

Piggy exposes a small read-only HTTP API under `/api`. Responses are JSON unless
an endpoint explicitly returns an image.

Assignment paths use the same URL-safe names as the `/main/...` assignment
routes. You can usually copy the path after `/main/` from the browser address
bar and use it directly in API calls.

## `GET /api/`

Returns the full Piggy map: years, classes, subjects, topics, assignments, and
metadata.

This is the broadest endpoint. Prefer the narrower endpoints below when a tool
only needs one assignment, search data, or reader audio.

## `GET /api/<path>`

Returns metadata and the Piggy map segment for a specific route.

Example:

```text
/api/VG1/IM/Programmering/Web_-_HTML_1/
```

Response shape:

```json
{
  "meta": {},
  "segment": {}
}
```

`meta` contains metadata for the requested path. `segment` contains the children
or assignment data at that path. Path objects are converted into API-friendly
strings and URLs.

## `GET /api/search-data`

Returns a flat assignment list used by the client-side Lunr search index.

Use this when building search UI or external search tooling. The response is
already flattened; it is easier to consume than walking `/api/`.

## `GET /api/generate_thumbnail/<text>`

Returns a generated WebP thumbnail image.

Query parameters:

- `bg_color`: optional background color, with or without `#`.
- `text_color`: optional text color, with or without `#`.
- `width`: optional width in pixels, capped at `1000`.
- `height`: optional height in pixels, capped at `1000`.
- `c`: optional palette seed. When `bg_color` and `text_color` are not provided,
  Piggy uses this together with `<text>` to choose a deterministic palette.

Example:

```text
/api/generate_thumbnail/Networking?width=1024&height=512&c=Networking
```

## `GET /api/get-audio-map/<assignment-url>/`

Returns the reader audio IDs and text for one assignment.

Example:

```text
/api/get-audio-map/VG1/IM/Programmering/Web_-_HTML_1/HTML_Level_1_-_Basic_HTML_Oppsett/
```

Language-specific audio maps use the `lang` query parameter:

```text
/api/get-audio-map/VG1/IM/Programmering/Web_-_HTML_1/HTML_Level_1_-_Basic_HTML_Oppsett/?lang=eng
```

The endpoint also accepts paths that include `/main/` at the front, and paths
that end with `/lang/<language>`. If both a path language and `?lang=` are
provided, the query parameter is used.

Response shape:

```json
[
  { "id": "s-01-0001", "text": "Hello there, this is the first sentence!" },
  { "id": "s-01-0002", "text": "Howdy sir, this is the second sentence!" },
  { "id": "p-01-0001", "texts": ["s-01-0001", "s-01-0002"] },
  { "id": "sec-01-0001", "texts": ["s-01-0001", "s-01-0002"] }
]
```

Audio ID prefixes:

- `s`: sentence audio clip. Record these as files.
- `p`: paragraph playlist. This lists the sentence IDs in the paragraph.
- `sec`: section playlist. This lists the heading and body sentence IDs for a
  section.

Sentence audio files are resolved by ID, for example `s-01-0001.mp3`. The first
number is the assignment level padded to two digits. The second number is the
sentence, paragraph, or section sequence padded to four digits.

For generator workflows:

1. Request the audio map for the assignment and language.
2. Filter entries whose IDs start with `s-`.
3. Generate one audio file per sentence using `text`.
4. Save each file as `<id>.mp3` or another supported extension in the assignment
   `audio/` folder.

## Reader Audio File Route

Reader playback uses this route rather than `/api`:

```text
/main/<assignment-url>/reader-audio/<sentence-id>
```

Translated pages add:

```text
?lang=<language>
```

The route serves the first matching supported audio extension from the
assignment-local audio folder. Supported extensions are `.mp3`, `.m4a`, `.ogg`,
`.opus`, `.wav`, and `.webm`.

The route validates the ID format, rejects path traversal, and only serves files
from the resolved assignment audio directory.

## Errors

Missing assignments, unavailable translations, invalid language codes, and
invalid reader audio IDs return the normal Piggy error response with an
appropriate HTTP status code, usually `404`.
