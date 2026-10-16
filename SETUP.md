# Running Beyond the Target

This project implements the component contracts in ARCHITECTURE.md. Python helpers belong to individual components; shared lib/common.py contains only I/O, receipts and model transport. Bash coordinates the pipeline.

## Dependencies

Python 3.10+, Bash, Codex CLI authenticated with ChatGPT, yt-dlp, and ffmpeg on PATH. Local transcription uses faster-whisper in a project virtual environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
source .venv/bin/activate
codex login status
python3 tools/check_ai.py
```

Sign in to Codex with ChatGPT if needed using `codex login`. No OpenAI API key, API credits or payment-card setup is required by this implementation. Existing ChatGPT/Codex plan eligibility and usage limits still apply. This is not a guarantee of unlimited free cloud inference. The previously created .env.local is ignored and unused; the program does not load it. Never commit any credentials.

Model inference uses `codex exec` with the CLI default model, with no model override, through the existing ChatGPT sign-in. Exact prompts, final JSON and execution events are retained per call. It runs read-only from an isolated scratch directory with the evidence supplied on stdin, requests no tools, and removes OPENAI_API_KEY and CODEX_API_KEY from the subprocess environment. Calls never fall back to API-key billing. Actual CLI telemetry is retained; subscription usage has no assigned per-call dollar price, so model-call cost is recorded as unknown rather than zero.

Transcription uses local faster-whisper CPU int8 inference, initially base.en. The first use downloads public model weights into ignored data/models/; audio is processed on this computer. It generates segment timestamps and requires checking names, scores and quotations against audio. Local compute has no provider API charge; electricity/hardware cost is not estimated. `transcription_model` in project configuration controls the selected local model. See https://github.com/SYSTRAN/faster-whisper and https://learn.chatgpt.com/docs/non-interactive-mode .

## Configuration

config/project.json holds the topic/audience. config/sources.json holds feed, youtube and podcast URLs; consult docs/SOURCE_RESEARCH.md for validation status. Several endpoints from a producer must share publisher_id. identity_overrides maps native feed GUIDs/video IDs to a shared underlying_id when the same recording appears twice. Inspect these mappings rather than guessing independence from different domains. Each definition may use max_items to bound discovery.

The policy and prompts are saved in their prescribed locations and snapshotted into every run. Do not change a completed run's snapshots to pretend it used a later policy. Preserve policy v1 before revising, create a new run or a separate comparison run, and retain both decisions and actual prompts.

## Commands

From the repository root:

```bash
bash run.sh
bash run.sh --package runs/RUN_ID
python3 -m unittest discover -s tests -v
```

Stages can be invoked independently using the interfaces in ARCHITECTURE.md. For example:

```bash
bash processing/filter_items.sh runs/RUN_ID < runs/RUN_ID/corpus.jsonl > runs/RUN_ID/eligible.jsonl
bash editorial/select_items.sh runs/RUN_ID < runs/RUN_ID/eligible.jsonl > runs/RUN_ID/decisions.jsonl
bash review/check_content.sh runs/RUN_ID > runs/RUN_ID/review.json
```

Collectors may emit partial output and exit 1; workflows preserve output and failed receipts. The run summary distinguishes incomplete coverage and missing later stages. Fix operational errors then replay the responsible stage; preserve previous receipts. Do not label a partial collection an empty successful search.

## Evidence and identities

Only data/store.sh (through data/store.py) opens data/evidence/index.sqlite3. It keeps immutable versions, latest pointers and per-run observations. Item IDs use stable feed GUIDs/canonical producer identities or YouTube native IDs. Version IDs are SHA-256 of title, URL, publication date, producer, kind, media URL, underlying identity, extracted text and transcript segments; retrieval time and asset paths are excluded. Replaying identical data creates no new version. Written content is retrieved again and versioned if extraction changes; unchanged media metadata can reuse retained transcripts. Media reuse cannot detect silent changes under the same URL; inspect questionable media manually and clear cache by retrieving a new version deliberately. Asset paths include item and version hashes, so previous runs keep resolving.

Original media/HTML downloads are in ignored data/media/. Retained text/segments are in data/assets/. Submit referenced retained assets and evidence index along with run artifacts, and document source URLs and retrieval commands for omitted media. YouTube downloads use yt-dlp; podcasts use their enclosure URLs. A federation feed may contain navigation mixed with article text: inspect retained passages and reject pages that do not contain substantive reporting. Extraction length alone does not establish quality.

## Human handoff

Read review.json and all drafts, verify exact passages/timestamps, then create approval.json yourself with review_id, decision (approve or revise), reviewer, reviewed_at (UTC ISO timestamp), and notes describing actual review/corrections. Only the student supplies this decision. The packager reruns assessment and rejects stale approval; packaging does not regenerate drafts or recollect sources. Publication links are preserved when packaging again.

Import the scripts into Google Vids/HeyGen and create three videos. Publish the reviewed articles on Substack and videos on YouTube, add reciprocal links and source notes, and enter real URLs in package/publication_links.json and SUBMISSION.md. Complete a second live run on a different day; fixture tests do not count. Record your own technical demonstration and reflection based on the actual results.


## Current collection behavior and recovery

Bing News RSS can serve as a discovery route for configured originating publishers. Redirect URLs are decoded, original publisher hosts are checked, and a producer is counted once across all its endpoints. RSS dates are retained separately when originating article metadata or a visible source calendar date is used. A calendar date without a known time is normalized to UTC midnight with publication_time_precision=day; that timestamp does not assert a known publication hour.

Written extraction selects article-body containers and excludes navigation/related-story lists. Unknown layouts fail visibly. YouTube caption failure can be recovered with a separate audio download and local transcription. Podcast include_title_pattern narrows discovery to the selected audience-relevant episodes. Saved audio/transcripts can be reused across retries without another transcription; the original content retrieval time is retained.

For the 14 October source-date verification, the first attempt was preserved, a recovery run was held before model invocation, then the extraction stage was replayed with origin-date/canonical metadata verification. before-date-verification/ retains earlier artifacts; date_verification.json records assistant corrections. These are source-verification corrections, not the student's personal policy review. tools/resume_verified_run.sh documents the exact recovery sequence; it requires a held run and refuses to overwrite an existing verification backup.

Use `python3 tools/catalogue_sources.py runs/RUN_ID` for the actual source catalogue and `python3 tools/prepare_review.py runs/RUN_ID` for a worksheet drawn from actual decisions. Neither tool supplies student approval. `python3 tools/compare_runs.py runs/OLD_ID runs/NEW_ID` records comparisons and explicitly labels same-day attempts. A same-day retry never replaces the required second live day.

## Offline verification of the submitted release

Run `python3 tools/verify_submission.py` from the repository root. Python’s standard library and Bash are sufficient; no API credential, model download or transcription dependency is needed for this verification. It checks the real retained artifacts and exercises storage, duplicate replay and freshness filtering in a temporary copy. It does not rerun live collection or editorial AI decisions. The ordinary full pipeline still requires the dependencies and provider login described above. The workflow `.github/workflows/verify-submission.yml` runs contract tests and the offline verifier on each push.

The contract suite additionally needs BeautifulSoup: `python3 -m pip install -r requirements-test.txt`. This small test dependency set avoids downloading Whisper or model weights just to inspect the submitted evidence. The first clean GitHub runner exposed the missing dependency; the workflow now installs it explicitly.
