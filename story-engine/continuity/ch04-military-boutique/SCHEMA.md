# Continuity Bible — schema (plain English)

Channel: thunder trundle Ch 4 Military Boutique
Path: `/workspace/streaming/story-engine/continuity/ch04-military-boutique/`
Home-only. TV-safe. American Hostage excluded (banned list only). No dial. No slapstick.
Written 2026-10-27 ~10:10 CT; revised ~11:10–11:12 CT. Status of content: DRAFT until trundle approves.

## What this is
The Continuity Bible is the locked memory for how 4 looks, sounds, and behaves across shows.
It is text + paths only. It does not generate video. It does not spend.

## trundle's model (do not break)
1. **Reference images** are consistency *targets* for the qualities they lock (palette, silhouette, lighting, wardrobe, prop shape, etc.). They are not frozen frames to copy pixel-for-pixel.
2. **Channel- and show-level base snippets** stay **LOCKED** (aesthetic, tone, hard constraints). Story Bot always includes them; they do not drift via casual edits.
3. **Variables** (cast looks, places, gags, aesthetic tags) start as `proposed` text pulled from configs. trundle's review observations isolate and refine one variable at a time. A refined value **promotes into the Bible only after trundle approves**.
4. **Aired video** later updates the Bible with what actually happened. **Callbacks** = real events from previous clips. **Generation quirks** = optional separate list of gen mistakes usable as later tricks — never automatic callbacks.
5. **On-screen text** is allowed where a show needs it, but every intended text element is tagged in `on_screen_text` for clean consistent application later (usually post).

## Files in this folder
| File | Role |
|---|---|
| `SCHEMA.md` | This document. Human-readable rules. |
| `bible.yaml` | The living Bible (status, locked snippets, variables, observations, refs, aired history). |
| `README.md` | Short how-to for Story Bot / trundle. |

Related (not in this folder):
- Runtime episode counters stay in `data/continuity/<show>.json` (what episode number ran).
- Smoke show bible at `data/smoke/forward-supply-ep1-20261027/bible.json` is unapproved test output; not this Bible.
- Source configs remain under `configs/` (channel, shows, snippets, commercials, news).

## bible.yaml sections
### meta
`channel`, `status` (`DRAFT` \| `APPROVED`), `home_only`, `tv_safe`, exclusions, pending flags (ref stills, smoke bible, house-ads expand TODO, station-id interval TODO).

### locked_base
Immutable until trundle explicitly changes them:
- **channel**: style_tail, palette, camera, tone, `inspiration_notes` (writers only — never in prompts), sound, tv_safe_rules, banned, house_ad_rules, station_id_clips, news_style, negative_safety_tags, reference_style, no_slapstick.
- **shows/<id>**: logline, format, length, season_arc.main, world_facts (as constraints). Shows Forward Supply, Clearance Brief, Depot After Hours are **kept**.

Nothing in `locked_base` may be loosened for romance, real brands, dial/phone CTAs, slapstick, or excluded titles.

### variables
Each entry: `id`, `kind` (`cast_look` \| `place` \| `gag` \| `aesthetic_tag` \| `catchphrase` \| `product_look`), `shows`, `current`, `source`, `status` (`proposed` \| `approved` \| `retired`), `version`, `approved_by` / `approved_at`, `notes`.

Cast ids (post-rename): `bill_dbears_look`, `mira_smirin_look`, `tim_look`, `osmund_look`, `voice_of_forward`.

### on_screen_text
Registry of intended text: `id`, `show`, `text`, `font_style_tag`, `placement`, `status`, `notes`. Applied consistently in post. No unintended/garbled text in gen.

### observations
Multi-note log **per clip**. Fields: `clip_id`, `observer`, `date`, `variable_id`, `note`, `proposed_change`, `decision`, `promoted_to_version`.

### reference_image_targets
Maps `variable_id` → `qualities_locked`, `image_path`, `status` (`none` \| `candidate` \| `locked`), `notes`. All slots empty/unlocked (trundle 11:14: no stills needed before pilot). Stills optional.

### aired_history
What actually shipped. Fields: `clip_id`/`episode_id`, `aired_at`, `summary`, `variables_touched`, `events` (real story events).

### callbacks
Real events from previous clips for continuity. **Not** generation mistakes.

### generation_quirks
Optional tricks from gen mistakes for later content. **Never** automatic callbacks.

### promotion_workflow / changelog
Legal path from observation → Bible change; dated append-only notes.

## What must never enter the Bible
- American Hostage (except the channel banned list).
- Dial / phone / keypad CTAs.
- Real defense brands, real game IPs, real people likeness (including inspiration IP names inside generation prompts).
- Outside commercial brands as house ads (trundle's products only).
- Explicit sex, graphic gore, weapon how-tos.
- Slapstick.

## Gaps (mark as TODO, do not invent)
- Reference stills optional (all slots empty; trundle 11:14).
- trundle confirm of candidates_from_notes / trundle_adds to expand house ads.
- Station ID interval.
- Any aired Forward Supply episode (smoke text only so far).
