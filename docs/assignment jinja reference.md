# Relevant data for assignment folders

## Context variabler

Følgende verdier gjelder for _alle_ templates:

- `ASSIGNMENT_URL_PREFIX`: Prefix for assignment routes (`assignments`).
- `MEDIA_URL_PREFIX`: Prefix for media routes (`media`), brukes av bilder i `media` mappene i piggybank.
- `piggymap`: En kopi av `piggymap`-objektet, som inneholder hele strukturen til piggybank.
  - `piggymap` sin struktur er `filsti['data']` eller `filsti['meta']`, hvor `data` inneholder en nestet struktur av mapper og filer, og `meta` inneholder metadata om disse filene. (f.eks. `piggymap['VG2'].data['Naturfag'].data`)

## Assignment context variabler

Felles for alt i `assignments`-mappen.

- `path`: Filsti relativ til prefix (`assignments/VG2/Naturfag` -> `VG2/Naturfag`).
- `media_abspath`: Absolutt filsti til `media`-routes. (`/assignments/VG2/Naturfag` -> `/media/assignments/VG2/Naturfag`).
- `abspath`: Absolutt filsti til `assignments`-routes. (`/assignments/VG2/Naturfag` -> `/assignments/VG2/Naturfag`).

## Level 0-3

Følgende verdier er tilgjengelige i disse templatesene:

```bash
0-assignments_root.html
1-year_level.html
2-class_name.html
3-subject.html
```

- `segment`: Segmentet (`dict[str, dict]` key-value pair) fra `piggymap`-objektet for den gitte filen. (En side på `1-year_level.html` vil ha alle underelementer til det året. `VG1` vil derfor ha segment `IM`, `MK` for eksempel).
  - `key`: Nøkkelen til segmentet (f.eks. `VG1`).
  - `value`: Verdiene til segmentet (f.eks. `IM`, `MK`), data (`value['data']`) + metadata til segmentet (`value['meta']`).
- `meta`: Metadata fra `meta.json`-filen i samme mappe.
  - `name`: Alltid tilgjengelig, navnet på mappen om det ikke er definert i `meta.json`.

## Level 4 (`4-topic.html`)

`4-topic.html`-templaten er unik pga. den har oppgaver som segment, som har ekstra metadata (i tillegg til metadataen som er tilgjengelig i 0-3).

- `value`: verdien til segmentet har ekstra verdier:
  - `path`: Relativ filsti til oppgaven på disk
  - `assignment_name`: Navnet på oppgaven (**Eksempel Oppgave** Level 1 - Tittel på oppgave)
  - `level`: Nivået til oppgaven (Eksempel Oppgave Level **1** - Tittel på oppgave)
  - `level_name`: Navnet på nivået til oppgaven (Eksempel Oppgave Level 1 - **Tittel på oppgave**)
  - `heading`: Overskrift for oppgaven (definert av markdown-filen)
  - `meta`: Metadata for oppgaven (frontmatter)
  - `data`: Verdiene til selve oppgavene
    - Se Level 5 for hva som er tilgjengelig i `data`.

```bash
4-topic.html
```

## Level 5 (`5-assignment.html`)

  - `content`: `turtleconverter` seksjoner.
    - `heading`: Overskrift for oppgaven.
    - `head`: Det som er i `<head>`-taggen fra generert HTML.
    - `body`: Det som er i `<body>`-taggen fra generert HTML.
    - `meta`: Metadata for oppgaven (frontmatter).
  - `current_language`: Nåværende språk
  - `supported_languages`: Støttede språk for oppgaven
  - `assignment_name`: Navnet på oppgaven (**Eksempel Oppgave** Level 1 - Tittel på oppgave)
  - `level`: Nivået til oppgaven (Eksempel Oppgave Level **1** - Tittel på oppgave)
  - `level_name`: Navnet på nivået til oppgaven (Eksempel Oppgave Level 1 - **Tittel på oppgave**)