"""Dress Inspection (Ch 4, Clearance Brief rebuild) prompt builder. Story Bot, 2026-10-27. No API calls."""
import json, sys, subprocess, hashlib
from pathlib import Path
sys.path.insert(0, 'story-engine/live'); import checker as C
import yaml
OUT = Path(__file__).parent
SE = Path('out-of-scope/streaming/story-engine')
MB = Path('out-of-scope/fakenews/channel-ready/thunder-trundle/4_Military-Boutique')
TF = Path('out-of-scope/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/lineage-tagfade-20261027')
ref = yaml.safe_load(open(SE/'live/ref-index.yaml'))['cast']
def refs(*keys):
    out = []
    for k in keys:
        for p in ref[k]['stills']:
            out.append(C.resolve_clean(p))   # clean-source lookup; raises on burned-text copies
    return out
BILL = ("Bill: tall, extremely muscular adult host with a huge chest, shoulders and arms, stiff posture, black utility duty shirt with sleeves "
        "straining at the arms, blank brass name tag on the chest, short dark graying hair with a sharp side part, square jaw, thin mouth, "
        "amber-tinted rectangular glasses with no readable text; always wears the shirt with sleeves and always wears the glasses.")
MIRA = ("Mira: compact adult officer, slate-gray short-sleeve duty tunic, olive utility scarf, long dark side braid, dry half-smile, "
        "black clipboard with four small color dots, cool cyan rim light on her face.")
OSM = ("Osmund: young adult man with a short buzz cut and light stubble, olive coveralls, blank brass tag on the chest, "
       "earnest worried expression.")
LOOK = ("Photoreal grounded near-future forward depot bay turned parade deck: wet concrete floor, hard top light, deep shadows, cold haze, "
        "seven matte pedestals in a straight line, each holding one product; biting, tough tone, never slapstick; candid observational framing, "
        "eyelines on each other or the products, characters never acknowledge the lens.")
AUDIO = ("Audio: dry and quiet; only boots on wet concrete, breathing and the low flat voice of Bill; no music, no hum, no sub-bass, "
         "no low drone; steady level.")
NEG = ["no real brands", "no logos", "no flags", "no insignia", "no on-screen text (all text added in post)", "no burned-in text, tags, badges or overlays",
       "no names", "no watermarks", "no extra people", "no young people", "no weapons", "no gore", "no slapstick", "no smoke", "no vapor",
       "no sleeveless Bill", "no Bill without glasses", "no eye contact with the lens", "no presenter pose", "no extra fingers", "no warped faces",
       "no music", "no low hum", "no sub-bass"]
POST_AUDIO = "Quiet dry bed: boots, breath, voice only; no music until the ad hits; no low hum or sub-bass; level to the house loudness standard in post."
# product beats -> registry name, ad slug, caption (overlay only), Bill's spoken line (audio)
PRODUCTS = [
 ("graphite-cloak-torso", "Graphite Cloak", 36, "A curtain with ambitions.", "You are a curtain. With ambitions."),
 ("scout-drone-jewelry", "Scout Drone", 34, "Jewelry that thinks it's a weapon.", "You are jewelry. Stop pretending."),
 ("tactical-helmet-pedestal", "Quietline Helmet", 30, "A salad bowl that reports for duty.", "Salad bowl. Reporting for duty."),
 ("modular-field-pack", "Modular Field Pack", 31, "Pockets. Just pockets. Pockets all the way down.", "Pockets. All the way down."),
 ("exo-gauntlet-vitrine", "Exo-Gauntlet", 33, "An oven mitt with a security clearance.", "An oven mitt. With clearance."),
 ("armored-showroom-cruiser", "Night Cruiser", 32, "A minivan that took one self-defense class.", "One self-defense class. One."),
 ("field-binoculars-velvet", "Field Glass", 35, "Binoculars that are afraid of distance.", "Afraid of distance. Noted."),
]
SURVIVOR = "Modular Field Pack"   # placeholder; Director's call
def frame(src, which, name):
    p = OUT/'anchors'/name
    if not p.exists():
        if which == 'first': cmd = ['ffmpeg','-v','error','-y','-i',src,'-frames:v','1',str(p)]
        else: cmd = ['ffmpeg','-v','error','-y','-sseof','-0.1','-i',src,'-update','1','-frames:v','1',str(p)]
        subprocess.run(cmd, check=True)
    return str(p)
