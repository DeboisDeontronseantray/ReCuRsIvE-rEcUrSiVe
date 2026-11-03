# PATHS INVENTORY: hardcoded `/workspace` paths

Status: **PROPOSED.** Nothing is changed by this document (Decision 10: inventory only). Config keys, defaults and the migration approach are proposals pending approval.

Scope: every git-tracked text file at commit `f34b704` on `plan/prompt-assembly-v1`, excluding `docs/`. **2615 occurrences, 607 distinct paths, 342 files.**

The MANIFEST counted more hits (for example 1884 for `/workspace/fakenews/channel-ready`) because it also scanned files that are not in the repo: the held-out `genealogy/LINEAGE.jsonl` and `data/spend/ledger.jsonl`, and the 44 git-ignored `story-engine/data/{smoke,exports,continuity}` files. Prefixes that only appeared there (`/workspace/media-central`, `/workspace/colormatch-20261029`, `/workspace/c4box`) have no hits in the repo.

Regenerate the counts with: `git ls-files | grep -v '^docs/' | xargs grep -oh '/workspace/[A-Za-z0-9._@+/-]*' | sort | uniq -c | sort -rn`.

## 1. Proposed config keys (longest prefix wins)

Resolution order for every key (PROPOSED): environment variable → git-ignored local `tt_paths.json` → repo-relative default. If there is no default and nothing is set, the feature that needs it is skipped with a clear message. It never silently falls back to `/workspace`. On the live box, setting no variables must keep today's behavior: each key's live value is the prefix itself.

| Config key | Prefix (live-box value) | Repo-relative default | Hits | Distinct paths | Files | Note |
|---|---|---|---:|---:|---:|---|
| `TT_ODYSSEY_APPLY_CHECK` | `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/tools/apply_check.py` | `prompts/experiments/odyssey-design-20261030/tools/apply_check.py` | 1 | 1 | 1 | already wired (Decision 9) in tools/apply_check_v4.py |
| `TT_PROMPTS_V4` | `/workspace/thunder-trundle/prompts/system-v4-20261030` | `prompts/system-v4-20261030` | 211 | 21 | 105 |  |
| `TT_EXPERIMENTS` | `/workspace/thunder-trundle/prompts/experiments` | `prompts/experiments` | 450 | 50 | 226 | only odyssey apply_check.py is in the repo; everything else is absent |
| `TT_PROMPTS` | `/workspace/thunder-trundle/prompts` | `prompts` | 10 | 9 | 3 | env var already read by story-engine/engine/assemble_prompt.py |
| `TT_CHANNELS` | `/workspace/thunder-trundle/channels` | (none; not in repo) | 75 | 19 | 58 | channel refs/sheets (images); not in repo |
| `TT_LINEAGE` | `/workspace/thunder-trundle/lineage` | (none; not in repo) | 4 | 1 | 2 | LINEAGE.jsonl is held out of the repo |
| `TT_STORY_DIR` | `/workspace/thunder-trundle/story` | (none; not in repo) | 9 | 9 | 9 |  |
| `TT_THUNDER_ROOT` | `/workspace/thunder-trundle` | (none; not in repo) | 19 | 7 | 14 | other thunder-trundle dirs (archive, harness, specs, handoffs, coordination) |
| `TT_STORY_ENGINE` | `/workspace/streaming/story-engine` | `story-engine` | 1152 | 139 | 41 |  |
| `TT_QUEUES` | `/workspace/streaming/queues` | `story-engine/queues` | 304 | 125 | 6 | repo copies were symlink targets (MANIFEST) |
| `TT_COMMENTER_PIPELINE` | `/workspace/streaming/commenter-pipeline` | (none; not in repo) | 13 | 4 | 3 | not in repo; commenter images stay OFF |
| `TT_STREAMING_ROOT` | `/workspace/streaming` | (none; not in repo) | 12 | 5 | 7 | loose streaming files (NAME-COVER, PULLED, UNUSABLE, shared_lib) |
| `TT_CHANNEL_READY` | `/workspace/fakenews/channel-ready` | (none; not in repo) | 260 | 175 | 42 | rendered/airing media; out of scope for assembly |
| `TT_SPEND_LEDGER` | `/workspace/fakenews/spend.jsonl` | (none; not in repo) | 3 | 1 | 3 | spend data; never read by the assembler |
| `TT_FAKENEWS_ROOT` | `/workspace/fakenews` | (none; not in repo) | 1 | 1 | 1 |  |
| `TT_SPEND_DIR` | `/workspace/shared/spend` | (none; not in repo) | 5 | 1 | 4 | spend data; never read by the assembler |
| `TT_SHARED_STREAMING` | `/workspace/shared/streaming` | (none; not in repo) | 38 | 17 | 12 |  |
| `TT_MEDIA_LIBRARY` | `/workspace/shared/media-library` | (none; not in repo) | 18 | 10 | 3 | media; not in repo |
| `TT_SHARED_ROOT` | `/workspace/shared` | (none; not in repo) | 10 | 4 | 6 | INVENTORY, vision, build-queue, weekly-review, handoffs |
| `TT_BACKUPS` | `/workspace/backups` | (none; not in repo) | 10 | 3 | 2 | backups are excluded from the repo |
| `TT_DIRECTOR_DIR` | `/workspace/director` | (none; not in repo) | 7 | 3 | 7 | Director briefs folder on the live box |
| `TT_DIAG` | `/workspace/diag` | (none; not in repo) | 2 | 1 | 1 | diagnostic media |
| `TT_DE_PARITY` | `/workspace/de-parity` | (none; not in repo) | 1 | 1 | 1 |  |

Already configurable today: `TT_PROMPTS` and `TT_LOCKS` (read by `story-engine/engine/assemble_prompt.py`) and `TT_ODYSSEY_APPLY_CHECK` (Decision 9, `prompts/system-v4-20261030/tools/apply_check_v4.py`).

## 2. Code files (migration targets)

These are the occurrences in `.py/.sh/.js/.ts/.tsx` files. A later migration PR (Decision 10, not approved yet) would replace each literal with the key's resolver. Any such PR must prove that prompt outputs stay byte-identical (v44 gate 53/53, NP16 parity test) and that the test suite does not regress. Comment-only and docstring mentions are included; the migration PR decides whether to touch them.

77 occurrences in 34 code files.

