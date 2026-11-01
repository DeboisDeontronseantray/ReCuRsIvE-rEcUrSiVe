# NOTES-IMPACT-LOG — every Trundle note, what it changed, where it is implemented
Times CT. "Impl" = file:line in system-v4-20261030 unless stated. Verbatim text given where I have it; memory items are paraphrased from saved memory (marked ≈).

| Date | Note (verbatim / ≈) | What it changed | Impl | Where I needed guidance |
|---|---|---|---|---|
| Oct 30 t362u | "fighting never actually make[s contact]" (FIGHT-CONTACT source) | fight grammar: move travels toward lens + lands on X + result + visible jolt, camera jerk; r9 FC2/FC3 wording kept, FC4/FC5 generic wording dropped | build_prompt_v4.py:25; gate V12 apply_check_v4.py:53 | blood level (see John Wick row) |
| Oct 30 t363u | suit-up stacking via matched-pace short gens | SU spec; tracking needs real start frame; still-prep step | regen_pending_v4.py odyssey() still-prep; V4 apply_check_v4.py:32 | SU1 retry = new shot version needs yes |
| Oct 30 t366u | meta will be replaced | version fields, alias table, swap timing, meta_check | config/meta_aliases.jsonl, config/swap_timing.json, tools/meta_check.py:15 | — |
| Oct 30 t369u | "Dont you think we should fix all the stuff … before we keep generating the wrong thing? … I'd rather have the things corrected before we lose it agsin" | this whole system-v4 build; hard gate; regen of all pending prompts | everything here | — |
| Oct 30 7:13 PM | Ch4 = photoreal 1971 | Ch4 lock flipped, ink refs blocked, corrections appended | config/channel_locks.json; V2/V2b; CORRECTIONS-Ch4.md | photoreal HERON/WOLFHOUND look sheets (GenerateImage) |
| Oct 30 (SU1 pilot) | front look-sheet refs pull head-on; "never at camera" alone fails | side/¾ crops only; named eyeline targets | refs_side/*; V3 :29; V6 :36; layers_v4 POOLS eyeline | — |
| Oct 30 (r9 scores) | stills beat text 4 vs 3; cuts on big camera change; subtle comedy didn't read; E1 shirt lost; P16-1 END | stills default carrier; one move per clip; physical sized comedy; costume still on transforms; motion-carries-on ending | layers_v4.carry_text:37; V5 :34; NEWS_COMEDY build_prompt_v4.py:18; V14 :59; V1 :21 | — |
| ≈ memory | authentic CRT static, first-test audio over second-test visuals | static_flip v2 snow kept | round9 tools/static_flip_v2.py (imported by v3) | — |
| ≈ memory | static = reality/Depth travel; CRT flip set, "wtf" cut-ins, monitoring-room push; intermediate-channel flips | channel walk with snow between heads, wtf cut-in 1 in 3, true collapse-to-dot | tools/static_flip_v3.py:20,35,41 | monitoring-room push not built (needs a room plate) |
| ≈ memory | log commenter credits | sidecar beats[].requester | build_prompt_v4.py sidecar; V8 | — |
| ≈ memory | bracketed format: only direction outside brackets | safety/rules in one trailing [bracket]; dialogue cues in [ ] | build_prompt_v4.py SAFETY_POOL use; V7 | whether ALL non-direction text must move into brackets (we keep look/setting outside) |
| ≈ memory | camera-jargon sentence | one camera sentence, simplified | regen simplify_camera:28 | — |
| ≈ memory | refs should show characters in the situation | state stills from real last frame | ref_policy_v4.state_stills:12 | — |
| ≈ memory | John Wick level for Ch4: "hard hits and some blood, but no gore" | his JW wording kept verbatim as base (F2) | regen keeps FC4 text | CONFLICT with safety line "no blood on skin" — needs his ruling |
| ≈ memory | low-health wrapper | L10 rule; wrapper beat first | gate A-checks (apply_check A-series) | — |
| ≈ memory | same-sex fight matchups | noted in spec; not auto-checked | WON'T auto-check (needs cast gender field) | add gender field to cards? |
| ≈ memory | obscured-in-purpose wording | kept in pools | layers_v4 POOLS | — |
| ≈ memory | word-order permutations + brackets to raise meta density | seeded shuffle of movable block, phrase pools | layers_v4.rng:15; build_prompt_v4 | — |
| ≈ memory | wants exact full prompts | full prompt verbatim in report; DIFF.md has full old/new | out/DIFF.md | — |
| ≈ memory | attach videos, not Drive links | reporting rule | n/a (parent reporting) | — |
| ≈ memory | don't get hung up on minor issues | gate = hard only on listed FAILs | apply_check_v4 | — |
| ≈ memory | bystander crossovers | not built here | NEEDS TRUNDLE (which channels) | yes |
| ≈ memory | problem registry + fix library | gate IDs = registry; FIX map in regen | apply_check_v4 IDs | — |
| ≈ memory | $500 cap, warn at $400 | no spend this build ($0) | — | — |
