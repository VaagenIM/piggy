# piggy - Oppgavebank for IKT & IM VG1/VG2

[![GitHub Pages](https://badgen.net/badge/visit/github%20pages/?icon=chrome)](https://piggy.iktim.no)
[![GitHub Pages Edge](https://badgen.net/badge/visit/demo%20pages/?icon=chrome)](https://piglet.iktim.no)

Install dev:

```bash
uv sync --all-extras --upgrade
uv run pre-commit install
npm i
```

Or just run the `install.sh` script

## Documentation

- [Folder `meta.json` reference](docs/METADATA.md)
- [Assignment frontmatter reference](docs/ASSIGNMENT_FRONTMATTER.md)

🚧 Construction in progress. 🚧

## Bøker og kapitler

Et tema kan ha et `book`-objekt i `meta.json`, med `title`, `contents` og en ordnet `chapters`-liste. `contents` peker på innholdssiden. Hvert kapittel har `title`, `page` og `anchor`. Sidestiene er relative til innholdsroten, med `.md`; `anchor` er en eksplisitt HTML-ID uten `#`, for eksempel `<a id="kapittel-3"></a>` i Markdown-kilden. Kapittelnummeret følger plasseringen i lista, uavhengig av filenes Level-numre.

Flere kapitler kan bruke samme side med ulike ankere, også på tvers av temaer. Bokmedlemssider får en meny med «Innhold» og «Kapittel 1» til N, samt forrige/neste. Andre sider beholder nivåvelgeren. Eksisterende adresser beholdes; innhold kopieres ikke. [Bokkontrakten](piggy/books.py) validerer sidemål, offentlig synlighet, ankere og entydig medlemskap ved oppstart, også før statisk bygging. Appen med bokstøtten må være installert før et bokkart tas i bruk.