def shot(sid, dur, cast, camera, action, dialogue, captions, keys, continues, props=()):
    raw = f'{LOOK} CAST (only these): ' + ' '.join({'Bill':BILL,'Mira':MIRA,'Osmund':OSM}[c] for c in cast) + \
          f' LOCATION: forward depot bay parade deck. CAMERA: {camera} ACTION: {action} {AUDIO} ' + \
          ' '.join(f'Caption "{t}".' for t in captions)
    gen, specs = C.split_overlay_text(raw, duration=dur)
    gen = gen.replace(C.NO_TEXT_CONSTRAINT, '').rstrip('; .').rstrip() + '. ' + C.NO_TEXT_CONSTRAINT + '; no readable text, no signage lettering'
    for s in specs: s['shot_id'] = sid
    names = {'Bill':"Commander Bill D'bears",'Mira':"Lt. Mira S'mirin'",'Osmund':'Osmund'}
    return {"id": sid, "duration_s": dur, "model": "grok-imagine-video-1.5", "resolution": "480p", "camera": camera,
            "cast": [names[c] for c in cast], "location": "Forward depot bay parade deck, wet concrete, seven pedestals",
            "lighting_fog": "hard top light, deep shadows, cold haze", "props_products": list(props),
            "continues_from": continues, "action": action, "dialogue": dialogue, "visual_prompt": gen,
            "reference_images": refs(*keys), "negative_prompt": NEG, "on_screen_text_post": [s['text'] for s in specs],
            "post_audio": POST_AUDIO, "status": "PROMPT ONLY - not rendered; needs trundle's yes with price"}, specs
shots, overlays = [], []
s, o = shot("DI-01", 6, ["Bill"], "locked symmetrical wide, no camera move.",
    "Seven products stand on matte pedestals in a straight line across the wet deck like recruits. Bill enters from frame left, boots loud, and halts at the first pedestal.",
    [], [], ["bill_dbears"], "cold open", [p[1]+": product on pedestal" for p in PRODUCTS])
shots.append(s); overlays += o
for i, (slug, name, gno, cap, line) in enumerate(PRODUCTS, 1):
    s, o = shot(f"DI-02-{i}", 6, ["Bill"], "low-angle handheld with an aggressive push-in.",
        f"Bill stops nose-to-nose with the {name} on its pedestal, leans in with his jaw tight and quiet menace, and delivers one flat line close to the product. Hard cut at the end of the line.",
        [{"speaker": "Commander Bill D'bears", "line": line}], [cap], ["bill_dbears"],
        "DI-01 end: Bill at the line of pedestals" if i == 1 else f"ad #{PRODUCTS[i-2][2]} hard cut back to the deck", [f"{name}: on pedestal"])
    shots.append(s); overlays += o
s, o = shot("DI-03", 6, ["Bill", "Mira"], "over the shoulder of Bill, handheld, slow drift.",
    "Mira walks behind Bill along the pedestal line, writing on her clipboard without looking up; she never reacts.", [], [], ["bill_dbears", "mira_smirin"],
    "cutaway after any takedown")
shots.append(s); overlays += o
s, o = shot("DI-04", 6, ["Osmund"], "tight close shot, locked.",
    "Osmund stands rigid at attention, sweat on his brow, his eyes flicking sideways toward Bill off-frame; he does not move.", [], [], ["osmund"],
    "cutaway after any takedown")
shots.append(s); overlays += o
s, o = shot("DI-05", 8, ["Bill", "Osmund"], "medium wide, locked, then holds on the empty deck.",
    f"Bill lifts the {SURVIVOR} off its pedestal, presses it into the hands of Osmund, turns and walks out of frame without a word. Osmund does not move. Hold two seconds on the empty deck.",
    [], ["PASSED: 1 / 7"], ["bill_dbears", "osmund"], "last ad hard cut back to the deck", [f"{SURVIVOR}: lifted from pedestal"])
shots.append(s); overlays += o
overlays.insert(0, {"text": "DRESS INSPECTION", "kind": "caption", "role": "bug", "position": "top_left", "start_s": 0.0, "end_s": None,
                    "style": "bug", "blocked": C.overlay_blocked("DRESS INSPECTION"), "airable": not C.overlay_blocked("DRESS INSPECTION"), "shot_id": "ALL"})
