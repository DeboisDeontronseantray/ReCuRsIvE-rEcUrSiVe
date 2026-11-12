# Ch 4 commenter-prompt pipeline (Commercial News Break), home-only
Built 2026-10-27 16:10-16:35 CT on trundle's 4:10 PM CT direction (prep for going live after the Run 2 review). Built and tested at $0, dry-run only.
Rules come from bible-v2.yaml: commenter-vision-20261027-1514, voice-post-and-run-plan-20261027-1443, channel.rules/tv_safe_rules/banned/negative_safety_tags.

## Layout
- `config.json`: **LIVE_ENABLED=false**, xAI cap $150 (warn $120), max 2 tries, models, -14 LUFS
- `schema/commenter-prompt.schema.json`, `inbox/` (drop zone), `inbox/processed/`
- `blocklists.json`: gate lists (kids, real brands/people, songs/shows, sexual, violence, hate, tactics, Bible banned). Add-only.
- `pipeline.py`: intake → gate → wrap → render (guarded) → post → outbox manifest
- `accepted/ rejected/ wrapped/ renders/ outbox/ logs/` (logs: intake, gate, render, post .jsonl)
- `HANDOFF-CONTRACT.md`: in/out contract for X Live Stream and playout

## Run
    python3 pipeline.py run-all --dry-run          # intake+gate+wrap+cost check, no API call
    python3 pipeline.py render --id <id>            # real render; refuses while LIVE_ENABLED=false
    python3 pipeline.py post --id <id> [--src mp4]  # loudness, OCR check, self-reflection overlay, outbox + manifest
Render reuses the render_clip_v2.py request logic: grok-imagine-video-1.5 at 480p with cast refs, and lite when no cast is in the shot. Before any call it reads the xAI month total from /workspace/fakenews/spend.jsonl, warns at $120 and stops if the clip would pass $150. It also stops after 2 tries per clip and never retries on its own. Every real call is logged to spend.jsonl.
The self-reflection line ("idk why I'm doing this but @handle thinks it's a good idea") is added only in post as text (and later TTS). It is never generated in the picture.

