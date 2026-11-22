# Veiledning for agenter

## Selvhostede runnere (eierregel, [piggyvisor#31](https://github.com/VaagenIM/piggyvisor/issues/31))

De selvhostede runnerne har tilgang til vertens Docker-socket, så en jobb på dem har root på serveren. Disse reglene skal aldri fjernes eller svekkes, og tillatelseslisten skal aldri utvides, uten at sondregronas uttrykkelig ber om det:

- Selvhostede runnere brukes bare for `push`, `workflow_dispatch`, `schedule` og `pull_request`, aldri for `pull_request_target`, `issue_comment`, `workflow_run` eller andre hendelser.
- På `pull_request` bare PR-er fra repoet selv, opprettet av en person (ikke forker, boter eller Dependabot). I et offentlig repo bare PR-er opprettet av `sondregronas`, `svHvidsten` eller `gulfarris`. Bruk tillitssjekken som allerede står i arbeidsflytene. Andre kjøringer faller tilbake til `ubuntu-latest`, eller hopper over jobber som trenger våre runnere.
- Hver arbeidsflyt setter `permissions: contents: read` øverst; en jobb øker bare det den trenger.
- Ingen `--privileged` og ingen monterte vertsstier i arbeidsflytsteg. Fjern containere og images jobben lager, i et `if: always()`-steg.