# guard: no overlay text may survive in any gen prompt
for s in shots:
    h = C.gen_prompt_requests_text(s['visual_prompt'].replace('no readable text, no signage lettering', '')); assert not h, (s["id"], h)
    for o in overlays:
        if o['shot_id'] in (s['id'],): assert o['text'] not in s['visual_prompt']
json.dump({"title": "Dress Inspection", "show": "clearance-brief (rebuild)", "channel": "4", "home_only": True,
           "brief": "out-of-scope/director/brief-dress-inspection-20261027.md", "written": "2026-10-27 CT by Story Bot",
           "shots": shots}, open(OUT/'prompts.json', 'w'), indent=1, ensure_ascii=False)
json.dump({"rule": "post-process overlay on a separate copy; never in generation; clean master is the anchor/mutation parent",
           "overlays": overlays}, open(OUT/'overlay_specs.json', 'w'), indent=1, ensure_ascii=False)
# bookkeeping
lin = [json.loads(l) for l in open(MB/'LINEAGE.jsonl')]
ads = {}
for r in lin:
    if r.get('row_type') == 'tagfade_air_copy' and r.get('global_no') in range(30, 37): ads[r['global_no']] = r
pulled_l = open('out-of-scope/streaming/PULLED-20261027.jsonl').read(); pulled_j = open('out-of-scope/shared/streaming/PULLED-20261027.json').read()
ad_rows, rows = [], []
for slug, name, gno, cap, line in PRODUCTS:
    r = ads[gno]; f = r['file']; sha = hashlib.sha256(open(f,'rb').read()).hexdigest()
    short = C.RAW_SHORT[slug]; master = str(MB/'raw'/f'mb_{short}.mp4')
    dur = float(subprocess.run(['ffprobe','-v','0','-show_entries','format=duration','-of','csv=p=0',f],capture_output=True,text=True).stdout)
    ad_rows.append({"product": name, "ad_global_no": gno, "ad_lineage": r['lineage'], "ad_tag": r['tag'], "file": f, "sha256": sha, "duration_s": dur,
        "audio_leveled": r.get('audio_leveled'), "needs_leveling": r.get('audio_leveled') is not True,
        "pulled": (Path(f).name in pulled_l or sha in pulled_l or Path(f).name in pulled_j or sha in pulled_j),
        "carries_mb_line": True, "clean_master": master, "ad_first_frame_clean": frame(master, 'first', f'ad{gno}_{short}_first.jpg'),
        "ad_last_frame_clean": frame(master, 'last', f'ad{gno}_{short}_last.jpg')})
for n, s in enumerate(shots):
    rows.append({"row_type": "pending_node", "status": "draft_pending_render_and_trundle_yes", "clip_id": f"ch4-di-{s['id'].lower()}",
        "lineage": "4.2", "tag": f"4.2 g1 #TBD", "gen": 1, "parent_global_no": None, "parent_id": None, "origin": "original (Clearance Brief rebuild, Director brief 2026-10-27)",
        "global_no": None, "global_no_note": "CNB assigns at render (LINEAGE max is 70; next free would be 71+)",
        "supersedes": None, "supersedes_note": "Color of the Day was a pitch only; no rendered clips replaced",
        "comment_prompt_ids": [], "slot_id": "ch4-S5", "alt_slot_id": "ch4-S8", "overlay_ids": [o['text'] for o in overlays if o['shot_id'] == s['id']],
        "clean_source": True, "audio_leveled": False, "written": "2026-10-27 CT"})
for r in rows:
    if r['clip_id'].startswith('ch4-di-di-02-'):
        i = int(r['clip_id'][-1]) - 1; a = ad_rows[i]
        r['anchor_out'] = {"cut": "hard", "next_clip": a['file'], "next_first_frame_clean": a['ad_first_frame_clean'],
                           "own_last_frame": "pending render (save from clean master after render)"}
        r['anchor_in_after_ad'] = a['ad_last_frame_clean']
with open(OUT/'bookkeeping-pending.jsonl', 'w') as f:
    for r in rows: f.write(json.dumps(r) + '\n')
    for a in ad_rows: f.write(json.dumps({"row_type": "reused_ad_ref", **a}) + '\n')
print(json.dumps(ad_rows, indent=1)); print(len(shots), sum(s['duration_s'] for s in shots), sum(a['duration_s'] for a in ad_rows))
