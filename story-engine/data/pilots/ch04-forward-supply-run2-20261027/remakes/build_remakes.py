import json, re, sys, hashlib
from pathlib import Path
sys.path.insert(0, "/workspace/streaming/story-engine/live")
import checker
P = Path(__file__).resolve().parents[1]
src = json.load(open(P/"clip-prompts.json"))
R = P/"run2/renders-480p-20261027_1547"
RULE = ("OBSERVATIONAL RULE: characters never look at or address the camera; candid fly-on-the-wall framing; "
        "eyelines on each other, their task, or off-frame; no direct-to-camera dialogue.")
NEG_ADD = ["no eye contact with the lens", "no looking into the camera", "no addressing the viewer", "no frontal centered stare",
           "no presenter pose", "no burned-in text, tags, badges or overlays"]
# shot -> (new camera, eyeline/blocking direction)
FIX = {
 "S1A": ("wide locked, high corner angle from behind the coffee urn", "Everyone is busy with breakfast and each other; Osmund faces his pack, Bill reads his folder in profile, Mira looks down at her clipboard, Tim drifts toward the urn."),
 "S1B": ("medium over Osmund's shoulder, three-quarter rear", "Osmund's eyes stay on the tins in his hands; he never lifts his head past the table edge."),
 "S1D": ("medium side angle, profile two-shot", "Bill and Tim in profile facing each other; Bill's eyes on the clip and on Tim's optic, then on the porthole as he gives the order."),
 "S1E": ("medium side push-in on Bill from screen-right, three-quarter profile", "Bill seated in profile at his desk, gaze across the room on Osmund patting his pockets; Tim behind him faces Osmund too."),
 "S2A": ("wide dolly along shelves, side angle", "Osmund in profile, eyes down into the pack cavity; Mira behind him facing the shelves, eyes on her tags; when they talk they glance at each other."),
 "S2B": ("close on hands, over Osmund's shoulder", "Osmund's face mostly turned away, eyes on the helmet liner."),
 "S2C": ("medium on Mira from a low side angle, three-quarter profile", "Mira tilts her head up toward the HUD strip above the shelves (off-axis, screen-left), then down to her clipboard; she answers Osmund by looking toward him off-frame right."),
 "S3C": ("close on Osmund in three-quarter profile", "Osmund's eyes on the foggy ridge off-frame left where Tim's chirps come from; he points that way, never toward the lens."),
 "S4C": ("medium two-shot from inside the bunk room, side angle", "Bill in profile at the hatch, eyes down on Osmund lying flat; Osmund's eyes under the bunk."),
 "S5A": ("wide from the side of the desk, three-quarter angle", "The crew faces the desk and each other; Bill stares down at the blank rectangle on the desk, then at his own flexing fingers."),
 "S5B": ("slow push-in on Bill from a side three-quarter angle", "Bill's rage is aimed at the empty desk and then straight up at the ceiling; the eruption shout goes upward, his face in profile."),
 "S5C": ("medium side two-shot across the desk", "Tim floats in from screen-left; Bill in profile watches only Tim and the envelope; his quiet line goes to Tim."),
 "S5D": ("three-shot from a side angle at desk height", "Bill in profile squares the envelope, eyes on his hands; Mira and Osmund look at Bill and at each other as they exhale."),
 "S6E": ("close on Osmund over Mira's shoulder, three-quarter", "Osmund's eyes on the box in Mira's hands, then on Mira as he nods."),
 "S7A": ("wide from the end of the table, side angle", "The crew faces each other along the table; eyes on the lamp, on Osmund's hands and on each other; Bill turns toward Osmund, not the room's far wall."),
}
ORDER = ["S1D","S1E","S2C","S3C","S5B","S5C","S5D","S6E","S1B","S2A","S4C","S5A","S2B","S7A","S1A"]
CONF = {**{k:"high" for k in ORDER[:8]}, **{k:"medium" for k in ORDER[8:12]}, "S2B":"low","S7A":"low","S1A":"earlier remake list"}
by = {s["id"]: s for s in src["shots"]}
shots, ref_log = [], []
for sid in ORDER:
    s = json.loads(json.dumps(by[sid])); cam, eye = FIX[sid]
    clean = []
    for p in s.get("reference_images", []):
        if checker.is_tainted(p) or checker.watchlist_hit(p): ref_log.append({"shot": sid, "dropped": p}); continue
        r = checker.resolve_clean(p); clean.append(r)
    vp = re.sub(r"\s*CAMERA:.*?one move only\.", "", s["visual_prompt"])
    vp = vp.replace(" OBSERVATIONAL RULE:", " OLDRULE:") if "OBSERVATIONAL RULE" in vp else vp
    vp += f" CAMERA: {cam}, one move only; the camera is an unnoticed observer. EYELINES: {eye} {RULE}"
    rend = next(R.glob(f"{sid}_480p_*_parody.mp4"), None)
    s.update({"id": f"{sid}-R1", "remake_of": sid, "remake_reason": f"camera rule flag ({CONF[sid]}), REVIEW-run2.md 16:58 CT",
        "camera": cam, "action": s["action"] + " " + eye, "visual_prompt": vp, "camera_rule": RULE,
        "negative_prompt": s["negative_prompt"] + [n for n in NEG_ADD if n not in s["negative_prompt"]],
        "reference_images": clean, "end_frame_source": None,
        "lineage": {"lineage": "4.1", "origin": "remake", "parent_file": str(rend) if rend else None,
                    "parent_used_as_input": False, "note": "Text prompt remake; parent render is NOT fed as ref or end frame. CNB assigns tag/global_no in LINEAGE.jsonl."},
        "status": "PROMPT ONLY - trundle approved remake prompts 17:25 CT; render needs CNB + spend check; home-only"})
    shots.append(s)
out = {"title": "Forward Supply Run 2 camera-rule remakes", "written": "2026-10-27 CT by Story Bot", "source": str(P/"clip-prompts.json"),
       "channel": "Ch 4 Military Boutique", "show": "Forward Supply", "home_only": True, "ref_drops": ref_log, "shots": shots}
dst = Path("/workspace/streaming/story-engine/data/pilots/ch04-forward-supply-run2-20261027/run2-remakes-20261027.json")
assert not dst.exists(), "exists; back up first"
dst.write_text(json.dumps(out, indent=1, ensure_ascii=False)); print(dst, len(shots), ref_log)
