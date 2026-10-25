# 31: "This page changed" fingerprints

**What to build:** Once a week, a check visits each official page the Season file cites as a source, and keeps a fingerprint of the part of the page that matters (its text, without scripts, adverts or timestamps). When a fingerprint changes, it opens **one GitHub issue** in the repo listing which Sports' source pages changed, with links and the Season-file entries that cite them. It never edits the Season file. Sites that refuse automated visitors (the curling bodies) are listed as "couldn't check", rather than failing the run.

**Blocked by:** 26 (The GitHub workflow)

**Status:** ready-for-agent

- [ ] The check runs weekly on its own schedule (separate from the Refresh) and can be run by hand.
- [ ] It asks each distinct source page once, politely (descriptive User-Agent, a few seconds apart).
- [ ] Fingerprints are stored with the last-good state and committed back only when they change.
- [ ] A page's first fingerprint never opens an issue. A change opens at most one issue per run, and adds to an open review issue rather than opening duplicates.
- [ ] The issue says, in plain words, what changed and what Katie should check, and is labelled so it's easy to find.
- [ ] Fingerprinting ignores noise that changes on every visit (tested with two saved copies of a page that differ only in a timestamp).
- [ ] Tests use saved pages through the fake internet. A deliberately changed page produces one review item; an unchanged page produces none.
