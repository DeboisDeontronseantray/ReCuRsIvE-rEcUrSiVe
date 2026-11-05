"""The Efficiency Review (Ch 4, lineage 4.12 g1) prompt builder. Story Bot, 2026-10-27. No API calls, no renders."""
import json, sys
from pathlib import Path
sys.path.insert(0, 'story-engine/live'); import checker as C
import yaml
OUT = Path(__file__).parent
SE = Path('out-of-scope/streaming/story-engine')
ref = yaml.safe_load(open(SE/'live/ref-index.yaml'))['cast']
def refs(*keys):
    return [C.resolve_clean(p) for k in keys for p in ref[k]['stills']]
LINEAGE = "4.12"
BILL = ("Bill (exactly one Bill in frame, never duplicated): tall, extremely muscular adult host with a huge chest, shoulders and arms, stiff posture, "
        "boxy charcoal duty jacket with full-length sleeves over a black utility duty shirt, both sleeves on and down to the wrists, blank brass name tag on the chest, "
        "short dark graying hair with a sharp side part, square jaw, thin mouth, amber-tinted rectangular glasses; always sleeved, always wears the glasses.")
MIRA = ("Mira: compact adult co-host, slate-gray short-sleeve duty tunic, olive utility scarf, long dark side braid, dry half-smile, "
        "black clipboard with four small color dots (blue, yellow, green, red), cool cyan rim light on her face.")
OSM = ("Osmund: young adult man with a short buzz cut and light stubble, olive coveralls, blank brass tag on the chest, slightly out of breath, "
       "earnest worried expression; no backpack in this episode.")
TIM = ("Tim: floating cybernetic brain the size of a beach ball, gray textured brain under a tall clear glass dome, dark armored ring with one glowing cyan optic, "
       "small cyan hover thrusters underneath, black cables trailing below, small rectangular implant chips with tiny cyan lights on its right side, hovering at shoulder height; silent.")
LOOKS = {'Bill': BILL, 'Mira': MIRA, 'Osmund': OSM, 'Tim': TIM}
KEYS = {'Bill': 'bill_dbears', 'Mira': 'mira_smirin', 'Osmund': 'osmund', 'Tim': 'tim'}
NAMES = {'Bill': "Commander Bill D'bears", 'Mira': "Lt. Mira S'mirin'", 'Osmund': 'Osmund', 'Tim': 'Tim'}
SHOWROOM = ("Photoreal near-future luxury showroom after closing: matte-black pedestals, glass vitrines, chrome and olive walls, blank monitors with soft cyan glow, "
            "museum lighting, empty of shoppers, merchandise only as soft out-of-focus background shapes, never featured; dry, quiet office-politics tone, nobody yells, "
            "never slapstick; candid observational framing, eyelines on each other, characters never acknowledge the lens.")
BAY = ("Photoreal near-future sterile loading bay at night: steady rain past the open dock edge, rolling night fog, amber safety lights mixed with cool blue light, "
       "empty crates with blank tags, a warm-lit showroom doorway in the background; dry, quiet tone, never slapstick; candid observational framing, characters never acknowledge the lens.")
AUDIO = "Audio: museum-quiet room tone, footsteps, paper, breathing and low calm voices; no music, no hum, no sub-bass, no low drone; steady level."
NEG = ["no real brands", "no logos", "no flags", "no insignia", "no on-screen text (all text added in post)", "no burned-in text, tags, badges or overlays",
       "no names", "no watermarks", "no extra people", "no young people", "no weapons", "no gore", "no slapstick", "no shouting",
       "no sleeveless Bill", "no bare arms on Bill", "no second Bill", "no duplicate characters", "no Bill without glasses",
       "no product close-ups", "no eye contact with the lens", "no presenter pose", "no extra fingers", "no warped faces", "no music", "no low hum", "no sub-bass"]
