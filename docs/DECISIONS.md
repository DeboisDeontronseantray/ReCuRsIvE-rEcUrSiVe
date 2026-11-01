# Locked decisions

Every decision the owner has locked. Each has a stable id that PR bodies cite; new decisions are appended at the bottom. A newer entry
supersedes an older one only where it says so. Changing an entry needs the owner's yes; agents add rows, they
don't rewrite them. Times are US Central unless marked UTC.

| Id | Date | Decision | Source |
|---|---|---|---|
| DEC-01 | Oct 27, 2026, 4:51 PM | **Nobody looks into the camera.** No eye contact with the lens or the audience, and no fourth-wall breaks. Made absolute ("never", with no owner-yes exception) on Oct 29 (T25). | `briefs/CURRENT-RULES.md` L509; `prompts/system-v4-20261030/RULES-OF-RECORD.md` T25 |
| DEC-02 | Oct 28, 2026, 12:44 PM | **Masters stay pure.** Show masters carry no embedded commercials, unrelated clips, burned-in genealogy or overlays. | `briefs/CURRENT-RULES.md` L137 |
| DEC-03 | Oct 30, 2026, 1:24 AM | **xAI spend cap is $500 a month** (warn at $400). | `briefs/CURRENT-RULES.md` L84 |
| DEC-04 | Oct 30, 2026, 7:13 PM | **Ch4 is photoreal 1971** (live action; ink references blocked for Ch4). | `briefs/CURRENT-RULES.md` L536; `prompts/system-v4-20261030/CORRECTIONS-Ch4.md` |
| DEC-05 | Oct 30, 2026, 10:48 PM | **Commenter images are off.** Only trundle turns them on. | `briefs/CURRENT-RULES.md` L493; v5 `CommenterImagesOn` (PR #9) |
| DEC-06 | Oct 30, 2026, 11:12 PM; D8 Oct 31, 10:32 PM | **FT1–FT4 are off** until trundle sees and approves them. | `briefs/CURRENT-RULES.md` L630; `docs/PLAN-prompt-assembly-v1.md` D8 (PR #3) |
| DEC-07 | Oct 31, 2026, 10:32 PM (D4) | **No handles in prompts.** Contributor handles, e-mails and ids never reach prompt text (R-NOHANDLES). | `docs/PLAN-prompt-assembly-v1.md` D4 (PR #3) |
| DEC-08 | Oct 30, 2026, 11:10 PM; Nov 1, 2026 | **Reference images are the identity lock.** Every prompt carries a reference image (hard rule; only the 16 listed ads are exempt). Identity comes from the reference images, not from text descriptions. | `briefs/CURRENT-RULES.md` L614; owner direction Nov 1 |
| DEC-09 | Nov 1, 2026 | **Generation is xAI / Grok Imagine only.** No other render or vision provider. | Owner direction Nov 1 |
| DEC-10 | Nov 1, 2026 (standing yes-gate) | **Every render needs the owner's yes and its price** before it runs. Nothing paid runs without both. | `briefs/CURRENT-RULES.md` yes-gates; owner direction Nov 1 |
| DEC-11 | Nov 1, 2026, 13:47 UTC | **Option 1 clothing rule: meta is for story only.** Stills and reference images carry wardrobe and continuity; still meta never re-describes clothing as text. | `prompts/stills-meta-v1/PLAN.md` Q4 (PR #11) |
| DEC-12 | Nov 1, 2026 | **Bible resolutions.** Ch4 is Military Boutique / BLACK ICE. The Ch2 anchors are Dora Vance and Hal Brisk, with Tess Okafor, Gale Morrow and Skip. Ch11 is Fist Theater, and its main show is The Night Porter. Marla (with Dale) is on Ch12, *Dale & Marla Live*. | `docs/canon/BIBLE-CONFLICTS-RESOLUTION-v1.md` (PR #17) |
| DEC-13 | Nov 1, 2026 | **Owner names are lowercase `trundle` or `thundertrundle` only.** The owner's real first name never appears in repo files, prompts or on screen; code that must recognize it decodes it at runtime. | Owner direction Nov 1; PR #20 |
| DEC-14 | Nov 1, 2026 | **Live files are read-only until their PRs are ready.** Agents work on repo copies and fixtures; nothing writes to the live box. | Owner direction Nov 1 |
| DEC-15 | Nov 1, 2026 | **The owner merges.** Agents never merge or enable auto-merge. *Superseded by DEC-20.* | Owner direction Nov 1 |
| DEC-16 | Nov 1, 2026 | **Merge order is bottom-up per stack.** #20 merges before #18, and #18 is superseded by #20. | Owner direction Nov 1 |
| DEC-17 | Nov 1, 2026 | **Ads and breaks are never trait evidence.** Ads and breaks may contain show characters, but character-memory `trait_observations` skip ad and break items. | Owner direction Nov 1; PRs #21, #22 |
| DEC-18 | Nov 1, 2026 | **"One live instance" means one copy of the same character at a time,** not one person on screen. Any number of different characters may share a shot. | Owner direction Nov 1; PRs #21, #22 |
| DEC-19 | Oct 31, 2026, 10:32 PM | **Only aired clips are canon.** A clip counts once playout marks it AIRED (slot `status: AIRED` with `aired_at`, joined to LINEAGE); missing means not aired, and unaired renders are ignored. Character-meta promotion needs N=3 distinct aired show clips; approval stays owner-only. | `docs/plans/CHARACTER-META-PLAN.md` plan approval (PR #6); PRs #15, #19 |
| DEC-20 | Nov 1, 2026, 11:04 AM | **"Yes go."** trundle approves all corrected pushes, commits and merges that align with these decisions. Merge order: #1, then #20 (closing #18 as superseded), then #23, then each stack bottom-up once checks are green and real findings are fixed: #3→#7→#9→#19→#22; #2→#11; #4→#10; #5→#12→#13/#14; #6→#8→#15/#16→#21. Stacked PRs are retargeted to main as their bases merge. Still no renders, paid API calls or go-live. Supersedes DEC-15. | Owner message Nov 1 |
| DEC-21 | Nov 1, 2026, 11:09 AM | **Trait promotion needs 3 aired clips.** Confirms the N=3 distinct aired show clips in DEC-19. | Owner confirmation Nov 1 |
| DEC-22 | Nov 1, 2026, 11:09 AM | **Forward Supply stays as Ch4 filler.** | Owner confirmation Nov 1 |
| DEC-23 | Nov 1, 2026, 11:09 AM | **Marla appears on Ch2 only as a deliberate crossover.** Her home stays Ch12 (DEC-12). | Owner confirmation Nov 1 |
| DEC-24 | Nov 1, 2026, 11:09 AM | **X partnerships scope is confirmed** as trundle stated it on Nov 1. | Owner confirmation Nov 1 |
