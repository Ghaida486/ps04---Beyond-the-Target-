# Current validation — 15 October 2026

Thirteen automated tests passed with `python3 -m unittest discover -s tests -v`. Tests cover version/duplicate storage, freshness exclusions, failed collection receipts, stale approval, missing content, insufficient evidence, credential removal, aggregator identity, substantive extraction and preserving student judgment. Fixtures are synthetic and do not count as collected evidence.

All four finished MP4 files passed full decoding. Actual publication statuses and cross-links were checked in the signed-in browser; the student reported all videos working. Outside-browser retrieval could not fetch the seven links and provides no independent anonymous-access result; the student later confirmed the articles worked following private-browser instructions. Detailed independent listening remains unverified.

## Submission integrity and reproducibility improvements

Three additional tamper tests confirm that missing cited evidence, missing prompt snapshots and a changed student approval identifier cause verification to fail. They alter only disposable test copies. The independent offline verifier executes the real store and freshness filter against retained records in a temporary root; its second-day result reproduces 3 new and 29 unchanged inputs, followed by 32 unchanged inputs on identical replay, 31 eligible records and 10 date exclusions. See REPRODUCIBILITY_REPORT.json.

All four final audio tracks were transcribed locally and compared with their authored narration. Results and timestamped recognition output are in publishing/production/audio-review. Similarity ratios are not pronunciation accuracy scores; the recorded differences remain listening flags. A complete independent listening audit is not claimed.

## Historical implementation checks

The following entries describe earlier states and are superseded by the current status above.

# Validation — 14 October 2026

- Python helpers compiled successfully with Python 3.14.7.
- Bash syntax checked for all 16 required components plus the shared workflow helper.
- Six isolated contract tests passed: duplicate/version history storage; inclusive UTC freshness boundaries and four exclusion reasons; current review, stale approval rejection and publication-link preservation; missing-content assessment; collection failure receipts; insufficient-evidence refusal before model invocation.
- Tests use fictional temporary fixtures, not submitted source evidence or human approval.
- OpenAI connection check reached the API and returned HTTP 429, credit_balance_exhausted / insufficient_quota. See api_connection_check.json. No successful AI generation or end-to-end live run is claimed.
- Two written feeds and two podcast feeds were retrieved and parsed during source research. Official YouTube links were checked against federation websites. Full media retrieval, transcription, AI selections, drafts, semantic consistency and publication are unverified.

Known limitations: media metadata-based reuse cannot detect an edit under unchanged metadata; written extraction can include navigation and requires passage inspection; audio transcription may mishear athlete names; source identity reconciliation needs editorial attention; machine checks cannot verify reasoning or full semantic consistency. Source coverage is not yet adequate/verified for the final series. No publication or student approval exists.

## Payment-free provider change

The earlier API check is historical. Codex CLI 0.156.1 is signed in with ChatGPT, and a real JSON inference check passed without API credentials. Configuration now uses codex_cli and local faster-whisper, with no paid API fallback. Existing Codex allowance applies. Local timestamped transcription passed on a short fictional speech sample. faster-whisper 1.2.1 required av 16.1.0; requirements now pins the compatible decoder range. Seven isolated contract tests pass, including API-credential removal from Codex inference.


## Live evidence work

Eight contract tests now pass, including RSS aggregator redirect/identity handling. The first actual attempt on 14 October was deliberately stopped after discovery and partial extraction to narrow podcast scope. A recovery run on the same date preserves both attempts; these are not two different-day runs. A caption HTTP 429 was recovered by downloading audio and using local transcription. Unsupported written layouts are recorded as extraction failures instead of accepting navigation as source content. Article-body extraction now targets substantive publisher containers, avoiding dynamic related-story/navigation text in version hashes. This recovery still needs end-to-end assessment and student review.

Local transcription now supports four-chunk batched CPU inference (faster-whisper base.en, beam 5), with the short synthetic check passing. Earlier cached transcripts may have used the sequential decoder; each exact transcript is retained and versioned. Names, scores and exact quotations still need audio verification.