| File | Line | Path | Key |
|---|---:|---|---|
| `prompts/system-v4-20261030/tests/test_v41.py` | 3 | `/workspace/thunder-trundle/channels/11-fist-theater/refs/sheets/SHEET_CH11_CAST_v1.jpg` | `TT_CHANNELS` |
| `prompts/system-v4-20261030/tests/test_v42.py` | 5 | `/workspace/thunder-trundle/channels/11-fist-theater/refs/sheets/SHEET_CH11_CAST_v1.jpg` | `TT_CHANNELS` |
| `prompts/system-v4-20261030/tests/test_v48.py` | 5 | `/workspace/thunder-trundle/channels/11-fist-theater/refs/sheets/SHEET_CH11_CAST_v1.jpg` | `TT_CHANNELS` |
| `prompts/system-v4-20261030/tools/apply_check_v4.py` | 10 | `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/tools/apply_check.py` | `TT_ODYSSEY_APPLY_CHECK` |
| `prompts/system-v4-20261030/tools/meta_check.py` | 9 | `/workspace/thunder-trundle/prompts/experiments/round8-prep-20261030/CHARACTERS.jsonl` | `TT_EXPERIMENTS` |
| `prompts/system-v4-20261030/tools/regen_pending_v4.py` | 7 | `/workspace/thunder-trundle/prompts/experiments` | `TT_EXPERIMENTS` |
| `prompts/system-v4-20261030/tools/regen_pending_v4.py` | 12 | `/workspace/thunder-trundle/prompts/experiments/round3-20261030/clips/C16-20pm-c3/refs_small/SHEET_CH16_WREN_v1.jpg` | `TT_EXPERIMENTS` |
| `prompts/system-v4-20261030/tools/regen_pending_v4.py` | 13 | `/workspace/thunder-trundle/prompts/experiments/round3-20261030/clips/C16-20pm-c3/refs_small/SHEET_CH16_GRAVES_ARCHIVIST_GUARD_v1.jpg` | `TT_EXPERIMENTS` |
| `prompts/system-v4-20261030/tools/regen_v41.py` | 10 | `/workspace/thunder-trundle/channels` | `TT_CHANNELS` |
| `prompts/system-v4-20261030/tools/static_flip_v3.py` | 9 | `/workspace/thunder-trundle/prompts/experiments/round9-design-20261030/tools/static_flip_v2.py` | `TT_EXPERIMENTS` |
| `story-engine/data/live/starters/build_starters.py` | 2 | `/workspace/streaming/story-engine/live` | `TT_STORY_ENGINE` |
| `story-engine/data/live/starters/build_starters.py` | 22 | `/workspace/streaming/story-engine/data/live/starters/comment-starters-20261027.json` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-pilot-20261027/gen-v2-backup-20261027-1421.py` | 2 | `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/bill-B2.png` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-pilot-20261027/gen-v2-backup-20261027-1421.py` | 2 | `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/mira-C.png` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-pilot-20261027/gen-v2-backup-20261027-1421.py` | 2 | `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/tim-E5.png` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-pilot-20261027/gen-v2-backup-20261027-1421.py` | 2 | `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/osmund-B.png` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-pilot-20261027/gen.py` | 2 | `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/bill-B2.png` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-pilot-20261027/gen.py` | 2 | `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/bill-B2-full.png` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-pilot-20261027/gen.py` | 2 | `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/bill-B2-side.png` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-pilot-20261027/gen.py` | 2 | `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/mira-C.png` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-pilot-20261027/gen.py` | 2 | `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/mira-C-full.png` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-pilot-20261027/gen.py` | 2 | `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/mira-C-side.png` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-pilot-20261027/gen.py` | 2 | `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/tim-E5.png` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-pilot-20261027/gen.py` | 2 | `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/tim-E5-sideback.png` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-pilot-20261027/gen.py` | 2 | `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/osmund-B.png` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-pilot-20261027/gen.py` | 2 | `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/osmund-B-full.png` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-pilot-20261027/gen.py` | 2 | `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/osmund-B-side.png` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/render_clip.py` | 2 | `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/render_clip.py` | 38 | `/workspace/fakenews/spend.jsonl` | `TT_SPEND_LEDGER` |
| `story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/render_clip_v2.py` | 2 | `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/render_clip_v2.py` | 39 | `/workspace/fakenews/spend.jsonl` | `TT_SPEND_LEDGER` |
| `story-engine/data/pilots/ch04-forward-supply-run2-20261027/build_run2.py` | 3 | `/workspace/streaming/story-engine` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-run2-20261027/remakes/build_remakes.py` | 3 | `/workspace/streaming/story-engine/live` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-run2-20261027/remakes/build_remakes.py` | 54 | `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2-remakes-20261027.json` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/render_clip_v2.py` | 2 | `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027` | `TT_STORY_ENGINE` |
| `story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/render_clip_v2.py` | 39 | `/workspace/fakenews/spend.jsonl` | `TT_SPEND_LEDGER` |
| `story-engine/data/shows/dress-inspection-20261027/build.py` | 4 | `/workspace/streaming/story-engine/live` | `TT_STORY_ENGINE` |
| `story-engine/data/shows/dress-inspection-20261027/build.py` | 7 | `/workspace/streaming/story-engine` | `TT_STORY_ENGINE` |
| `story-engine/data/shows/dress-inspection-20261027/build.py` | 8 | `/workspace/fakenews/channel-ready/thunder-trundle/4_Military-Boutique` | `TT_CHANNEL_READY` |
| `story-engine/data/shows/dress-inspection-20261027/build.py` | 9 | `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/lineage-tagfade-20261027` | `TT_CHANNEL_READY` |
| `story-engine/data/shows/dress-inspection-20261027/build.py` | 97 | `/workspace/director/brief-dress-inspection-20261027.md` | `TT_DIRECTOR_DIR` |
| `story-engine/data/shows/dress-inspection-20261027/build.py` | 106 | `/workspace/streaming/PULLED-20261027.jsonl` | `TT_STREAMING_ROOT` |
| `story-engine/data/shows/dress-inspection-20261027/build.py` | 106 | `/workspace/shared/streaming/PULLED-20261027.json` | `TT_SHARED_STREAMING` |
| `story-engine/data/shows/the-efficiency-review-20261027/build.py` | 4 | `/workspace/streaming/story-engine/live` | `TT_STORY_ENGINE` |
| `story-engine/data/shows/the-efficiency-review-20261027/build.py` | 7 | `/workspace/streaming/story-engine` | `TT_STORY_ENGINE` |
| `story-engine/data/shows/the-efficiency-review-20261027/build.py` | 107 | `/workspace/director/brief-the-efficiency-review-20261027.md` | `TT_DIRECTOR_DIR` |
| `story-engine/data/stills-20261027/build.py` | 2 | `/workspace/streaming/story-engine/live` | `TT_STORY_ENGINE` |
| `story-engine/data/stills-20261027/build.py` | 3 | `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/raw` | `TT_CHANNEL_READY` |
| `story-engine/data/stills-20261027/build.py` | 52 | `/workspace/streaming/story-engine/data/stills-20261027/product-stills-prompts-20261027.json` | `TT_STORY_ENGINE` |
| `story-engine/engine/assemble_prompt.py` | 13 | `/workspace/thunder-trundle/prompts` | `TT_PROMPTS` |
| `story-engine/engine/assemble_prompt.py` | 432 | `/workspace/thunder-trundle/prompts/looks` | `TT_PROMPTS` |
| `story-engine/engine/resolve_embed.py` | 6 | `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/LINEAGE.jsonl` | `TT_CHANNEL_READY` |
| `story-engine/live/build_ref_index.py` | 9 | `/workspace/shared/media-library/ch04-military-boutique/cnb-series` | `TT_MEDIA_LIBRARY` |
| `story-engine/live/checker.py` | 51 | `/workspace/fakenews/channel-ready/thunder-trundle/4_Military-Boutique` | `TT_CHANNEL_READY` |
| `story-engine/live/checker.py` | 75 | `/workspace/shared/streaming/tag-slip-watchlist.jsonl` | `TT_SHARED_STREAMING` |
| `story-engine/live/checker.py` | 349 | `/workspace/streaming/queues/COMMENT-PROMPTS.jsonl` | `TT_QUEUES` |
| `story-engine/live/checker.py` | 585 | `/workspace/streaming/shared_lib` | `TT_STREAMING_ROOT` |
| `story-engine/live/checker.py` | 611 | `/workspace/de-parity/pickup.py` | `TT_DE_PARITY` |
| `story-engine/live/intake.py` | 31 | `/workspace/shared/streaming/x-intake/queue/storybot-inbox` | `TT_SHARED_STREAMING` |
| `story-engine/live/intake.py` | 80 | `/workspace/shared/streaming/x-intake/export_cnb.py` | `TT_SHARED_STREAMING` |
| `story-engine/live/post_audit.py` | 9 | `/workspace/shared/streaming/tag-slip-watchlist.jsonl` | `TT_SHARED_STREAMING` |
| `story-engine/live/tests/test_assemble_prompt.py` | 2 | `/workspace/streaming/story-engine/engine` | `TT_STORY_ENGINE` |
| `story-engine/live/tests/test_assemble_prompt.py` | 5 | `/workspace/streaming/story-engine/channels/04-military-boutique/shows/black-ice/ep01-20261027/segments/BI-12.yaml` | `TT_STORY_ENGINE` |
| `story-engine/live/tests/test_dense_prompt.py` | 3 | `/workspace/streaming/story-engine/engine` | `TT_STORY_ENGINE` |
| `story-engine/live/tests/test_dense_prompt.py` | 6 | `/workspace/streaming/story-engine/channels/04-military-boutique/shows/black-ice/ep01-20261027/segments` | `TT_STORY_ENGINE` |
| `story-engine/live/tests/test_live.py` | 287 | `/workspace/fakenews/channel-ready/thunder-trundle/4_Military-Boutique` | `TT_CHANNEL_READY` |
| `story-engine/live/tests/test_live.py` | 372 | `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/lineage-tagged-20261027/20261026_231528_4_1_Military-Boutique_tactical-helmet-pedestal_parody_salesadBA_tagged_parody.mp4` | `TT_CHANNEL_READY` |
| `story-engine/live/tests/test_look.py` | 3 | `/workspace/streaming/story-engine/engine` | `TT_STORY_ENGINE` |
| `story-engine/live/tests/test_look.py` | 5 | `/workspace/streaming/story-engine/channels/04-military-boutique/shows/black-ice/ep01-20261027/segments/BI-01.yaml` | `TT_STORY_ENGINE` |
| `story-engine/live/tests/test_look.py` | 24 | `/workspace/streaming/story-engine/engine/assemble_prompt.py` | `TT_STORY_ENGINE` |
| `story-engine/live/tests/test_node_rows.py` | 2 | `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/LINEAGE.jsonl` | `TT_CHANNEL_READY` |
| `story-engine/server/app/model_routing.py` | 42 | `/workspace/shared/INVENTORY/accounts-subs-apis.md` | `TT_SHARED_ROOT` |
| `story-engine/server/app/spend.py` | 3 | `/workspace/shared/INVENTORY/accounts-subs-apis.md` | `TT_SHARED_ROOT` |
| `story-engine/server/app/spend.py` | 6 | `/workspace/shared/spend/xai-month.md` | `TT_SPEND_DIR` |
| `story-engine/server/app/spend.py` | 22 | `/workspace/shared/spend/xai-month.md` | `TT_SPEND_DIR` |
| `story-engine/server/app/tv/export_cnb.py` | 3 | `/workspace/shared/streaming/grok-imagine-90s-news-guide.md` | `TT_SHARED_STREAMING` |
| `story-engine/tests/test_queue_policy.py` | 3 | `/workspace/streaming/story-engine/rules/queue-policy.yaml` | `TT_STORY_ENGINE` |

## 3. Data and doc files

Paths inside JSON/JSONL/YAML data (for example `image_path` and `reference_image_paths` in `prompts_v4*/**/*.args.json`) and in Markdown notes are **records, not configuration**. They are proposed to stay as-is: `build()` and the gates treat them as opaque strings, and `prompts_v44/` must not be edited. New code resolves only the paths it creates itself through the keys above.

## 4. Every distinct path, grouped by prefix

Each row gives the path, its occurrence count, and the number of tracked files that contain it.

<details><summary><code>/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/tools/apply_check.py</code> → <code>TT_ODYSSEY_APPLY_CHECK</code> (1 paths, 1 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/tools/apply_check.py` | 1 | 1 |

