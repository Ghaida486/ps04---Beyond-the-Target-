# Retained evidence and media retrieval

The repository includes both live-run manifests, stage receipts, decisions, briefs, draft outputs, source notes, metadata inventories, replay proof, failed collection records, policy comparison and student approval. The metadata inventories deliberately omit complete publisher text. Article source notes retain precise versions, original links and supporting passage locators.

Complete source transcripts, written-source text, raw model request/response records and downloaded original media remain in the local project archive. Cited supporting excerpts are now committed under the original asset paths with explicit export labels. Full originals are not public repository artifacts. The operational SQLite metadata index is now committed with a checksum; it does not embed the complete source texts. Source text/segments are under data/assets, index under data/evidence/index.sqlite3, original media under data/media, and model-call records under each run/model_calls.

Retrieve source media from the original URLs/enclosures using the documented collectors and extraction/transcription stages in SETUP.md; existing version hashes may differ if a publisher edits content or extraction changes. Do not present regenerated evidence as identical to the retained version.

Final audience and technical videos are accessible through the seven links in SUBMISSION.md. Production JSON records their local filenames, platforms, durations and disclosures. Raw HeyGen project links are also retained. Full final MP4 files are kept locally rather than committed to Git. Historical drafts remain labeled as drafts; published copies are in publishing/production/published-articles.

## Public evidence export scope

The two submitted runs now include exact configuration/prompt snapshots, collector streams, normalized item streams, store-exported corpus views and eligible records. Referenced text/segment paths resolve in this repository. To avoid republishing entire third-party articles and recordings, the public asset files contain the exact claim-support passages and selected timestamp segments, clearly labeled as excerpts. Non-cited candidates have provenance-only files. EXPORT_SCOPE.json lists each export. Complete original source assets remain in the local archive. The committed index can be inspected through `data/store.sh`; public excerpt files are explicitly rejected by the extractor’s full-media reuse guard. The version identifiers describe the original retained evidence, not a hash of the excerpt file.

Consequently, a fresh content check against this excerpt export has a different fingerprint from the original full-evidence approval; do not rewrite student approval to conceal that difference. Historical review.json and approval.json describe the original locally retained inputs. A reviewer can inspect the committed supporting passages, or retrieve original material using the recorded URLs.
