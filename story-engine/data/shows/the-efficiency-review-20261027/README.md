# The Efficiency Review — Ch 4 (Military Boutique), lineage 4.12 g1 (original)
Story Bot, 2026-10-27 CT. Home-only. PROMPTS ONLY — nothing rendered, queued or aired.
Brief: /workspace/director/brief-the-efficiency-review-20261027.md (plot unchanged). Builder: build.py (no API calls).

## Files
prompts.json (14 shots, grok-imagine-video-1.5, 480p, cast refs from ref-index, dialogue field) · overlay_specs.json (all on-screen text, post only) ·
bookkeeping-pending.jsonl (14 pending_node rows, lineage 4.12 g1, + ad_pod_plan row) · checker-result.json · build.py

## Runtime and cost
- Program: 12 × 10 s + 2 × 12 s = **144 s (2:24)**; ads add their own runtime.
- Brief's per-shot estimate: 14 × $0.53 = **$7.42**. This matches the measured Dress Inspection rate ($5.83 / 111 s ≈ $0.0525/s → 144 s ≈ $7.56).
- **Clash:** a flat $0.087/s gives 144 × 0.087 = **$12.53**, which is over the $9.30 cap. $0.087/s does not match the measured rate; $7.42 implies ~$0.0515/s. CNB must confirm the real rate before rendering.
- Hard cap **$9.30 including retries**; max 2 paid tries per clip. Note 2 tries on every clip (~$14.84) would exceed the cap — only ~3–4 retries fit. Stop and check back before exceeding $9.30.

## Cut plan (ad pods; products are NOT in the story)
ER-01…ER-05 (Act 1) → **AD POD 1: #30, #31** → ER-06…ER-10 (Act 2) → **AD POD 2: #32, #33, #34** → ER-11…ER-14 (Act 3) → **AD POD 3 / outro: #35, #36**.
Ads are used untouched (reused, $0). Ad pods are clean breaks.

## Dress Inspection
Dress Inspection (4.2 g1, #71–81) is **shelved and must not air**.

## Hard rules applied
Bill explicitly sleeved + "exactly one Bill" in every Bill shot; "no second Bill / no sleeveless Bill" in negatives (fixes #73 duplicate and #76/#77 sleeveless flaws). Mira included wherever the brief has her (S02, S03, S05, S07, S09, S10, S12, S14). Every prompt ends "no readable text". No real brands, no kids, no personal names on screen, no money/donation/tip lines. Airing needs a separate yes from trundle.

## Continuity clashes and fixes
1. Tim: brief + configs/snippets/ch04/characters.yaml say "matte-graphite courier drone with antennas"; bible-v2 locks Tim as a floating cyber-brain under a glass dome with one cyan optic → prompts use the bible-locked look and tim-E5 refs; "drone" kept only as his job in the story.
2. Tim speaks only in chirps (bible/checker) → Tim has no spoken words; ER-12 gives him one chirp with the blink.
3. Bill wardrobe: brief/characters.yaml "boxy charcoal duty jacket" vs bible locked "black utility duty shirt" (+ qualities "charcoal jacket") → charcoal jacket with full-length sleeves over the black duty shirt, sleeves on to the wrists.
4. Osmund's bible look carries the big modular field pack, which is a sold product (Modular Field Pack, ad #31) → dropped from Osmund this episode ("no backpack") so no product appears in the story.
5. Loading bay: brief "rain, cool light" vs bible "rolling night fog, amber safety lights" → rain + rolling fog, amber safety lights mixed with cool light (fog never lifts).
6. Mira's clipboard has four color dots in the bible; brief's "blank clipboard" + box labeled "B" → clipboard keeps its dots; she sticks a red sticker beside a blank square; the "B" exists only as an overlay.
7. Folder title, "FILED BY: TIM", verdict and "EFFICIENCY: IMPROVED." were described as on-screen text → all moved to overlay_specs.json; folder/pages are "plain/blank" in prompts.
8. Brief shows products as background set dressing → prompts keep merchandise as soft out-of-focus shapes, never featured; props_products empty.
9. Chain exceptions in the brief (ER-12 starts on ER-10 last, ER-13 on ER-11 last) are kept as written; CNB must save those last frames from clean masters.
10. Cost: $0.087/s vs $7.42 mismatch (see above) → reported, not resolved; render must not exceed $9.30.

## Checker / tests
live/checker.py on prompts.json: 14 pass, 0 warn, 0 fail. live/tests: 95 passed.
No bible edit was needed.
