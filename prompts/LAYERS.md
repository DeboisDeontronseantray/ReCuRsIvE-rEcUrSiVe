# Prompt layers (Director, Oct 28 2026)
Every render prompt is assembled in this order. System wrappers are ALWAYS applied; the commenter layer is optional and comes last.

1. global   prompts/_global.md            network-wide rules: photoreal, no kids, no real people/brands, in-scene text preferred, home-only
2. channel  prompts/<NN-channel>/_channel.md   channel tone + limits (Ch 4: Cold War espionage, 35mm, steel blue / signal orange)
3. format   prompts/<NN-channel>/_show.md or _commercial.md   show bible look OR commercial rules (ads stay separate breaks)
4. show/ad  prompts/<NN-channel>/<show>/_wrapper.md   characters, locations, look, continuity refs
5. shot     segment sidecar (segments/<shot>.yaml): the 7-block prompt, keyframes, screen_inserts
6. commenter (optional) a request from commenter/<NN>/approved/: may change action, dialogue, props, weather, or add screen_inserts ("TV on the wall plays #58"). It can never override layers 1-3 (safety, home-only, channel identity).

Conflicts: a lower number wins over a higher one, except layer 6 may change layer 4-5 details.
Lineage: record the sha256 of each layer file used (prompt_layers: {global, channel, format, wrapper, shot, commenter}) in the row.
Embeds from commenters are resolved with engine/resolve_embed.py (#number refs only, clean masters only).

2026-10-28 12:40 CT (trundle 12:33 CT): "no eye contact with camera" / observational framing is a PER-SHOW rule, not global. Shows opt in via their _wrapper.md or show.yaml no_eye_contact: true (Black Ice opts in). Story Bot, add-only.

2026-10-28 12:45 CT CORRECTION (Director spec; trundle 10:41 CT): no eye contact with camera IS GLOBAL (layer 1, every character, every channel). Only the 'window into lives' observational framing is Forward Supply-only. The 12:40 note above is superseded for eye contact. Story Bot, add-only.

2026-10-28 6:15 PM CT (Director, approved by trundle 6:14 PM CT): layer 6 record format is COMMENTER-SCHEMA.md (+ commenter-prompt.schema.json). Add-only.
2026-10-28 6:46 PM CT (Director, trundle-approved 6:46 PM): experiment protocol is EXPERIMENT-PROTOCOL.md. Add-only.

2026-10-28 ~10:30 PM CT (Director, trundle t121): dense output mode and the gen/extend take policy are in PROMPT-STYLE.md. Same 6 layers; output is one plain-English paragraph + @ImageN refs. Add-only.


## 2026-10-28 note (trundle t132): reference image REQUIRED
Every render prompt must include at least 1 reference image (@Image1+), character sheets first. Not optional. Dense assembly raises MissingReferenceImageError when 0 refs resolve.

## 2026-10-28 ~11:15 PM CT, style references allowed (Director, trundle t135u; supersedes "Never name real directors or artists as style")
- ALLOWED: naming films, franchises, genres and directors' styles as STYLE references, e.g. "realistic, technical fight choreography like a John Wick movie but more intense".
- STILL NOT ALLOWED: real actors' likeness or voices on screen, real people as characters, real brands outside parody.