</details>

<details><summary><code>/workspace/thunder-trundle/prompts/system-v4-20261030</code> → <code>TT_PROMPTS_V4</code> (21 paths, 211 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/thunder-trundle/prompts/system-v4-20261030/prompts_v44` | 1 | 1 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/refs_side/CONCIERGE_threequarter_face.png` | 20 | 17 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/refs_side/GRAVES_guard_side_full.png` | 7 | 6 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/refs_side/GIDEON_QUILL_side_full.png` | 7 | 6 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/refs_side/GIDEON_QUILL_threequarter_face.png` | 81 | 68 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/refs_side/WREN_side_full.png` | 13 | 11 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/state_stills_v42/BEAR_P07-1.png` | 5 | 4 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/state_stills_v42/DALE_P12-1.png` | 5 | 4 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/state_stills_v42/DEV_P08-1.png` | 5 | 4 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/state_stills_v42/MAE_P03-2.png` | 5 | 4 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/state_stills_v42/OSCAR_P08-1.png` | 5 | 4 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/state_stills_v42/PENDING/BEAR_P07-2.png` | 6 | 4 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/state_stills_v42/PENDING/DALE_P12-2.png` | 6 | 4 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/state_stills_v42/PENDING/DEV_P08-2.png` | 6 | 4 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/state_stills_v42/PENDING/OSCAR_P08-2.png` | 6 | 4 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/state_stills_v42/PENDING/RITA_P07-2.png` | 6 | 4 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/state_stills_v42/PENDING/SABLE_P09-2.png` | 6 | 4 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/state_stills_v42/PENDING/VIK_P09-2.png` | 6 | 4 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/state_stills_v42/RITA_P07-1.png` | 5 | 4 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/state_stills_v42/SABLE_P09-1.png` | 5 | 4 |
| `/workspace/thunder-trundle/prompts/system-v4-20261030/state_stills_v42/VIK_P09-1.png` | 5 | 4 |

</details>

<details><summary><code>/workspace/thunder-trundle/prompts/experiments</code> → <code>TT_EXPERIMENTS</code> (50 paths, 450 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/thunder-trundle/prompts/experiments` | 1 | 1 |
| `/workspace/thunder-trundle/prompts/experiments/density-sweep-v1/renders/` | 2 | 2 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/clips/NP01_last.png` | 7 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/clips/NP02_last.png` | 7 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/clips/NP03_last.png` | 7 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/clips/NP04_last.png` | 7 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/clips/NP05_last.png` | 7 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/clips/NP06_last.png` | 7 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/clips/NP07_last.png` | 8 | 7 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/clips/NP08_last.png` | 7 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/clips/NP09_last.png` | 7 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/clips/NP15_last.png` | 8 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/clips/SU1_last.png` | 7 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/clips/SU2_last.png` | 7 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/clips/SU3_last.png` | 7 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/clips/SU4_last.png` | 7 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/clips/SU5_last.png` | 7 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/state_stills/GIDEON_QUILL_full_` | 29 | 21 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/state_stills/GIDEON_QUILL_full_SU1.png` | 8 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/state_stills/cap_detail.png` | 8 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/state_stills/final` | 8 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/state_stills/gloves_detail.png` | 8 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/state_stills/rolling` | 8 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/odyssey-design-20261030/ODYSSEY/state_stills/tape_detail_SU1.png` | 8 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/round3-20261030/clips/C16-20pm-c3/refs_small/SHEET_CH16_GRAVES_ARCHIVIST_GUARD_v1.jpg` | 2 | 2 |
| `/workspace/thunder-trundle/prompts/experiments/round3-20261030/clips/C16-20pm-c3/refs_small/SHEET_CH16_WREN_v1.jpg` | 3 | 3 |
| `/workspace/thunder-trundle/prompts/experiments/round4-20261030/refs/MADAM_HU.png` | 7 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/round5-20261030/frames/CH11-lobby.png` | 70 | 58 |
| `/workspace/thunder-trundle/prompts/experiments/round8-prep-20261030/CHARACTERS.jsonl` | 1 | 1 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/clips/D1/D1_last.png` | 36 | 31 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/clips/P02-2/P02-2_last.png` | 8 | 7 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/clips/P03-2/P03-2_last.png` | 8 | 7 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/clips/P05-2/P05-2_last.png` | 8 | 7 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/clips/P06-2/P06-2_last.png` | 8 | 7 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/clips/P07-1/P07-1_last.png` | 8 | 7 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/clips/P07-2/P07-2_last.png` | 8 | 7 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/clips/P08-1/P08-1_last.png` | 8 | 7 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/clips/P08-2/P08-2_last.png` | 8 | 7 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/clips/P09-1/P09-1_last.png` | 8 | 7 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/clips/P09-2/P09-2_last.png` | 8 | 7 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/clips/P10-1/P10-1_last.png` | 6 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/clips/P10-2/P10-2_last.png` | 6 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/clips/P12-1/P12-1_last.png` | 8 | 7 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/clips/P12-2/P12-2_last.png` | 8 | 7 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/clips/P14-1/P14-1_last.png` | 6 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/clips/P14-2/P14-2_last.png` | 6 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/clips/P16-1/P16-1_last.png` | 8 | 7 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/refs/C16-20pm-c3_FIRSTFRAME.png` | 8 | 7 |
| `/workspace/thunder-trundle/prompts/experiments/round9-20261030/refs/STATE_STEVE_E1_lizard.png` | 7 | 6 |
| `/workspace/thunder-trundle/prompts/experiments/round9-design-20261030/tools/static_flip_v2.py` | 1 | 1 |

</details>

<details><summary><code>/workspace/thunder-trundle/prompts</code> → <code>TT_PROMPTS</code> (9 paths, 10 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/thunder-trundle/prompts` | 1 | 1 |
| `/workspace/thunder-trundle/prompts/02-news/_channel.md` | 1 | 1 |
| `/workspace/thunder-trundle/prompts/04-military-boutique/_channel.md` | 2 | 2 |
| `/workspace/thunder-trundle/prompts/06-shopping/_channel.md` | 1 | 1 |
| `/workspace/thunder-trundle/prompts/08-sitcom/_channel.md` | 1 | 1 |
| `/workspace/thunder-trundle/prompts/10-action/_channel.md` | 1 | 1 |
| `/workspace/thunder-trundle/prompts/12-90s/_channel.md` | 1 | 1 |
| `/workspace/thunder-trundle/prompts/14-music/_channel.md` | 1 | 1 |
| `/workspace/thunder-trundle/prompts/looks` | 1 | 1 |

</details>

<details><summary><code>/workspace/thunder-trundle/channels</code> → <code>TT_CHANNELS</code> (19 paths, 75 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/thunder-trundle/channels` | 4 | 4 |
| `/workspace/thunder-trundle/channels/02-news/channel.md` | 1 | 1 |
| `/workspace/thunder-trundle/channels/02-news/refs/sheets/SHEET_CH2_NEWS_CAST_v1.jpg` | 33 | 27 |
| `/workspace/thunder-trundle/channels/03-clean-job/refs/sheets/SHEET_CH3_CREW_v1.jpg` | 1 | 1 |
| `/workspace/thunder-trundle/channels/04-military-boutique/channel.md` | 2 | 2 |
| `/workspace/thunder-trundle/channels/05-night-patrol/refs/sheets/SHEET_CH5_CAST_VEHICLES_v1.jpg` | 6 | 5 |
| `/workspace/thunder-trundle/channels/06-shopping/channel.md` | 1 | 1 |
| `/workspace/thunder-trundle/channels/06-shopping/refs/sheets/SHEET_CH6_SHOPPING_CAST_v1.jpg` | 7 | 6 |
| `/workspace/thunder-trundle/channels/07-monster-hour/refs/sheets/SHEET_CH7_CAST_v2.jpg` | 2 | 2 |
| `/workspace/thunder-trundle/channels/08-sitcom/channel.md` | 1 | 1 |
| `/workspace/thunder-trundle/channels/08-sitcom/refs/sheets/SHEET_CH8_SITCOM_CAST_v1.jpg` | 2 | 2 |
| `/workspace/thunder-trundle/channels/09-iron-league/refs/sheets/SHEET_CH9_CAST_v1.jpg` | 2 | 2 |
| `/workspace/thunder-trundle/channels/10-action/channel.md` | 1 | 1 |
| `/workspace/thunder-trundle/channels/10-action/refs/sheets/SHEET_CH10_ACTION_CAST_v1.jpg` | 2 | 2 |
| `/workspace/thunder-trundle/channels/11-fist-theater/refs/sheets/SHEET_CH11_CAST_v1.jpg` | 3 | 3 |
| `/workspace/thunder-trundle/channels/12-90s/channel.md` | 1 | 1 |
| `/workspace/thunder-trundle/channels/12-90s/refs/sheets/SHEET_CH12_DALE_MARLA_STATIC_v1.jpg` | 2 | 2 |
| `/workspace/thunder-trundle/channels/14-music/channel.md` | 1 | 1 |
| `/workspace/thunder-trundle/channels/14-music/refs/sheets/SHEET_CH14_MUSIC_CAST_v2.jpg` | 3 | 3 |

</details>

<details><summary><code>/workspace/thunder-trundle/lineage</code> → <code>TT_LINEAGE</code> (1 paths, 4 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/thunder-trundle/lineage/LINEAGE.jsonl` | 4 | 2 |

</details>

<details><summary><code>/workspace/thunder-trundle/story</code> → <code>TT_STORY_DIR</code> (9 paths, 9 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/thunder-trundle/story/` | 1 | 1 |
| `/workspace/thunder-trundle/story/approvals` | 1 | 1 |
| `/workspace/thunder-trundle/story/director` | 1 | 1 |
| `/workspace/thunder-trundle/story/engine` | 1 | 1 |
| `/workspace/thunder-trundle/story/genealogy` | 1 | 1 |
| `/workspace/thunder-trundle/story/queues` | 1 | 1 |
| `/workspace/thunder-trundle/story/rules` | 1 | 1 |
| `/workspace/thunder-trundle/story/stream` | 1 | 1 |
| `/workspace/thunder-trundle/story/templates` | 1 | 1 |

</details>

<details><summary><code>/workspace/thunder-trundle</code> → <code>TT_THUNDER_ROOT</code> (7 paths, 19 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/thunder-trundle` | 12 | 12 |
| `/workspace/thunder-trundle/archive/story-bot-backups/20261028-1500` | 1 | 1 |
| `/workspace/thunder-trundle/archive/story-bot-backups/20261028-1500/continuity-ch04` | 1 | 1 |
| `/workspace/thunder-trundle/archive/story-bot-backups/20261028-1500/continuity-ch04/bible-v1.yaml` | 1 | 1 |
| `/workspace/thunder-trundle/handoffs/current-job/state-keeper-CURRENT-JOB.md` | 1 | 1 |
| `/workspace/thunder-trundle/harness` | 2 | 2 |
| `/workspace/thunder-trundle/specs/MUTATION-SPEC-v2.md` | 1 | 1 |

</details>

<details><summary><code>/workspace/streaming/story-engine</code> → <code>TT_STORY_ENGINE</code> (139 paths, 1152 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/streaming/story-engine` | 4 | 4 |
| `/workspace/streaming/story-engine/channels/04-military-boutique/shows/black-ice/ep01-20261027/segments` | 1 | 1 |
| `/workspace/streaming/story-engine/channels/04-military-boutique/shows/black-ice/ep01-20261027/segments/BI-01.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/channels/04-military-boutique/shows/black-ice/ep01-20261027/segments/BI-12.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/channels/04-military-boutique.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/channels/06-shopping.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/channels/08-sitcom.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/channels/10-action.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/channels/12-90s.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/channels/14-music.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/commercials/lightning-lamp.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/commercials/sky-diffuser.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/commercials/strata-clip-ration-tin.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/news/ch04-pigeon-signal-drift.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/news/ch04-sticker-shortage.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/shows/clearance-brief.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/shows/depot-after-hours.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/shows/forward-supply.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/slots/ch04-late-night.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/slots/ch04-midroll.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/slots/ch04-news-top.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/slots/ch04-prime-1900.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/slots/smoke-outline.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/snippets/ch04/characters.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/snippets/ch04/locations.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/configs/snippets/ch04/style.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/continuity/ch04-military-boutique` | 2 | 2 |
| `/workspace/streaming/story-engine/continuity/ch04-military-boutique/bible-v2.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/data/continuity/forward-supply.json` | 1 | 1 |
| `/workspace/streaming/story-engine/data/exports` | 1 | 1 |
| `/workspace/streaming/story-engine/data/live/starters/comment-starters-20261027.json` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C01_480p_grok-imagine-video-1.5-lite_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C02_480p_grok-imagine-video-1.5_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C03_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C04_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C05_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C06_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C07_480p_grok-imagine-video-1.5-lite_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C08_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C09_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C10_480p_grok-imagine-video-1.5-lite_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C11_480p_grok-imagine-video-1.5-lite_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C12_480p_grok-imagine-video-1.5-lite_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C13_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C14_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C15_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C16_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C17_480p_grok-imagine-video-1.5-lite_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C18_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C19_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C20_480p_grok-imagine-video-1.5-lite_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-pilot-20261027/renders-480p-draft-20261027_1424/FS-P01-C21_480p_grok-imagine-video-1.5-lite_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/clip-prompts.json` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2-remakes-20261027.json` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S1A_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S1B_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S1C_480p_grok-imagine-video-1.5_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S1D_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S1E_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S2A_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S2B_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S2C_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S2D_480p_grok-imagine-video-1.5_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S2E_480p_grok-imagine-video-1.5-lite_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S2F_480p_grok-imagine-video-1.5_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S2G_480p_grok-imagine-video-1.5-lite_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S3A_480p_grok-imagine-video-1.5_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S3B_480p_grok-imagine-video-1.5_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S3C_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S3D_480p_grok-imagine-video-1.5_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S3E_480p_grok-imagine-video-1.5_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S4A_480p_grok-imagine-video-1.5_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S4B_480p_grok-imagine-video-1.5_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S4C_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S4D_480p_grok-imagine-video-1.5-lite_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S5A_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S5B_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S5C_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S5D_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S5E_480p_grok-imagine-video-1.5_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S6A_480p_grok-imagine-video-1.5_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S6B_480p_grok-imagine-video-1.5_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S6C_480p_grok-imagine-video-1.5_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S6D_480p_grok-imagine-video-1.5_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S6E_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S7A_480p_grok-imagine-video-1.5_parody.mp4` | 2 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S7B_480p_grok-imagine-video-1.5_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S7C_480p_grok-imagine-video-1.5_parody.mp4` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/S7D_480p_grok-imagine-video-1.5_parody.mp4` | 32 | 3 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/ch04_forward-supply_pocket-taupe_480p-run2_parody.mp4` | 2 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/frames` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/frames/S1A_0.jpg` | 13 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/frames/S2A_1.jpg` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/frames/S2E_1.jpg` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/frames/S2G_0.jpg` | 10 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/frames/S3B_1.jpg` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/frames/S3C_1.jpg` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/frames/S3E_0.jpg` | 4 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/frames/S4C_0.jpg` | 4 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/frames/S5B_0.jpg` | 4 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/frames/S6B_1.jpg` | 1 | 1 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/frames/S7D_1.jpg` | 4 | 2 |
| `/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2/renders-480p-20261027_1547/log.jsonl` | 1 | 1 |
| `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/bill-B2-full.png` | 74 | 10 |
| `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/bill-B2-side.png` | 74 | 10 |
| `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/bill-B2.png` | 91 | 12 |
| `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/mira-C-full.png` | 71 | 10 |
| `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/mira-C-side.png` | 71 | 10 |
| `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/mira-C.png` | 103 | 12 |
| `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/osmund-B-full.png` | 88 | 10 |
| `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/osmund-B-side.png` | 88 | 10 |
| `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/osmund-B.png` | 120 | 12 |
| `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/tim-E5-sideback.png` | 50 | 9 |
| `/workspace/streaming/story-engine/data/refs/ch04-cast-stills-20261027/tim-E5.png` | 64 | 11 |
| `/workspace/streaming/story-engine/data/shows/dress-inspection-20261027/anchors/ad30_helmet_first.jpg` | 2 | 1 |
| `/workspace/streaming/story-engine/data/shows/dress-inspection-20261027/anchors/ad30_helmet_last.jpg` | 2 | 1 |
| `/workspace/streaming/story-engine/data/shows/dress-inspection-20261027/anchors/ad31_pack_first.jpg` | 2 | 1 |
| `/workspace/streaming/story-engine/data/shows/dress-inspection-20261027/anchors/ad31_pack_last.jpg` | 2 | 1 |
| `/workspace/streaming/story-engine/data/shows/dress-inspection-20261027/anchors/ad32_rover_first.jpg` | 2 | 1 |
| `/workspace/streaming/story-engine/data/shows/dress-inspection-20261027/anchors/ad32_rover_last.jpg` | 2 | 1 |
| `/workspace/streaming/story-engine/data/shows/dress-inspection-20261027/anchors/ad33_gauntlet_first.jpg` | 2 | 1 |
| `/workspace/streaming/story-engine/data/shows/dress-inspection-20261027/anchors/ad33_gauntlet_last.jpg` | 2 | 1 |
| `/workspace/streaming/story-engine/data/shows/dress-inspection-20261027/anchors/ad34_drone_first.jpg` | 2 | 1 |
| `/workspace/streaming/story-engine/data/shows/dress-inspection-20261027/anchors/ad34_drone_last.jpg` | 2 | 1 |
| `/workspace/streaming/story-engine/data/shows/dress-inspection-20261027/anchors/ad35_binoculars_first.jpg` | 2 | 1 |
| `/workspace/streaming/story-engine/data/shows/dress-inspection-20261027/anchors/ad35_binoculars_last.jpg` | 2 | 1 |
| `/workspace/streaming/story-engine/data/shows/dress-inspection-20261027/anchors/ad36_cloak_first.jpg` | 2 | 1 |
| `/workspace/streaming/story-engine/data/shows/dress-inspection-20261027/anchors/ad36_cloak_last.jpg` | 2 | 1 |
| `/workspace/streaming/story-engine/data/shows/the-efficiency-review-20261027/prompts.json` | 2 | 2 |
| `/workspace/streaming/story-engine/data/stills-20261027/product-stills-prompts-20261027.json` | 1 | 1 |
| `/workspace/streaming/story-engine/director/pitches/espionage-show-20261027.md` | 2 | 2 |
| `/workspace/streaming/story-engine/engine` | 3 | 3 |
| `/workspace/streaming/story-engine/engine/assemble_prompt.py` | 3 | 3 |
| `/workspace/streaming/story-engine/live` | 5 | 5 |
| `/workspace/streaming/story-engine/live/checker.py` | 1 | 1 |
| `/workspace/streaming/story-engine/rules/queue-policy.yaml` | 1 | 1 |
| `/workspace/streaming/story-engine/server` | 1 | 1 |

</details>

<details><summary><code>/workspace/streaming/queues</code> → <code>TT_QUEUES</code> (125 paths, 304 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/streaming/queues` | 1 | 1 |
| `/workspace/streaming/queues/COMMENT-PROMPTS.jsonl` | 2 | 2 |
| `/workspace/streaming/queues/PREEMPTION-ADDENDUM.md` | 2 | 1 |
| `/workspace/streaming/queues/PROMOTION-PROCESS.md` | 2 | 2 |
| `/workspace/streaming/queues/QUEUE-PLAN-20261027.json` | 1 | 1 |
| `/workspace/streaming/queues/frames/10/04_0261026-232851-4-4-action-concrete-garage-standoff_first.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/10/04_0261026-232851-4-4-action-concrete-garage-standoff_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/10/05_20261026-232851-4-4-action-night-alley-chase-blur_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/10/05_20261026-232851-4-4-action-night-alley-chase-blur_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/10/06_20261026-232851-4-4-action-rooftop-city-bokeh_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/10/06_20261026-232851-4-4-action-rooftop-city-bokeh_last.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/10/07_20261026-232851-4-4-action-wet-bridge-headlights_first.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/10/07_20261026-232851-4-4-action-wet-bridge-headlights_last.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/10/08_0261027-080512-4-4-action-stairwell-emergency-haze_first.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/10/08_0261027-080512-4-4-action-stairwell-emergency-haze_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/10/09_20261027-080512-4-4-action-subway-platform-blur_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/10/09_20261027-080512-4-4-action-subway-platform-blur_last.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/12/01_20261026-232851-4-5-90s-boombox-skate-curb_first.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/12/01_20261026-232851-4-5-90s-boombox-skate-curb_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/12/02_20261026-232851-4-5-90s-empty-arcade-neon_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/12/02_20261026-232851-4-5-90s-empty-arcade-neon_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/12/03_20261026-232851-4-5-90s-food-court-daylight_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/12/03_20261026-232851-4-5-90s-food-court-daylight_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/12/04_20261026-232851-4-5-90s-vhs-living-room-glow_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/12/04_20261026-232851-4-5-90s-vhs-living-room-glow_last.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/12/05_20261027-080735-4-5-90s-roadside-diner-counter_first.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/12/05_20261027-080735-4-5-90s-roadside-diner-counter_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/12/06_emple-water-tower-declares-independence-fix2-clean_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/12/06_emple-water-tower-declares-independence-fix2-clean_last.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/12/07_a-trial-bellquist-a-once-daily-pill-fo-s2144003566_first.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/12/07_a-trial-bellquist-a-once-daily-pill-fo-s2144003566_last.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/12/08_dhmo-live_first.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/12/08_dhmo-live_last.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/12/09_20261026-183646-housead-glosneaks-90s-lufs14_first.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/12/09_20261026-183646-housead-glosneaks-90s-lufs14_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/12/10_261026-183033-housead-fizzbolt-90s-lufs14-audiofix_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/12/10_261026-183033-housead-fizzbolt-90s-lufs14-audiofix_last.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/12/11_261026-183211-housead-dynapage-90s-lufs14-audiofix_first.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/12/11_261026-183211-housead-dynapage-90s-lufs14-audiofix_last.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/14/01_20261026-232851-4-6-music-club-stage-haze_first.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/14/01_20261026-232851-4-6-music-club-stage-haze_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/14/02_20261026-232851-4-6-music-dj-deck-vinyl-spin_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/14/02_20261026-232851-4-6-music-dj-deck-vinyl-spin_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/14/03_20261026-232851-4-6-music-loft-rehearsal-amp_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/14/03_20261026-232851-4-6-music-loft-rehearsal-amp_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/14/04_20261026-232851-4-6-music-vocal-booth-meters_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/14/04_20261026-232851-4-6-music-vocal-booth-meters_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/14/05_20261027-074825-4-6-music-upright-piano-loft_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/14/05_20261027-074825-4-6-music-upright-piano-loft_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/14/06_20261027-074825-4-6-music-vinyl-crate-wall_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/14/06_20261027-074825-4-6-music-vinyl-crate-wall_last.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/4/01_ch04-forward-supply-pocket-taupe-480p-run2_first.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/4/01_ch04-forward-supply-pocket-taupe-480p-run2_last.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/4/05_mock-05-ch04-commenter_first.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/4/05_mock-05-ch04-commenter_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/4/06_mock-08-manual-ch04-commenter_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/4/06_mock-08-manual-ch04-commenter_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/4/07_x-m1002-ch04-commenter_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/4/07_x-m1002-ch04-commenter_last.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/4/08_ed-showroom-cruiser-salesadb-cover-tagged-audiofix_first.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/08_ed-showroom-cruiser-salesadb-cover-tagged-audiofix_last.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/08_ed-showroom-cruiser-salesadb-cover-tagged-audiofix_master_first.jpg` | 3 | 1 |
| `/workspace/streaming/queues/frames/4/08_ed-showroom-cruiser-salesadb-cover-tagged-audiofix_master_last.jpg` | 3 | 1 |
| `/workspace/streaming/queues/frames/4/09_xo-gauntlet-vitrine-salesadb-cover-tagged-audiofix_first.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/09_xo-gauntlet-vitrine-salesadb-cover-tagged-audiofix_last.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/09_xo-gauntlet-vitrine-salesadb-cover-tagged-audiofix_master_first.jpg` | 3 | 1 |
| `/workspace/streaming/queues/frames/4/09_xo-gauntlet-vitrine-salesadb-cover-tagged-audiofix_master_last.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/10_modular-field-pack-salesadb-cover-tagged-audiofix_first.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/10_modular-field-pack-salesadb-cover-tagged-audiofix_last.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/10_modular-field-pack-salesadb-cover-tagged-audiofix_master_first.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/10_modular-field-pack-salesadb-cover-tagged-audiofix_master_last.jpg` | 3 | 1 |
| `/workspace/streaming/queues/frames/4/11_scout-drone-jewelry-salesadb-cover-tagged-audiofix_first.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/11_scout-drone-jewelry-salesadb-cover-tagged-audiofix_last.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/11_scout-drone-jewelry-salesadb-cover-tagged-audiofix_master_first.jpg` | 3 | 1 |
| `/workspace/streaming/queues/frames/4/11_scout-drone-jewelry-salesadb-cover-tagged-audiofix_master_last.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/12_cal-helmet-pedestal-salesadb-cover-tagged-audiofix_first.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/12_cal-helmet-pedestal-salesadb-cover-tagged-audiofix_last.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/12_cal-helmet-pedestal-salesadb-cover-tagged-audiofix_master_first.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/12_cal-helmet-pedestal-salesadb-cover-tagged-audiofix_master_last.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/13_d-binoculars-velvet-salesadb-cover-tagged-audiofix_first.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/13_d-binoculars-velvet-salesadb-cover-tagged-audiofix_last.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/13_d-binoculars-velvet-salesadb-cover-tagged-audiofix_master_first.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/13_d-binoculars-velvet-salesadb-cover-tagged-audiofix_master_last.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/14_raphite-cloak-torso-salesadb-cover-tagged-audiofix_first.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/14_raphite-cloak-torso-salesadb-cover-tagged-audiofix_last.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/14_raphite-cloak-torso-salesadb-cover-tagged-audiofix_master_first.jpg` | 1 | 1 |
| `/workspace/streaming/queues/frames/4/14_raphite-cloak-torso-salesadb-cover-tagged-audiofix_master_last.jpg` | 3 | 1 |
| `/workspace/streaming/queues/frames/6/01_20261026-232851-4-2-shopping-retro-checkout-bokeh_first.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/6/01_20261026-232851-4-2-shopping-retro-checkout-bokeh_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/6/02_0261027-074825-4-2-shopping-glass-escalator-atrium_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/6/02_0261027-074825-4-2-shopping-glass-escalator-atrium_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/6/03_20261027-080512-4-2-shopping-glass-jewelry-case_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/6/03_20261027-080512-4-2-shopping-glass-jewelry-case_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/6/04_026-232851-4-2-shopping-marble-bags-sweep-audiofix_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/6/04_026-232851-4-2-shopping-marble-bags-sweep-audiofix_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/6/05_6-232851-4-2-shopping-neon-boutique-aisle-audiofix_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/6/05_6-232851-4-2-shopping-neon-boutique-aisle-audiofix_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/6/06_232851-4-2-shopping-rain-storefront-glass-audiofix_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/6/06_232851-4-2-shopping-rain-storefront-glass-audiofix_last.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/8/01_20261026-232851-4-3-sitcom-apartment-doorway_first.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/8/01_20261026-232851-4-3-sitcom-apartment-doorway_last.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/8/02_20261026-232851-4-3-sitcom-corner-booth-diner_first.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/8/02_20261026-232851-4-3-sitcom-corner-booth-diner_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/8/03_20261026-232851-4-3-sitcom-sitcom-kitchen-island_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/8/03_20261026-232851-4-3-sitcom-sitcom-kitchen-island_last.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/8/04_20261026-232851-4-3-sitcom-warm-couch-cold-open_first.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/8/04_20261026-232851-4-3-sitcom-warm-couch-cold-open_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/8/05_20261027-080512-4-3-sitcom-patio-string-lights_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/8/05_20261027-080512-4-3-sitcom-patio-string-lights_last.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/8/06_20261027-080735-4-3-sitcom-laundry-room-folding_first.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/8/06_20261027-080735-4-3-sitcom-laundry-room-folding_last.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/all/01_7-085408-guide-transition-neutral-landing-audiofix_first.jpg` | 4 | 1 |
| `/workspace/streaming/queues/frames/all/01_7-085408-guide-transition-neutral-landing-audiofix_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/all/02_14-guide-transition-4-1-military-boutique-audiofix_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/all/02_14-guide-transition-4-1-military-boutique-audiofix_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/all/03_1027-085419-guide-transition-4-2-shopping-audiofix_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/all/03_1027-085419-guide-transition-4-2-shopping-audiofix_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/all/04_261027-085425-guide-transition-4-3-sitcom-audiofix_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/all/04_261027-085425-guide-transition-4-3-sitcom-audiofix_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/all/05_261027-085430-guide-transition-4-4-action-audiofix_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/all/05_261027-085430-guide-transition-4-4-action-audiofix_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/all/06_20261027-085435-guide-transition-4-5-90s-audiofix_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/all/06_20261027-085435-guide-transition-4-5-90s-audiofix_last.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/all/07_0261027-085441-guide-transition-4-6-music-audiofix_first.jpg` | 2 | 1 |
| `/workspace/streaming/queues/frames/all/07_0261027-085441-guide-transition-4-6-music-audiofix_last.jpg` | 4 | 1 |

</details>

<details><summary><code>/workspace/streaming/commenter-pipeline</code> → <code>TT_COMMENTER_PIPELINE</code> (4 paths, 13 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/streaming/commenter-pipeline/config.json` | 7 | 2 |
| `/workspace/streaming/commenter-pipeline/outbox/mock-05_ch04_commenter_parody.mp4` | 2 | 1 |
| `/workspace/streaming/commenter-pipeline/outbox/mock-08-manual_ch04_commenter_parody.mp4` | 2 | 1 |
| `/workspace/streaming/commenter-pipeline/outbox/x-m1002_ch04_commenter_parody.mp4` | 2 | 1 |

</details>

<details><summary><code>/workspace/streaming</code> → <code>TT_STREAMING_ROOT</code> (5 paths, 12 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/streaming` | 2 | 2 |
| `/workspace/streaming/NAME-COVER-20261027.json` | 5 | 3 |
| `/workspace/streaming/PULLED-20261027.jsonl` | 3 | 2 |
| `/workspace/streaming/UNUSABLE-20261027.jsonl` | 1 | 1 |
| `/workspace/streaming/shared_lib` | 1 | 1 |

</details>

<details><summary><code>/workspace/fakenews/channel-ready</code> → <code>TT_CHANNEL_READY</code> (175 paths, 260 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/fakenews/channel-ready/20261026_153228_breaking_news_temple-water-tower-declares-independence_fix2_clean_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/20261026_153414_pharma_trial_bellquist-a-once-daily-pill-fo_s2144003566_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/guide-transitions/20261026_223621_guide_transition_4_1_Military-Boutique_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/guide-transitions/20261027_085408_guide_transition_neutral_landing_audiofix_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/guide-transitions/20261027_085414_guide_transition_4_1_Military-Boutique_audiofix_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/guide-transitions/20261027_085419_guide_transition_4_2_shopping_audiofix_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/guide-transitions/20261027_085425_guide_transition_4_3_sitcom_audiofix_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/guide-transitions/20261027_085430_guide_transition_4_4_action_audiofix_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/guide-transitions/20261027_085435_guide_transition_4_5_90s_audiofix_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/guide-transitions/20261027_085441_guide_transition_4_6_music_audiofix_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/house-ads/20261026_183033_housead_fizzbolt_90s_lufs14_audiofix_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/house-ads/20261026_183211_housead_dynapage_90s_lufs14_audiofix_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/house-ads/20261026_183646_housead_glosneaks_90s_lufs14_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique` | 2 | 2 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/LINEAGE.jsonl` | 3 | 3 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027` | 3 | 3 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/cut/black-ice-20261027_ch4_ep1_showonly_v2_720p_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/lastframes/BI-01_g99_last_clean_v3_parody.jpg` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/lastframes/BI-02_g100_last_clean_parody.jpg` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/lastframes/BI-03_g101_last_clean_v2_parody.jpg` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/lastframes/BI-04_g102_last_clean_parody.jpg` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/lastframes/BI-05_g103_last_clean_parody.jpg` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/lastframes/BI-06_g104_last_clean_parody.jpg` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/lastframes/BI-07_g105_last_clean_parody.jpg` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/lastframes/BI-08_g106_last_clean_parody.jpg` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/lastframes/BI-09_g107_last_clean_parody.jpg` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/lastframes/BI-10_g108_last_clean_parody.jpg` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/lastframes/BI-11_g109_last_clean_parody.jpg` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/lastframes/BI-12_g110_last_clean_parody.jpg` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/lastframes/BI-13_g111_last_clean_parody.jpg` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/lastframes/BI-14_g112_last_clean_parody.jpg` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/lastframes/BI-15_g113_last_clean_parody.jpg` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/lastframes/BI-16_g114_last_clean_parody.jpg` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/lastframes/BI-17_g115_last_clean_parody.jpg` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/lastframes/BI-18_g116_last_clean_parody.jpg` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/leveled/BI-01_g99_cap_tag_lev_v3_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/leveled/BI-02_g100_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/leveled/BI-03_g101_cap_tag_lev_v2_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/leveled/BI-04_g102_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/leveled/BI-05_g103_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/leveled/BI-06_g104_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/leveled/BI-07_g105_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/leveled/BI-08_g106_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/leveled/BI-09_g107_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/leveled/BI-10_g108_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/leveled/BI-11_g109_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/leveled/BI-12_g110_cap_tag_lev_v2_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/leveled/BI-13_g111_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/leveled/BI-14_g112_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/leveled/BI-15_g113_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/leveled/BI-16_g114_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/leveled/BI-17_g115_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/leveled/BI-18_g116_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/masters/BI-01_try1_480p_clean_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/masters/BI-02_try1_480p_clean_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/masters/BI-03_try1_480p_clean_delogo_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/masters/BI-04_try1_480p_clean_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/masters/BI-05_try1_480p_clean_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/masters/BI-06_try1_480p_clean_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/masters/BI-07_try1_480p_clean_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/masters/BI-08_try1_480p_clean_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/masters/BI-09_try1_480p_clean_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/masters/BI-10_try1_480p_clean_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/masters/BI-11_try1_480p_clean_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/masters/BI-12_try1_480p_clean_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/masters/BI-13_try1_480p_clean_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/masters/BI-14_try1_480p_clean_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/masters/BI-15_try1_480p_clean_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/masters/BI-16_try1_480p_clean_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/masters/BI-17_try1_480p_clean_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/masters/BI-18_try1_480p_clean_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/qc/STATUS-HOLD-20261028-0831.md` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/shots_ep1.py` | 2 | 2 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC1_LANDING_AROLL/BI-S01_end_try2_parody.png` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC1_LANDING_AROLL/BI-S01_start_try1_parody.png` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC1_LANDING_AROLL/BI-S03_start_try1_parody.png` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC1_LANDING_AROLL/BI-S05_start_try1_parody.png` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC1_LANDING_AROLL/BI-S06_start_try1_parody.png` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC1_LANDING_BROLL/BI-S02_start_try1_parody.png` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC1_LANDING_BROLL/BI-S07_start_try1_parody.png` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC2_RADIOROOM_AROLL/BI-S04_start_try2_parody.png` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC2_RADIOROOM_AROLL/BI-S15_start_try2_parody.png` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC3_ICE_AROLL/BI-S08_end_try1_parody.png` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC3_ICE_AROLL/BI-S08_start_try1_parody.png` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC3_ICE_AROLL/BI-S09_start_try1_parody.png` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC4_PERIMETER_BROLL/BI-S10_end_try1_parody.png` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC4_PERIMETER_BROLL/BI-S10_start_try2_parody.png` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC5_HALL_AROLL/BI-S11_end_try1_parody.png` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC5_HALL_AROLL/BI-S11_start_try1_parody.png` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC5_HALL_AROLL/BI-S12_start_try2_parody.png` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC5_HALL_AROLL/BI-S13_start_try1_parody.png` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC5_HALL_AROLL/BI-S14_start_try1_parody.png` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC5_HALL_AROLL/BI-S16_start_try1_parody.png` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC5_HALL_AROLL/BI-S17_end_try1_parody.png` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC5_HALL_AROLL/BI-S17_start_try1_parody.png` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC6_ICE_ESCAPE_AROLL/BI-S18_end_try1_parody.png` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/black-ice-20261027/stills/SC6_ICE_ESCAPE_AROLL/BI-S18_start_try2_parody.png` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/dress-inspection-20261027/leveled/DI-01_g71_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/dress-inspection-20261027/leveled/DI-02-1_g72_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/dress-inspection-20261027/leveled/DI-02-2_try2g2_g82_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/dress-inspection-20261027/leveled/DI-02-3_g74_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/dress-inspection-20261027/leveled/DI-02-4_g75_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/dress-inspection-20261027/leveled/DI-02-5_try2g2_g83_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/dress-inspection-20261027/leveled/DI-02-7_g78_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/dress-inspection-20261027/leveled/DI-03_try2g2_g84_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/dress-inspection-20261027/leveled/DI-04_g80_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/dress-inspection-20261027/leveled/DI-05_g81_cap_tag_lev_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/lineage-tagfade-20261027` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/lineage-tagfade-20261027/20261026_231528_4_1_Military-Boutique_armored-showroom-cruiser_parody_salesadBA_tagfade_parody.mp4` | 3 | 2 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/lineage-tagfade-20261027/20261026_231528_4_1_Military-Boutique_exo-gauntlet-vitrine_parody_salesadBA_tagfade_parody.mp4` | 3 | 2 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/lineage-tagfade-20261027/20261026_231528_4_1_Military-Boutique_modular-field-pack_parody_salesadBA_tagfade_parody.mp4` | 3 | 2 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/lineage-tagfade-20261027/20261026_231528_4_1_Military-Boutique_scout-drone-jewelry_parody_salesadBA_tagfade_parody.mp4` | 3 | 2 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/lineage-tagfade-20261027/20261026_231528_4_1_Military-Boutique_tactical-helmet-pedestal_parody_salesadBA_tagfade_parody.mp4` | 3 | 2 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/lineage-tagfade-20261027/20261027_080512_4_1_Military-Boutique_field-binoculars-velvet_parody_salesadBA_tagfade_parody.mp4` | 3 | 2 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/lineage-tagfade-20261027/20261027_080512_4_1_Military-Boutique_graphite-cloak-torso_parody_salesadBA_tagfade_parody.mp4` | 3 | 2 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/lineage-tagged-20261027/20261026_231528_4_1_Military-Boutique_tactical-helmet-pedestal_parody_salesadBA_tagged_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/raw` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/raw/mb_binoculars.mp4` | 2 | 2 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/raw/mb_cloak.mp4` | 2 | 2 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/raw/mb_drone.mp4` | 2 | 2 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/raw/mb_gauntlet.mp4` | 2 | 2 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/raw/mb_helmet.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/raw/mb_pack.mp4` | 2 | 2 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/raw/mb_rover.mp4` | 2 | 2 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/sales-overlay-20261027` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/sales-overlay-20261027/MANIFEST.json` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/sales-overlay-B-20261027` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/salesad-A-cover-20261027/20261026_231528_4_1_Military-Boutique_armored-showroom-cruiser_parody_salesadB_cover_tagged_audiofix_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/salesad-A-cover-20261027/20261026_231528_4_1_Military-Boutique_exo-gauntlet-vitrine_parody_salesadB_cover_tagged_audiofix_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/salesad-A-cover-20261027/20261026_231528_4_1_Military-Boutique_modular-field-pack_parody_salesadB_cover_tagged_audiofix_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/salesad-A-cover-20261027/20261026_231528_4_1_Military-Boutique_scout-drone-jewelry_parody_salesadB_cover_tagged_audiofix_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/salesad-A-cover-20261027/20261026_231528_4_1_Military-Boutique_tactical-helmet-pedestal_parody_salesadB_cover_tagged_audiofix_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/salesad-A-cover-20261027/20261027_080512_4_1_Military-Boutique_field-binoculars-velvet_parody_salesadB_cover_tagged_audiofix_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/salesad-A-cover-20261027/20261027_080512_4_1_Military-Boutique_graphite-cloak-torso_parody_salesadB_cover_tagged_audiofix_parody.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_2_Shopping/20261026_232851_4_2_Shopping_marble-bags-sweep_audiofix_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_2_Shopping/20261026_232851_4_2_Shopping_neon-boutique-aisle_audiofix_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_2_Shopping/20261026_232851_4_2_Shopping_rain-storefront-glass_audiofix_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_2_Shopping/20261026_232851_4_2_Shopping_retro-checkout-bokeh_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_2_Shopping/20261027_074825_4_2_Shopping_glass-escalator-atrium_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_2_Shopping/20261027_080512_4_2_Shopping_glass-jewelry-case_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_3_Sitcom/20261026_232851_4_3_Sitcom_apartment-doorway_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_3_Sitcom/20261026_232851_4_3_Sitcom_corner-booth-diner_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_3_Sitcom/20261026_232851_4_3_Sitcom_sitcom-kitchen-island_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_3_Sitcom/20261026_232851_4_3_Sitcom_warm-couch-cold-open_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_3_Sitcom/20261027_080512_4_3_Sitcom_patio-string-lights_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_3_Sitcom/20261027_080735_4_3_Sitcom_laundry-room-folding_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_4_Action/20261026_232851_4_4_Action_concrete-garage-standoff_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_4_Action/20261026_232851_4_4_Action_night-alley-chase-blur_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_4_Action/20261026_232851_4_4_Action_rooftop-city-bokeh_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_4_Action/20261026_232851_4_4_Action_wet-bridge-headlights_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_4_Action/20261027_080512_4_4_Action_stairwell-emergency-haze_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_4_Action/20261027_080512_4_4_Action_subway-platform-blur_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_5_90s/20261026_232851_4_5_90s_boombox-skate-curb_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_5_90s/20261026_232851_4_5_90s_empty-arcade-neon_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_5_90s/20261026_232851_4_5_90s_food-court-daylight_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_5_90s/20261026_232851_4_5_90s_vhs-living-room-glow_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_5_90s/20261027_080735_4_5_90s_roadside-diner-counter_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_6_Music/20261026_232851_4_6_Music_club-stage-haze_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_6_Music/20261026_232851_4_6_Music_dj-deck-vinyl-spin_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_6_Music/20261026_232851_4_6_Music_loft-rehearsal-amp_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_6_Music/20261026_232851_4_6_Music_vocal-booth-meters_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_6_Music/20261027_074825_4_6_Music_upright-piano-loft_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_6_Music/20261027_074825_4_6_Music_vinyl-crate-wall_parody.mp4` | 2 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_Military-Boutique` | 6 | 6 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_Military-Boutique/raw/mb_binoculars.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_Military-Boutique/raw/mb_cloak.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_Military-Boutique/raw/mb_drone.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_Military-Boutique/raw/mb_gauntlet.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_Military-Boutique/raw/mb_helmet.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_Military-Boutique/raw/mb_pack.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/4_Military-Boutique/raw/mb_rover.mp4` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/SERIES-PLAN.md` | 1 | 1 |
| `/workspace/fakenews/channel-ready/thunder-trundle/house-ads` | 2 | 2 |
| `/workspace/fakenews/channel-ready/thunder-trundle/house-ads/20261026_232450_housead_lightninglamp_thunder-trundle-home_parody.mp4` | 3 | 3 |
| `/workspace/fakenews/channel-ready/thunder-trundle/house-ads/20261026_232450_housead_skydiffuser_thunder-trundle-home_parody.mp4` | 3 | 3 |

</details>

<details><summary><code>/workspace/fakenews/spend.jsonl</code> → <code>TT_SPEND_LEDGER</code> (1 paths, 3 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/fakenews/spend.jsonl` | 3 | 3 |

</details>

<details><summary><code>/workspace/fakenews</code> → <code>TT_FAKENEWS_ROOT</code> (1 paths, 1 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/fakenews/out/qa` | 1 | 1 |

</details>

<details><summary><code>/workspace/shared/spend</code> → <code>TT_SPEND_DIR</code> (1 paths, 5 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/shared/spend/xai-month.md` | 5 | 4 |

</details>

<details><summary><code>/workspace/shared/streaming</code> → <code>TT_SHARED_STREAMING</code> (17 paths, 38 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/shared/streaming/CHARACTER-BIBLE-20261026.md` | 1 | 1 |
| `/workspace/shared/streaming/CLIP-PROMOTION-PROCESS-20261027.md` | 4 | 3 |
| `/workspace/shared/streaming/IDEAS.md` | 1 | 1 |
| `/workspace/shared/streaming/MEDIA-LIBRARY.md` | 1 | 1 |
| `/workspace/shared/streaming/MILITARY-BOUTIQUE-EXPERIMENTS.md` | 1 | 1 |
| `/workspace/shared/streaming/PULLED-20261027.json` | 1 | 1 |
| `/workspace/shared/streaming/QUEUE-LOAD-` | 1 | 1 |
| `/workspace/shared/streaming/STATUS.md` | 1 | 1 |
| `/workspace/shared/streaming/STORY-CONFIG-PLAN.md` | 2 | 2 |
| `/workspace/shared/streaming/ch04-sales-overlay-sheet-DRAFT.md` | 10 | 1 |
| `/workspace/shared/streaming/grok-imagine-90s-news-guide.md` | 2 | 2 |
| `/workspace/shared/streaming/house-ad-product-specs-20261027.md` | 7 | 1 |
| `/workspace/shared/streaming/tag-slip-watchlist.jsonl` | 2 | 2 |
| `/workspace/shared/streaming/templates/PROMPT-TEMPLATES.md` | 1 | 1 |
| `/workspace/shared/streaming/x-intake/HANDOFF.md` | 1 | 1 |
| `/workspace/shared/streaming/x-intake/export_cnb.py` | 1 | 1 |
| `/workspace/shared/streaming/x-intake/queue/storybot-inbox` | 1 | 1 |

</details>

<details><summary><code>/workspace/shared/media-library</code> → <code>TT_MEDIA_LIBRARY</code> (10 paths, 18 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/shared/media-library/ch04-military-boutique/cnb-house-ads/20261026_232450_housead_lightninglamp_thunder-trundle-home.mp4` | 1 | 1 |
| `/workspace/shared/media-library/ch04-military-boutique/cnb-house-ads/20261026_232450_housead_skydiffuser_thunder-trundle-home.mp4` | 1 | 1 |
| `/workspace/shared/media-library/ch04-military-boutique/cnb-series` | 2 | 2 |
| `/workspace/shared/media-library/ch04-military-boutique/cnb-series/20261026_231528_4_1_Military-Boutique_armored-showroom-cruiser.mp4` | 2 | 2 |
| `/workspace/shared/media-library/ch04-military-boutique/cnb-series/20261026_231528_4_1_Military-Boutique_exo-gauntlet-vitrine.mp4` | 2 | 2 |
| `/workspace/shared/media-library/ch04-military-boutique/cnb-series/20261026_231528_4_1_Military-Boutique_modular-field-pack.mp4` | 2 | 2 |
| `/workspace/shared/media-library/ch04-military-boutique/cnb-series/20261026_231528_4_1_Military-Boutique_scout-drone-jewelry.mp4` | 2 | 2 |
| `/workspace/shared/media-library/ch04-military-boutique/cnb-series/20261026_231528_4_1_Military-Boutique_tactical-helmet-pedestal.mp4` | 2 | 2 |
| `/workspace/shared/media-library/ch04-military-boutique/cnb-series/20261027_080512_4_1_Military-Boutique_field-binoculars-velvet.mp4` | 2 | 2 |
| `/workspace/shared/media-library/ch04-military-boutique/cnb-series/20261027_080512_4_1_Military-Boutique_graphite-cloak-torso.mp4` | 2 | 2 |

</details>

<details><summary><code>/workspace/shared</code> → <code>TT_SHARED_ROOT</code> (4 paths, 10 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/shared/INVENTORY/accounts-subs-apis.md` | 4 | 4 |
| `/workspace/shared/build-queue` | 2 | 2 |
| `/workspace/shared/vision` | 2 | 2 |
| `/workspace/shared/weekly-review/2026-10-30.md` | 2 | 2 |

</details>

<details><summary><code>/workspace/backups</code> → <code>TT_BACKUPS</code> (3 paths, 10 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/backups/eggbot-20261029-1300/` | 2 | 2 |
| `/workspace/backups/harness-archive-20261029/harness-codex` | 4 | 2 |
| `/workspace/backups/profiles-O9-20261029` | 4 | 2 |

</details>

<details><summary><code>/workspace/director</code> → <code>TT_DIRECTOR_DIR</code> (3 paths, 7 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/director/brief-dress-inspection-20261027.md` | 3 | 3 |
| `/workspace/director/brief-the-efficiency-review-20261027.md` | 3 | 3 |
| `/workspace/director/dress-inspection-recut-20261027/work/cutaway_minivan.mp4` | 1 | 1 |

</details>

<details><summary><code>/workspace/diag</code> → <code>TT_DIAG</code> (1 paths, 2 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/diag/dhmo_live_parody.mp4` | 2 | 1 |

</details>

<details><summary><code>/workspace/de-parity</code> → <code>TT_DE_PARITY</code> (1 paths, 1 hits)</summary>

| Path | Hits | Files |
|---|---:|---:|
| `/workspace/de-parity/pickup.py` | 1 | 1 |

</details>