POST_AUDIO = "Quiet dry bed; dialogue clean; level to the house loudness standard in post."
shots, overlays = [], []
def shot(sid, dur, cast, camera, action, dialogue, captions, chain, loc='showroom', act=1):
    look = BAY if loc == 'bay' else SHOWROOM
    raw = f'{look} CAST (only these, one of each): ' + ' '.join(LOOKS[c] for c in cast) + f' CAMERA: {camera} ACTION: {action} {AUDIO}'
    gen, _ = C.split_overlay_text(raw, duration=dur)
    gen = gen.replace(C.NO_TEXT_CONSTRAINT, '').rstrip('; .').rstrip() + '. ' + C.NO_TEXT_CONSTRAINT + '; no readable text'
    if 'Bill' in cast: assert 'sleeves on' in gen and 'exactly one Bill' in gen
    for t, pos, s0, s1 in captions:
        overlays.append({"text": t, "kind": "caption", "role": "caption", "position": pos, "start_s": s0, "end_s": s1, "style": "default",
                         "blocked": C.overlay_blocked(t), "airable": not C.overlay_blocked(t), "shot_id": sid})
    shots.append({"id": sid, "act": act, "duration_s": dur, "model": "grok-imagine-video-1.5", "resolution": "480p", "camera": camera,
        "cast": [NAMES[c] for c in cast],
        "location": "Loading bay behind the showroom, night rain and fog" if loc == 'bay' else "Military Boutique showroom after closing",
        "lighting_fog": "amber safety lights, cool rain light, rolling fog" if loc == 'bay' else "museum lighting, cyan edge light",
        "props_products": [], "continues_from": chain, "action": action,
        "dialogue": [{"speaker": NAMES[s], "line": l} for s, l in dialogue], "visual_prompt": gen,
        "reference_images": refs(*[KEYS[c] for c in cast]), "negative_prompt": NEG,
        "on_screen_text_post": [c[0] for c in captions], "post_audio": POST_AUDIO,
        "status": "PROMPT ONLY - not rendered; trundle approved render 8:16 PM CT cap $9.30 (per Director relay); airing needs a separate yes"})
# ACT 1
shot("ER-01", 10, ['Osmund'], "slow push-in, one move.",
     "Wide view of the dark, closed showroom. Osmund hurries in, out of breath, holding a sealed plain folder against his chest, and stops at center floor.",
     [('Osmund', "Efficiency review. One host gets reassigned by morning.")], [], "NEW (establishing)")
shot("ER-02", 10, ['Bill', 'Mira', 'Osmund'], "locked medium, no move.",
     "Bill and Mira turn from the counter toward Osmund with matching polite smiles and give a short, easy laugh together; their eyes stay calculating.",
     [('Bill', "Reassigned. Sure."), ('Mira', "How exciting for someone.")], [], "first = ER-01 last")
shot("ER-03", 10, ['Bill', 'Mira', 'Osmund'], "slow orbit around the three, one move.",
     "Osmund sets the sealed plain folder down on the counter. Bill and Mira trade one brief, smiling glance over it.",
     [], [("EFFICIENCY REVIEW", "center", 2.0, 6.0)], "first = ER-02 last")
shot("ER-04", 10, ['Bill', 'Osmund'], "locked medium, no move.",
     "Near a display wall, Bill leans quietly toward Osmund, voice low, sleeves on, one hand resting on the wall.",
     [('Bill', "Who wrote it?"), ('Osmund', "I don't know. It was very thorough.")], [], "first = ER-03 last (Bill/Osmund side)")
shot("ER-05", 10, ['Mira'], "museum-light push-in, one move.",
     "Mira alone at the counter, dry half-smile, peels a small red sticker and presses it onto her black clipboard beside a small blank square.",
     [], [("B", "center", 5.0, 10.0)], "NEW (Mira cast still ref). Act 1 out; then AD POD 1 (#30, #31)")
# ACT 2
shot("ER-06", 10, ['Bill', 'Osmund'], "locked medium, no move.",
     "Bill stands beside a seated Osmund, one sleeved hand on Osmund's shoulder, and dictates calmly while Osmund writes on a blank page.",
     [('Bill', "Praise her bold flexibility. Around timekeeping.")], [], "NEW (Bill + Osmund refs; first shot back from AD POD 1)", act=2)
shot("ER-07", 10, ['Mira', 'Osmund'], "locked medium, mirror framing of ER-06, no move.",
     "Mira stands beside the seated Osmund, one hand on his shoulder in the mirror pose, and dictates sweetly while Osmund writes on a blank page.",
     [('Mira', "Praise his calm. Which some mistake for absence.")], [], "NEW (mirror composition of ER-06)", act=2)
shot("ER-08", 10, ['Osmund'], "slow push-in, one move.",
     "Osmund, sweating, staples two blank pages together and slides them into the same plain folder.",
     [], [], "first = ER-07 last", act=2)
shot("ER-09", 12, ['Bill', 'Mira', 'Tim'], "slow push-in, one move.",
     "Bill and Mira stand side by side, both smiling, eyes forward, saying nothing; Bill fully sleeved. Behind them, softly out of focus, Tim hovers with his cyan optic glowing.",
     [], [], "NEW (two-shot)", act=2)
shot("ER-10", 10, ['Bill', 'Mira', 'Tim'], "locked medium, no move.",
     "Tim hovers at shoulder height in sharp focus, his cyan optic pulsing slowly; Bill and Mira are soft out-of-focus shapes behind, Bill sleeved. Nobody looks at Tim.",
     [], [], "first = ER-09 last. Act 2 out; then AD POD 2 (#32, #33, #34)", act=2)
