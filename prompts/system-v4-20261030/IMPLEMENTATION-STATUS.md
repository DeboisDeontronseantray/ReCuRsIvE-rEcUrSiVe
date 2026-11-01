# IMPLEMENTATION-STATUS (no "planned" entries). Files relative to system-v4-20261030/.
Gate = tools/apply_check_v4.py (A1–A15 imported from odyssey tools/apply_check.py, A2 replaced by V2; V1–V16 new). Builder raises GateFail on any FAIL.

## REASSESSMENT L1–L30
| # | Status | Where |
|---|---|---|
| L1 detail for wardrobe not action; no "very high" text | IMPLEMENTED | V9 keys ≤3 (apply_check_v4.py:45); A-checks |
| L2 one move per clip, precise motion | IMPLEMENTED | V5 :34; regen simplify_camera |
| L3 slapstick framing clears moderation | IMPLEMENTED | SAFETY_POOL layers_v4 |
| L4 start frame = real last frame; one location | IMPLEMENTED | ref_policy_v4.last_frame:10; spec start_frame |
| L5 end-on-image steers; literal words render | IMPLEMENTED | pinned ending build_prompt_v4.py:111 |
| L6 new char needs look sheet first | IMPLEMENTED (gate) | V15 no TBD refs :61 (Dynapage BLOCKED) |
| L7 ref present → name + 2–3 keys | IMPLEMENTED | V9 :45; build cast sentence |
| L8 buffs land only as main action | IMPLEMENTED | A-checks (imported) |
| L9 behaviour beats drop; object action lands | IMPLEMENTED | NEWS_COMEDY physical pool :18 |
| L10 low-health wrapper | IMPLEMENTED | A-check imported |
| L11 3–4 beats per 8–10 s | IMPLEMENTED | A-check imported |
| L12 face crop beats sheet | IMPLEMENTED | refs_side/*; V3 :29 |
| L13 no scripted out | IMPLEMENTED | A-check imported |
| L14 health numbers not quotable | IMPLEMENTED | A-check imported |
| L15 single 15 s take | IMPLEMENTED | duration in spec; "One continuous N s take" |
| L16 render ahead | WON'T DO here (ops policy, not prompt code) | — |
| L17 pinned last frame | IMPLEMENTED | spec.pinned / last_frame_path |
| L18 events need physical beats | IMPLEMENTED | fight grammar :25 |
| L19 arc headline leads | IMPLEMENTED | fixed thread arc line on beat clips (layers_v4) |
| L20 carried state line + still | IMPLEMENTED | carry_text decay :37 |
| L21 style lock fights ref | IMPLEMENTED | compact look pools; Ch4 corrected (CORRECTIONS-Ch4.md) |
| L22 zoom land-back bridge | IMPLEMENTED earlier | round9 tools/nest_zoom_v2.py; swap_timing bridge |
| L23 no held still | IMPLEMENTED | V1 :21, A3 |
| L24 router bug | WON'T DO (n/a to authored builds) | — |
| L25 commenter refs prop only | IMPLEMENTED | ref_policy_v4.commenter_filter:23 (fail-closed); V13 :56 |
| L26 JW verbatim base | IMPLEMENTED | regen keeps FC4 lines; NEEDS TRUNDLE on blood level |
| L27 suit-up matched pace | IMPLEMENTED | SU2–SU6 v4; stride_cut.py; SU1 NEEDS TRUNDLE (retry yes + start still) |
| L28 meta replaced | IMPLEMENTED | meta_check.py, meta_aliases.jsonl, swap_timing.json |
| L29 contact move+landing+result | IMPLEMENTED | :25, V12 |
| L30 bracketed delivery cues | IMPLEMENTED | V7 :39 |

## Checklist A1–A15: IMPLEMENTED as hard gate (imported unchanged except A2 → V2 photoreal Ch4).

## LEARNINGS-APPLIED F1–F5 (the 5 overwrites)
| F | Status | Where |
|---|---|---|
| F1 static flip exact circumstances | IMPLEMENTED | static_flip_v3.py walk/collapse_dot (real line→dot→glow) on top of v2 snow |
| F2 JW prompt verbatim base | IMPLEMENTED | FC4 lines kept, FC2/3 contact grammar layered; blood = NEEDS TRUNDLE |
| F3 pivot zoom on frozen still | IMPLEMENTED earlier | round9 nest_zoom_v2.py (live frames); swap_timing "in-world bridge" |
| F4 held-still seam | IMPLEMENTED | V1 + regen ending "Motion carries on through the last half second" |
| F5 burned seam labels | IMPLEMENTED | labels in sidecar v2 only; V16 no on-screen text |

## Decided ledger items
| # | Status |
|---|---|
| 44 Ch4 identity | IMPLEMENTED — resolved photoreal (ledger appended) |
| 29 96 s chain | WON'T DO — HELD by Trundle |
| 33 whip zoom, 34 v2 snow, 35 no long hold, 41 gate, 42 forced-layer changes, 43 META v2, 45 free builds, 46 FC fixes | IMPLEMENTED (treated as decided by t369u "fix all"): nest_zoom_v2/static_flip_v3; V1; apply_check_v4 in builder; layers_v4 kinds; meta_check+sidecar v2; palette_lut/stride_cut/lipcorr (local captioner: WON'T DO — no free model on box, tesseract absent); FC relabel via V11 |
| 6 Saga | NEEDS TRUNDLE (which Saga) |
| 37 look sheets, 38 SU pilot, 39 LS test, 40 commercials | NEEDS TRUNDLE (paid renders/images) — prompts regenerated and gated |
All other ledger rows (#1–5, 7–28, 30–32, 36) are OPEN questions, not decided → untouched.

## Fixed threads: config/fixed_threads.json — PENDING proposal FT1–FT4, NEEDS TRUNDLE.

> **v48 sync note (Oct 30 ~11:00 PM CT, Director):** See RULES-OF-RECORD T42-T45. Commenter images OFF (config/commenter_images.json); contributors sidecar-only + gate R-NOHANDLES; brand/name line in every bracket + gate R-BRANDS. **Stored prompts_v42 outputs predate the bracket change and need a (free) rebuild before go-live; R-REF hard FAIL is HELD pending Trundle.**
