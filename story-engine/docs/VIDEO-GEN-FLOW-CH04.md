# Video gen flow — Ch 4 Military Boutique
Written 2026-10-27 ~08:41 CT by Story Bot. Plan/docs only. No video gen this turn.
Also see: `/workspace/shared/streaming/MILITARY-BOUTIQUE-EXPERIMENTS.md`

## What goes into one CNB clip prompt (order)

1. **Channel style tail** (`configs/channels/04-military-boutique.yaml` look/sound + `snippets/ch04/style.yaml` `style_tail`)
2. **Negative / safety tags** (`snippets/ch04/style.yaml` `negative_safety_tags`) — always on; cannot be loosened
3. **Location tag** (`snippets/ch04/locations.yaml` or show `places[].look`)
4. **Character look tag(s)** (`snippets/ch04/characters.yaml` or show `cast[].look`) — omit for product-only B-roll
5. [SUPERSEDED 2026-10-30 by Story Bot: Director owns the prompt cascade and hands over finished beats/clip prompts; Story Bot sends no clip prompts to CNB and does no commercial scripts since Oct 29 12:00 PM CT. Historical only.] **Story Bot beat** (from episode outline / commercial script / news shot_list): action, camera, mood, VO line as note for assemble (VO is usually TTS in post, not in the image/video model)
6. **Reference stills** (if any under `references/ch04` or character cache) — attached as image refs to Imagine/fal; cited as IMAGE_0… in prompt when the provider supports it
7. **Post-only** (NOT in generator prompt): lower-thirds, thunder trundle bug, supers from on_screen_text registry, parody label (metadata and/or on-screen)

## Which layer wins
| Kind | Winner |
|---|---|
| tone, camera, length | slot > show/commercial/news item > channel |
| look tags | show/character/location snippet > channel style |
| tv_safe / banned / no-phone / trundle-products-only | strictest wins (union); nothing loosens |
| Story Bot dialogue/VO | beats file; burned via TTS + assemble, not the video model |

## Story Bot outputs → CNB inputs
| Story Bot output | Becomes |
|---|---|
| Show bible / show YAML cast+places | look tags + world constraints in every clip |
| Episode outline beats | one clip brief per beat (action + camera + mood) |
| Dialogue lines | TTS script / assemble; optional lip-sync only if approved later |
| Commercial YAML (pitch_beats, shot_list, vo_lines) | house-ad clip pack (10–30 s) |
| News YAML (headline, shot_list, lower_third) | news clip pack; L3 in post |
| Continuity JSON | avoid repeating resolved gags; not pasted into prompts |

## Worked example (hand-assembled, not generated)
Beat: Forward Supply E1 cold open — Bill salutes helmet pedestal; Mira S'mirin' invents "signal mauve".

```
Photoreal Military Boutique commercial look, luxury near-future showroom, matte black and graphite, museum lighting, cyan edge light, late-90s broadcast polish, center-weighted composition, no unintended text, no logos, no watermarks; intended text via tagged registry (post).
Tall adult host, stiff posture, boxy charcoal duty jacket, blank brass shift tag, short dark hair sharp side part, thin mouth, amber HUD glasses with no readable text, saluting a matte tactical helmet on a velvet pedestal.
Background: dark luxury showroom, matte-black pedestals, velvet pads, glass vitrines, blank HUD monitors soft cyan glow, empty of shoppers.
Camera: slow museum-light push-in. Mood: cool, clinical, slightly absurd.
No logos, no real insignia, no real people, no unintended text, no phone, no keypad, no dial UI, no weapons pointed at camera, no slapstick.
```

Optional refs: all slots empty (trundle 11:14: stills optional before pilot). Assemble adds L3 "MILITARY BOUTIQUE" + corner `4` + VO "Let's ship it forward."

## Known risks
- **Prompt too long** — models drop the tail; keep ≤ ~1200 chars; put safety tags early and late.
- **Character drift** — without reference stills, Bill/Mira faces may change every clip (stills optional per trundle 11:14).
- **Tags models ignore** — "no logos" / unintended text often fail; intended text via tagged registry, composite in post.
- **Over-specifying motion** — one camera move per shot (SERIES-PLAN / guide).
- **Seed IP bleed** — Death Stranding clips are seed video only; never name game IPs on screen.

## Export location
Local only: `/workspace/streaming/story-engine/data/exports/` and smoke `data/smoke/*/cnb_export/`.
**Do not send to CNB until trundle OKs.**