# ACT 3
shot("ER-11", 10, ['Osmund'], "slow push-in, one move.",
     "Osmund finally reads the top page of the folder; his face falls slowly.",
     [('Osmund', "Filed unit to unit. Four hundred hours of floor observation.")], [("FILED BY: TIM", "lower_third", 3.0, 9.0)], "NEW (first shot back from AD POD 2)", act=3)
shot("ER-12", 10, ['Bill', 'Mira', 'Tim'], "slow orbit, one move.",
     "Bill and Mira slowly turn together toward Tim, Bill fully sleeved. Tim's cyan optic blinks once and he gives one short chirp.",
     [('Tim', "(one short chirp)")], [], "first = ER-10 last (Tim continuity)", act=3)
shot("ER-13", 10, ['Osmund'], "locked medium, no move.",
     "Osmund stands alone at center floor in the host position, stiff and terrified, hands at his sides.",
     [('Osmund', "Effective immediately?")], [("VERDICT: BOTH HOSTS TO OUTBOUND LOGISTICS. OSMUND: FLOOR HOST.", "lower_third", 1.0, 8.0)], "first = ER-11 last", act=3)
shot("ER-14", 12, ['Bill', 'Mira', 'Tim'], "slow pull-back, one move.",
     "In the rain-lit loading bay, Bill and Mira stand side by side under the dock roof holding plain parcels, not speaking; Bill sleeved, jacket dark with rain at the shoulders. Tim drifts past them into the warm showroom doorway.",
     [], [("EFFICIENCY: IMPROVED.", "center", 8.0, 12.0)], "NEW (ending). Then AD POD 3 / outro (#35, #36)", loc='bay', act=3)
overlays.insert(0, {"text": "THE EFFICIENCY REVIEW", "kind": "caption", "role": "title", "position": "center", "start_s": 0.5, "end_s": 4.0,
                    "style": "title", "blocked": C.overlay_blocked("THE EFFICIENCY REVIEW"), "airable": not C.overlay_blocked("THE EFFICIENCY REVIEW"), "shot_id": "ER-01"})
for s in shots:
    h = C.gen_prompt_requests_text(s['visual_prompt'].replace('no readable text, no signage lettering', '').replace('no readable text', '')); assert not h, (s['id'], h)
    for o in overlays:
        if len(o['text']) > 2: assert o['text'] not in s['visual_prompt'], (s['id'], o['text'])
        else: assert f'"{o["text"]}"' not in s['visual_prompt'] and 'labeled' not in s['visual_prompt'], (s['id'], o['text'])
json.dump({"title": "The Efficiency Review", "show": "Military Boutique after hours", "channel": "4", "lineage": LINEAGE, "home_only": True,
           "brief": "out-of-scope/director/brief-the-efficiency-review-20261027.md", "written": "2026-10-27 CT by Story Bot", "shots": shots},
          open(OUT/'prompts.json', 'w'), indent=1, ensure_ascii=False)
json.dump({"rule": "post-process overlay on a separate copy; never in generation; clean master is the anchor/mutation parent", "overlays": overlays},
          open(OUT/'overlay_specs.json', 'w'), indent=1, ensure_ascii=False)
with open(OUT/'bookkeeping-pending.jsonl', 'w') as f:
    for s in shots:
        f.write(json.dumps({"row_type": "pending_node", "status": "draft_pending_render", "clip_id": f"ch4-er-{s['id'].lower()}",
            "lineage": LINEAGE, "tag": f"{LINEAGE} g1 #TBD", "gen": 1, "parent_global_no": None, "parent_id": None,
            "origin": "original (Director brief 2026-10-27, The Efficiency Review)", "global_no": None,
            "global_no_note": "CNB assigns at render (LINEAGE max is 84; next free would be 85+)", "supersedes": None,
            "comment_prompt_ids": [], "act": s['act'], "duration_s": s['duration_s'], "continues_from": s['continues_from'],
            "overlay_ids": [o['text'] for o in overlays if o['shot_id'] == s['id']], "clean_source": True, "audio_leveled": False,
            "max_paid_tries": 2, "written": "2026-10-27 CT"}) + '\n')
    f.write(json.dumps({"row_type": "ad_pod_plan", "lineage": LINEAGE, "pods": [
        {"after": "ER-05 (Act 1 out)", "ads": [30, 31]}, {"after": "ER-10 (Act 2 out)", "ads": [32, 33, 34]}, {"after": "ER-14 (outro)", "ads": [35, 36]}],
        "ads_untouched": True, "note": "products are not in the story; ads air only as separate pods"}) + '\n')
tot = sum(s['duration_s'] for s in shots); print(len(shots), tot, round(tot*0.087, 2), round(len(shots)*0.53, 2))
