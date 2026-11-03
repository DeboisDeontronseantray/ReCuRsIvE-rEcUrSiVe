# system-v4-20261030
tools/build_prompt_v4.py (spec → args + tt-clipmeta/v2 sidecar, hard gate) · tools/apply_check_v4.py · tools/layers_v4.py · tools/meta_check.py · tools/ref_policy_v4.py · tools/palette_lut.py · tools/stride_cut.py · tools/lipcorr.py · tools/static_flip_v3.py · tools/regen_pending_v4.py (regenerates everything pending → prompts_v4/, out/DIFF.md, out/diff.jsonl).
Tests: `python3 -m unittest tests/test_v4.py` (32 pass, out/TEST-RESULTS.txt). Backups of appended files: backups/.

v4.2 (Oct 30 8:20 PM CT, Trundle t371u): tools/build_prompt_v42.py, tools/apply_check_v42.py (R-REFDESC), tools/regen_v42.py -> prompts_v42/, out/DIFF-v42.md. v4.1 untouched.

> **v48 sync note (Oct 30 ~11:00 PM CT, Director):** See RULES-OF-RECORD T42-T45. Commenter images OFF (config/commenter_images.json); contributors sidecar-only + gate R-NOHANDLES; brand/name line in every bracket + gate R-BRANDS. **Stored prompts_v42 outputs predate the bracket change and need a (free) rebuild before go-live; R-REF hard FAIL is HELD pending Trundle.**

Note (Oct 30, 2026, 11:26 PM CT, Director): the v4/odyssey gate (tools/apply_check_v4*.py) is RETIRED and kept for history only. The live gate is tools/apply_check_v44.py (RULES-OF-RECORD T48/T49). Don't use apply_check_v4 for new prompts.

> **Canon fix (Nov 2 2026, 1:02 PM CT, Director New; flagged by Story Bot 11-02):** tools/canon.py + config/canon_aliases.json now map superseded source names/looks to show-bible canon before every build (Ch11 GIDEON QUILL, ch11.gideon_quill: faded burgundy porter uniform, brass buttons, loosened collar, no mustache; Ch14 cast Vee/Onyx/Pixel). config/static_v41.json fixed; refs_side/MARLO_QUILL_* renamed GIDEON_QUILL_*; regen_v42 Ch7 monster = Cyborg Bear. prompts_v43 and prompts_v44 regenerated (gate 53 PASS / 0 FAIL / 5 HELD). prompts_v4/v41/v42 marked SUPERSEDED (archival). Pre-fix copy: coordination/handoff-notes/archive/canon-fix-20261102/.
