# Persistent evidence index

`index.sqlite3` is a copy of the operational SQLite metadata index, including immutable versions, latest pointers and run observations. `manifest.json` records its checksum and scope. It contains source records and paths, not full article or audio contents. Only `data/store.sh` and its helper query or mutate this database.

Inspect it from the repository root:

```bash
bash data/store.sh list
bash data/store.sh get ITEM_ID VERSION_ID
```

Do not run a mutating replay against the submitted index merely to inspect it. `python3 tools/verify_submission.py` reconstructs a separate index in a temporary copy and verifies replay behavior without changing this file or historical run artifacts.

Public text/segment assets contain labeled claim-support excerpts. Collected records not cited in the series have provenance-only text files; they must not be mistaken for complete source content. Full originals remain in the local archive. Regenerating a source from its URL can produce a different version if the publisher has edited it.