## Go-live checklist (trundle)
1. Review Run 2 and say whether it's accepted.
2. Approve the commenter-prompt rules (board item B2, Story Bot drafts) and this gate's blocklists.
3. Pick the self-reflection format: text overlay, TTS, or both. Pick the TTS voices for Bill's eruptions, the guard and the "You're watching" ID. Voice clones stay on hold.
4. Flip `LIVE_ENABLED` to true in config.json (trundle's yes only).
5. Set a per-session spend limit inside the $150 xAI month.
6. Give the airing yes: which clips, which channel or stream, and when. Playout can only load manifest rows with `thundertrundle_air_yes: true`.
## Open questions
- Intake source: post-broadcast chat or live replies/mentions (X-LIVE-PREP item 7). X livestream reads need an X reconnect (broadcast.read).
- Should the gate be keyword-only (today) or also get a model review step? Keyword matching is conservative and can over-reject (for example, "shoot" in "photo shoot").
- Should continuity (where a clip sits in the story, and the end frame it continues from) be added by Story Bot per prompt?
- Out-of-character detection uses a verb list and Bill's calm default. Story Bot should own a per-character "in character" list.
- The OCR check uses tesseract with 5+ letter words and can miss garbled text. A failed check holds the clip for review.

## Prompt injections (added 2026-10-27 16:40 CT on trundle's 4:33 PM CT request; every injection is a draft)
- Library: `injections.json`. Each entry has id, kind (spoken_line / visual_beat / overlay_text), text, requires_people, speakers, apply_when (weak_score / every_nth / manual) and delivery (post_tts / in_prompt_soft / overlay). Every status is `draft` until trundle approves it.
- Switch: `config.json` `INJECTIONS_ENABLED` (true), `max_injections_per_clip` 2, `inject_every_nth` 5, `weak_score_threshold` 2.
- Weak-prompt score (0-4): +1 for under 6 words, +1 more for under 3 words, +1 if no cast is named, +1 if there's no action verb.
- How injections are applied:
  - The commenter text is never edited.
  - Visual beats go into a separate `[CHANNEL INJECTION ... in addition ...]` block after `[END COMMENTER REQUEST]`.
  - Spoken lines never go into the video prompt. They become `post_tts_cues` (character, line, timing, voice=TBD) in the manifest and in `outbox/<id>_tts_cues.json`. No TTS is generated until trundle picks the voices; the cue file is the audio placeholder.
  - Overlay text is drawn in post only.
  - Injections that need people, and spoken lines from cast, are skipped when no cast is in the shot.
  - A prompt can request one by name with `"manual_injections": ["inj-..."]`.
- Logging: every pick goes to `logs/injections.jsonl` and to the manifest row (`injections`, `injections_status: draft-needs-thundertrundle-ok`).
- Go-live checklist addition: trundle approves each injection's wording (especially `inj-donation-line`), its voice, and whether INJECTIONS_ENABLED stays on.

## Money rule (trundle 2026-10-27 16:35 CT)
No injection may mention amounts, prices, donations, or ask for money/support. Channel flair stays subtle (e.g. "Comments steer this channel.").

## Single inbound route (2026-10-27 16:45 CT, per COMMENTER-CLIP-PATH-20261027.md, Smart Home Lead)
- The only intake is `inbox/xls-<source>-<message_id>.json` written by **Story Bot**. The flow is XLS chat → trundle APPROVED → Story Bot wraps and sets IN_STORY → this inbox.
- A file is accepted only if all of these hold:
  - the name matches `xls-*.json`;
  - it has the required fields;
  - `intake_by == "Story Bot"`;
  - it carries a trundle-approved marker (`status` APPROVED or IN_STORY, or `thundertrundle_approved: true`);
  - the text matches `commenter_text_sha256` when present.
- Anything else is moved to `rejected/`, with the reason logged in `logs/intake.jsonl`.
- Dedupe: an `id` or `source_post_id` already in `logs/seen.jsonl`, `outbox/manifest.jsonl` or `inbox/processed/` is skipped and moved to `inbox/processed/dup-*`. A comment can never render twice.
- Raw-comment intake is retired but kept as `intake_legacy()`, behind `RAW_INTAKE_ENABLED=false`. pending-approval/ is not read.
- Credit line: the record's `credit_line` is used; if it's missing, the template in on-screen-text.md is used. The credit is drawn in post on every commenter clip (`CREDIT_LINE_ENABLED`, default true).
- Story Bot's `wrapped_prompt` is stored in the manifest. CNB still runs its own gate and wrapper on the verbatim text as a second check.
- Injections: `inj-donation-line` is blocked (trundle 4:35 PM CT: no money asks). The new draft `inj-disclosure-subtle` says "The comments steer this place."

## Auto mode (2026-10-27 16:50 CT, trundle approved building it at 4:38 PM CT). Every switch is OFF by default.
- `AUTO_APPROVE_PROMPTS=false` (Phase B). When it's on, intake also accepts `status: AUTO_APPROVED` and stamps `approved_by: "auto-gate"`. The prompt still has to pass the gate (brands, kids, real people, money talk, cartoonish wording; the money and cartoonish lists were added to blocklists.json). The older key `AUTO_APPROVE_ENABLED` is no longer read.
- Post checks on every clip:
  - OCR for stray text.
  - A frame check. Frames are saved to `outbox/held/frames_*`. Kid and logo detection isn't reliable locally (`FRAME_CHECK_MODE=flag_for_review`), and this box's cv2 build has no face detector, so **every clip is currently held for human review**.
  - Loudness of -14 LUFS ±1.
  Any failure moves the clip to `outbox/held/` with a `_HELD.json` reason file and the manifest status `held-not-for-air`.
- `AUTO_AIR_YES=false`. When it's on, clips that pass every check get `thundertrundle_air_yes: true` and `air_yes_by: "auto-gate"`. **This needs trundle's explicit flip AND an update to COMMENTER-CLIP-PATH-20261027.md**, which today requires a per-clip trundle AIR_OK.
- Stops:
  - `KILL_SWITCH` blocks auto-approve, renders and auto air-yes.
  - `SESSION_SPEND_CAP_USD=5` and `MAX_CLIPS_PER_HOUR=6`, tracked per `SESSION_ID` in logs/session.jsonl.
  - `AUTO_REVERT_FLAG_LIMIT=2`: two held clips in a session set both auto switches to false. It backs up the config first and logs to logs/auto_revert.jsonl.
- Tests: `tests/auto-1650/run_tests.py`, `t9_stub.py`, `results.txt`. They restore the config afterwards.

## 2026-10-27 17:30 CT — clean-master allowlist + LINEAGE row types (CNB)
- Watchlist rows with `row_type: "clean_master_allow"` are an exact-sha256 allowlist (raw/mb_*.mp4 + CLEAN-SOURCES.json masters). An exact sha match wins over any watchlist phash/dHash/name hit in `slipcheck.watch_guard` (used by `pipeline.input_guard`) and in slipcheck provenance. Readers (Story Bot checker) must skip these rows when matching hashes.
- LINEAGE.jsonl readers: rows without `file` are corrections; they carry `row_type: "correction"` and `correction_for_sha256` pointing at the original row's sha256. Every correction row written by CNB/pipeline/slipcheck must carry `row_type`.

## Made-up path (2026-10-27 17:45 CT, CNB; trundle 17:25 CT "make more up… auto approval from the start")
- `made_up.py <prompts.json> [--dry-run] [--only ID]`: CNB-written prompts, `origin: made_up`, `intake_by: CNB made_up path`, `approved_by: auto-gate`. Does NOT forge Story Bot intake.
- Runs: AUTO_APPROVE_PROMPTS/KILL_SWITCH check → dedupe → gate → wrap → injections (spoken lines dropped) → input_guard → month cap/warn, 2 tries, session cap, clips/hour → one render → post (OCR, frame check, LUFS) → slipcheck + provenance → LINEAGE row in 4.3.
- Does not require LIVE_ENABLED (kept false for live intake/air). thundertrundle_air_yes always false. Dry runs are not counted against the session cap.
- First batch: made_up_prompts_20261027.json (mu1745-01..06), contact sheet outbox/mu1745-contact-sheet.png.

## Audio leveling gate (trundle standing rule, 2026-10-27 17:36 CT; $0, ffmpeg only)
Every finished clip, every channel, is checked before queue. `audiolevel.py` (also `pipeline.py audiolevel <mp4...> [--report-only]`); runs automatically in post-render QA (`manifest`) next to slipcheck.
- Targets: -16 LUFS integrated (±1 LU), true peak ≤ -1.5 dBTP, LRA ≤ 7 LU (gated only on clips ≥15 s; EBU LRA is unreliable on 6–10 s clips), sub-120 Hz share ≤ 0.35, no mains-hum harmonic (60–600 Hz) both ≥10 dB above neighbours and >1% of band energy. Block rule: consecutive clips in a block may differ by ≤2 LU (`audiolevel.py block f1 f2 ...` in play order).
- Fix (on fail): NEW file `<src minus _parody>_audiofix_parody.mp4` beside the source; never overwrites, never touches masters. Chain: highpass 85 Hz → notches on detected 60·k Hz hum (k=1..10) and any 85–200 Hz resonance (e.g. binoculars/cloak ~110 Hz) → lowshelf 200 Hz -4 dB → [optional brown-noise room tone, product ads] → two-pass loudnorm (I=-16, TP=-1.5, LRA=7, linear) → trim pass (gain + limiter at -2.5 dBFS, re-encoded from source) if loudnorm undershoots. Video `-c:v copy`; audio AAC 128k / 44.1 kHz.
- The fixed copy becomes `queue_file`; a clip that still fails is held. Values (lufs_i, true_peak, lra, audio_leveled) go to `outbox/AUDIO-LEVELS.jsonl`; Ch4 air copies also log to `AUDIO-LEVELS.jsonl` beside LINEAGE and an `audio_post` LINEAGE row (source_sha256, source_global_no, out_sha256, file, tags copied; no new global_no/gen — same picture, same tag).
