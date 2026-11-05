import json, sys
sys.path.insert(0, "story-engine/live"); import checker
RAW = "out-of-scope/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/raw/"
STYLE = ("Photoreal Military Boutique catalog still, luxury near-future military-cyberpunk showroom, matte black and graphite steel, chrome fittings, "
         "olive accents, cyan edge light, museum spot lighting, soft grey fog haze in the background, late-90s broadcast polish, center-weighted 16:9 hero composition with clear headroom and empty lower third for post overlays.")
AUD = "Audio: quiet, unobtrusive ambient bed (soft room tone, faint servo ticks, light showroom air); no droning low hum, no sub-bass rumble, no engine drone; dialogue and VO sit clearly above the bed."
NEG = ["no names", "no signatures", "no watermarks", "no low hum", "no droning bass", "no text", "no words", "no letters", "no numbers", "no labels", "no logos", "no brand names", "no watermarks", "no price tags",
       "no channel bug", "no badges or tags", "no insignia", "no flags", "no weapons", "no people unless specified", "no real products", "no garbled text"]
P = [
 ("modular-field-pack", "Modular Field Pack", "mb_pack.mp4",
  "a large olive and black weatherproof modular field pack on a quick-release graphite frame, standing on a lit glass plinth; dozens of small identical pouches in tidy rows, each with a blank brass number plate (plates blank); one side pouch open showing a molded warm insert with a faint amber glow; a brass shift-tag loop on the chest strap; thin cyan edge light tracing the frame seams",
  ["38 numbered pouches, none labeled", "Warm Pocket insert that fits one Quietline Helmet", "weatherproof shell, quick-release frame", "brass shift-tag loop"]),
 ("armored-showroom-cruiser", "Night Cruiser", "mb_rover.mp4",
  "a sleek graphite armored showroom cruiser, four-wheeled, smooth comfort-armor panels, parked on a polished black showroom floor in front of a fogged glass wall; low amber fog-glide headlights casting a soft beam into the haze; cyan edge light along the roofline; open rear cargo deck neatly stacked with sealed insulated ration packs; no turrets, no mounts, no weapons",
  ["graphite comfort-armor panels", "fog-glide amber headlights", "cabin hush", "cargo deck for 40 Thermal Ration Packs", "showroom/depot runs only"]),
 ("exo-gauntlet", "Exo-Gauntlet", "mb_gauntlet.mp4",
  "a single right-hand powered exo-gauntlet displayed upright in a glass vitrine on black velvet; segmented graphite and chrome plates over a glove-in-glove fit, visible tendon cables along the fingers; a cyan light line across the knuckles glowing at mid level; beside it a small open crate of sealed ration tins and a sheet of colored dot stickers as demo props",
  ["grip-assist tendons lift a full crate", "fingertip pads sort stickers by color", "cyan knuckle line shows assist level", "graphite and chrome segments", "lifting and sorting tool only"]),
 ("scout-drone", "Scout Drone", "mb_drone.mp4",
  "a compact matte graphite four-rotor scout drone hovering a hand's width above an open black velvet jewelry-style docking case; slim whisper rotors with soft motion blur; a subtle pearl-grey fog-sense skin panel on top shimmering faintly; a small cyan status light; fog haze curling around it under museum spotlights",
  ["fog-sense skin measures fog density", "finds lost inventory by temperature", "returns to velvet dock", "whisper rotors, matte graphite", "inventory and weather scouting only"]),
 ("field-binoculars", "Field Glass", "mb_binoculars.mp4",
  "a pair of weighted graphite field binoculars resting on a velvet rest atop a black glass pedestal; brass lens caps hanging on a fine brass chain; the objective lenses reflecting layered grey fog in many subtle shades; cyan rim light on the barrel edges; fogged showroom window behind",
  ["fog-graded optics, 12 shades of grey", "reticle that confirms the fog has not lifted", "velvet rest, lens caps on brass chain", "weighted graphite barrels", "viewing only"]),
 ("graphite-cloak", "Graphite Cloak", "mb_cloak.mp4",
  "a long hooded graphite cloak draped on a faceless matte black display torso; fine fog-match weave whose grey subtly blends into the haze behind it; the hood edge with a neat channel seam; beside the torso, a second cloak folded into a perfect square on a low plinth; soft museum spot light and cyan edge light",
  ["fog-match weave matches the day's fog grey", "warm through a full night watch", "hood channels condensation away from glasses", "folds to a perfect square", "not invisibility, not armor"]),
 ("make-a-clip-remote", "Make A Clip Remote", None,
  "a plain black universal TV-style remote about 15 cm long, no markings, lying at a slight angle on a graphite display pad under a glass dome; standard rubber keypad with all keys blank, one key slightly highlighted by spot light; a faint tiny board LED glow visible through a seam; in the soft-focus background a fogged screen showing an abstract out-of-focus glow",
  ["press one key and speak an idea", "the home AI turns it into a clip for the next break", "silent press, only a tiny board LED", "black ~15 cm remote shell; home prototype, not for sale"]),
 ("river-cooled-peltier-ice-cooler", "River-Cooled Peltier Ice Cooler", None,
  "a rugged olive and graphite camping cooler sitting on smooth river stones at the edge of a shallow clear stream in a misty forest; a finned graphite heat-exchanger plate and a short braided hose dipping into the flowing water; lid slightly open showing clear ice and frost inside; cyan edge light on the metal fins; morning fog between dark pines",
  ["solid-state Peltier modules", "flowing river water as the heat sink", "refreezes meltwater into ice with a brine bath", "for river, forest or lake camping; concept, not for sale"]),
]
out = []
for pid, name, raw, look, sell in P:
    ref = None; blocked = None
    if raw:
        try: ref = checker.resolve_clean(RAW + raw)   # clean, untagged master; raises if watchlisted
        except checker.CleanSourceError as e: ref = None; blocked = str(e)
    out.append({"id": f"still-{pid}", "product_id": pid, "product_name": name, "model": "grok-imagine-image",
        "aspect": "16:9", "lineage": "4.4", "origin": "first_render",
        "prompt": f"{STYLE} Product: {look}. Selling points shown visually (no text): " + "; ".join(sell) + ". Clean frame, nothing written anywhere in the image. " + AUD, "audio": AUD,
        "negative_prompt": NEG, "selling_points": sell,
        "reference_frame_source": ref, "reference_blocked": blocked, "reference_note": ("held: clean master tripped watchlist pHash; text-only until CNB clears it" if blocked else "clean raw master; CNB pulls one frame at render time" if ref else "no clip or still exists; text-only prompt"),
        "on_screen_text_post": "product name / tagline / price added in post with overlay A layout, never baked in",
        "status": "PROMPT ONLY - not rendered; home-only"})
for o in out:
    assert not checker.brand_hits(checker.strip_negated(o["prompt"])), o["id"]
    assert not checker.unsafe_hits(checker.strip_negated(o["prompt"])), o["id"]
json.dump({"title": "Ch 4 product-still prompts (8 products without stills)", "written": "2026-10-27 CT Story Bot", "stills": out},
          open("story-engine/data/stills-20261027/product-stills-prompts-20261027.json", "x"), indent=1, ensure_ascii=False)
print("ok", len(out))
