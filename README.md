# piggy - Oppgavebank for IKT & IM VG1/VG2

[![GitHub Pages](https://badgen.net/badge/visit/github%20pages/?icon=chrome)](https://piggy.iktim.no)

Oppgavebank for IKT & IM VG1/VG2


## Filstruktur
Alle oppgaver må følge denne filstrukturen:

```
oppgaver/
    Enkel/
    Middels/
    Vanskelig/
    Prosjekt/
```

## Frontmatter:

```
---
title: "Tittel på oppgaven" (Valgfritt)
authors:
    -  "Forfatter" (Valgfritt)
tags:
    - "<Emne>" (Påkrevd), f.eks. "Programmering", "Nettverk", "Sikkerhet", "Digital kompetanse"
    - "<Emne>" (Valgfritt) f.eks. "HTML", "Python", osv.
github_template: <link til github repo> (Valgfritt) (Ikke implementert)
codepen_url: <link til codepen> (Valgfritt) (Ikke implementert)
---

# Tittel på oppgaven
```

## Vedlegg

Videoer kan bygges inn med HTML via "Del og bygg inn" på YouTube gjennom en iFrame.

Bilder må legges i en undermappe i `_assets/` og kan bygges inn med Markdown:

```
![Bildebeskrivelse](/_assets/<bildenavn>.png)
```

alt.:

```
![[<bildenavn>.png]]
```
