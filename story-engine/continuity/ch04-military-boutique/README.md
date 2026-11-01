# Continuity Bible — Ch 4 Military Boutique

**Status: DRAFT — awaiting trundle approval.**
Path: `/workspace/streaming/story-engine/continuity/ch04-military-boutique/`
Home-only. TV-safe. No dial. No slapstick. American Hostage excluded.

## Files
- `SCHEMA.md` — plain-English rules and field meanings
- `bible.yaml` — locked base + proposed variables + empty observations/aired/callbacks/quirks
- `README.md` — this file

## How Story Bot uses this
1. Always include `locked_base.channel` (style, tone, tv_safe, banned, no-dial, no-slapstick). Never paste `inspiration_notes` studio/IP names into prompts.
2. Include the show's `locked_base.shows.<id>` for the episode being written.
3. Pull **approved** variables into clip prompts; if none are approved yet, use `proposed` text from configs only for drafts, and say so.
4. Reference images (when locked) constrain **qualities**, not frozen frames.
5. Log review notes under `observations.entries` (many rows per `clip_id` OK).
6. Promote a variable only after trundle says so (see `promotion_workflow` in bible.yaml).
7. After something airs / trundle accepts a render, append `aired_history` with real events → those feed `callbacks`. Optional gen mistakes go in `generation_quirks` only.
8. Intended on-screen text: register in `on_screen_text`; apply in post for consistency.
9. Station ID / "you're watching" bumps at the interval trundle sets (`station_id_clips`).

## Pending trundle calls (also in bible.yaml meta.pending_flags)
- Approve this Bible (`meta.status: APPROVED`) before treating it as locked memory.
- Reference stills: all slots empty; optional (trundle 11:14: none needed before pilot).
- Confirm candidates_from_notes / fill trundle_adds to expand house ads (Sky Diffuser, Lightning Lamp, StrataClip included; see bible house_ad_rules).
- Set station ID / "you're watching" interval.

## Kept (trundle 2026-10-27 ~11:12 CT)
- Shows: Forward Supply, Clearance Brief, Depot After Hours.
- House ads: Sky Diffuser, Lightning Lamp, StrataClip Ration Tin.

## Cast (post-rename)
- Commander Bill D'bears (was Vale Rook) — "Let's ship it forward."
- Lt. Mira S'mirin' (was Mira Quill) — catchphrases unchanged.
- Tim (was Pigeon-7) — chirps only.
- Depot Clerk Osmund, The Voice of Forward — unchanged names.

## Related paths
- Configs: `configs/channels/04-military-boutique.yaml`, `configs/shows/`, `configs/snippets/ch04/`
- Mapping: `docs/VIDEO-GEN-FLOW-CH04.md`
- Runtime episode counter (not this Bible): `data/continuity/forward-supply.json`
- Unapproved smoke bible: `data/smoke/forward-supply-ep1-20261027/bible.json`
- Plan pointer: `/workspace/shared/streaming/STORY-CONFIG-PLAN.md`

## Do not
- Generate video or spend from this folder.
- Send exports to CNB / air / publish / post without trundle OK.
- Invent new cast, places, or products beyond configs; mark gaps TODO.
- Use slapstick. Paste inspiration IP/studio names into generation prompts.
