# RULE CONFLICTS FIXED: v4 → v4.1 (2026-10-30 7:40 PM CT)
v4 files are untouched (add-only). The new files are tools/build_prompt_v41.py, apply_check_v41.py, regen_v41.py, new_shows_v41.py, config/static_v41.json and tests/test_v41.py. The outputs are in prompts_v41/, and the full per-prompt before/after text is in out/DIFF-v41.md.

| # | Conflict (evidence) | His rule | Before (v4) | After (v4.1) |
|---|---|---|---|---|
| 1 | layers_v4.py:27-28 SAFETY_POOL | T14, T20, T21 | "No gore, no blood on skin; stains on clothing only." / "Stage-combat hits land on coats and props; no wounds or blood on skin" | "No gore; bloodstains on clothing are fine, no blood draining out." Ch4 fights add: "John Wick level: hard hits and some blood, but no gore." The gate FAILs if the old wording returns |
| 2 | Same pool: "No on-screen text, no logos", "Theatrical props only" | T15, T16, T19 | In the bracket | Removed. Real weapons and in-scene text are allowed |
| 3 | Pool of 2 random brackets | T1 static | Random choice | One fixed bracket in his words |
| 4 | build_prompt_v4.py:59, a random look from look_pool | T1 static tangible | Look varied per clip | One fixed look line per channel (static_v41.json) |
| 5 | build_prompt_v4.py:96 `R.shuffle(movable)` | T1 static; T6 brackets | Sentence order shuffled | Fixed slots: [Look] [Setting] [Cast] → Continue → Shot → Eyelines → timed beats → ending → [Rules]. Tested: 5 builds give the same text |
| 6 | Dialogue `says, "[cue] line"` | T6, T7, T8 | Only the cue was bracketed; pronoun speakers passed | `NAME speaks [cue: "line"]`. The gate FAILs on an unnamed or unbracketed speaker (it caught P06-3 "she" and P12-2 "he") |
| 7 | apply_check_v4.py:57-59 V14 transform still | T2 (Steve = thread-following) | FAIL without state stills | Removed. THREAD-FOLLOWING.md added; CHARACTER-CHANGE.md kept unedited |
| 8 | A1 ≤330 words, A13 ≤4 beats as FAIL | T13, T23 | Blocked dense prompts | WARN only |
| 9 | V16 cut words, V5 one move, V4 tracking-needs-start as FAIL | T11, T15 | Blocked "quick cuts" and the POV change | WARN only |
| 10 | V13 commenter fail-closed | T22 relaxed filter | FAIL | Removed; the bracket carries the moves-and-attitude-no-likeness rule |
| 11 | No reference check (Polar Thermos and most ads passed with refs=None) | T3 | Passed | R-REF FAILs. 20 pilots/lipsync were fixed free with the approved channel cast sheets. 16 ads are BLOCKED until refs exist |
| 12 | regen_pending_v4.py:97 NP01 set plate used as START frame | T4 | Plate as image_path | Plate moved to the references; <IMAGE_n> renumbered; a new gate check X-image-numbering confirms it |
| 13 | AD-Dynapage remake in the commercial set | T29 | Was in the pending set | R-REMAKE FAIL: do not render |
| 14 | build_prompt_v4.py:25,100 "strike travels toward the lens" | T25 (eyes off the camera); our exit rule | Added to every fight | Dropped; strikes land on the opponent |
| 15 | NEWS_COMEDY auto-layer (build_prompt_v4.py:17) | T1, T33 (Director writes the beats) | Injected randomly | Not injected; comedy is written into each show's beats |

Gate run: 42 OK / 58 pending; the 16 BLOCKED are all ads without a reference image. Tests: 42 passed (v4 32 + v4.1 10), out/TEST-RESULTS-v41.txt.

## v4.2 append (2026-10-30 8:20 PM CT), Trundle t371u
| # | Conflict | His rule | v4.1 | v4.2 |
|---|---|---|---|---|
| 16 | "name + 2-3 visual keys" printed next to every image tag (REF-POLICY (b), Director's invention) | T40 | `MARLO QUILL (<IMAGE_2>; maroon porter's waistcoat with brass buttons, grey mustache)`, set details after "as in <IMAGE_1>:" | Name + tag only. New FAIL gate R-REFDESC. Superseded in RULES-OF-RECORD |
| 17 | v4.1 auto-attached channel cast sheets that do NOT show the named characters (Ch3, Ch7, Ch8, Ch9, Ch10, Ch12, Ch14), so text, sheet and start frame disagreed | T40, T5 (chain from real last frame) | Sheet attached but never pointed at; text described a look the sheet contradicts | Sheet dropped for those channels; free state-still crops from the parent's real last frame (state_stills_v42/) are the refs; ones whose parent isn't rendered are cut at file time (PENDING/) |
| 18 | P10-1 render: JACE closely resembles a real, famous actor | no real likeness | P10-2/3 chained off it | BLOCKED, needs Trundle's call |
| 19 | KILO (Ch14) has no image at all; sheet v2 shows other people | T3/T40 | P14-1..3 passed with a non-matching sheet | BLOCKED until a KILO ref exists (needs his yes) |
| 20 | Image gate scope | T41 | R-REF applied to built prompts only (confirmed); no comment code requires an image | Unchanged; documented |

Gate run v4.2: 37 OK / 58 (was 42; 5 newly blocked = #18, #19). Tests: 50 passed (v4 32 + v4.1 10 + v4.2 8), out/TEST-RESULTS-v42.txt.

> **v48 sync note (Oct 30 ~11:00 PM CT, Director):** See RULES-OF-RECORD T42-T45. Commenter images OFF (config/commenter_images.json); contributors sidecar-only + gate R-NOHANDLES; brand/name line in every bracket + gate R-BRANDS. **Stored prompts_v42 outputs predate the bracket change and need a (free) rebuild before go-live; R-REF hard FAIL is HELD pending Trundle.**
