import json, sys
sys.path.insert(0, "/workspace/streaming/story-engine/live"); import intake, checker
T = ["Osmund recounts every ration tin in the supply bay while Tim floats beside him keeping score with chirps",
 "Mira re-stickers the whole depot shelf by fog color while Bill watches with his arms crossed",
 "Bill tries to fold the Graphite Cloak into a perfect square the way Osmund does and gets close",
 "Tim scouts the fog outside the porthole and comes back with a single brass tag clipped to his ring",
 "Osmund and Mira test the Field Glass from the hatch and argue about which shade of grey the fog is today",
 "Bill does his morning stretch routine in the command hut while Mira reads the inventory list beside him",
 "The crew sets up the Lightning Lamp in the mess hall during a storm and eats dinner by its flicker",
 "Osmund loses his helmet again and Tim finds it by warmth in the bunk room",
 "Mira teaches Tim to sort colored stickers onto her clipboard one dot at a time",
 "Bill inspects the supply bay with a white glove and finds exactly one speck of dust"]
clips = []
for i, t in enumerate(T, 1):
    rec = {"id": f"starter-{i:02d}", "handle": "@starter", "text": t, "received_at": "2026-10-27T17:35:00-05:00", "source": "storybot-starter"}
    assert not intake.moderate(t), (t, intake.moderate(t))
    shot = intake.to_clip(intake.inject(intake.wrap(rec), rec["id"]))
    shot["id"] = f"LIVE-STARTER-{i:02d}"; shot["lineage"] = {"lineage": "4.3", "origin": "first_render", "parent": None}
    shot["status"] = "STARTER PROMPT - auto-approve on; render only via CNB with filters; not live"
    clips.append(shot)
json.dump({"title": "Ch 4 lineage 4.3 commenter-style starters", "written": "2026-10-27 CT Story Bot", "shots": clips},
          open("/workspace/streaming/story-engine/data/live/starters/comment-starters-20261027.json", "x"), indent=1, ensure_ascii=False)
