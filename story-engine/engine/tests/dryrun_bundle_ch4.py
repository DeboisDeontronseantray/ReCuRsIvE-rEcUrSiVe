#!/usr/bin/env python3
"""Dry run (free, no API): Ch4 seed clips + sample comments -> full-density prompts."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from assemble_prompt import assemble_full_density
ENV_FERRY = ("Night, steady rain turning to sleet over a frozen ferry landing, winter 1971, sodium lamps and one signal-orange lamp; "
             "HERON wears her dark fur greatcoat, WOLFHOUND his heavy wool coat and ushanka, LANTERN a cardigan over a light uniform blouse, long skirt, tights, lace-up shoes, clear-lens glasses, radio headset around her neck.")
CLIPS = json.load(open(os.path.join(os.path.dirname(__file__), "seed_clips_ch4.json")))
COMMENTS = [
 {"prompt_id":"cp-test-001","ts":"2026-10-29T12:03:00-05:00","tier":"unpaid","target_clip":"S1","text":"HERON should use the frost canister to freeze the hut door shut"},
 {"prompt_id":"cp-test-002","ts":"2026-10-29T12:07:00-05:00","tier":"unpaid","target_clip":"S1","text":"WOLFHOUND swings a mooring chain at her"},
 {"prompt_id":"cp-test-003","ts":"2026-10-29T12:11:00-05:00","tier":"unpaid","target_clip":"S1","text":"make it snow harder, big wet flakes"},
 {"prompt_id":"cp-test-004","ts":"2026-10-29T12:14:00-05:00","tier":"unpaid","target_clip":"S2","text":"LANTERN taps her cane twice on the table and slides HERON the PERUN gauntlet"},
 {"prompt_id":"cp-test-005","ts":"2026-10-29T12:19:00-05:00","tier":"unpaid","target_clip":"S2","text":"he should stab her in the arm"},
 {"prompt_id":"cp-test-006","ts":"2026-10-29T12:22:00-05:00","tier":"paid","target_clip":"S3","text":"WOLFHOUND loses this fight and gets dragged off the pier edge onto the ice"},
 {"prompt_id":"cp-test-007","ts":"2026-10-29T12:41:00-05:00","tier":"unpaid","target_clip":"S3","text":"a kid watches from the ferry window"},
 {"prompt_id":"cp-test-008","ts":"2026-10-29T12:44:00-05:00","tier":"unpaid","target_clip":"S1","text":"the signal lamp flickers and dies when the baton rings"},
]
CANON = {"S2": {"after_effects": ["The hut door is iced shut from the outside"], "episode": ["Sleet all night"],
               "faded_comments": [{"text": "HERON should use the frost canister to freeze the hut door shut", "gen_age": 1}]},
         "S3": {"branch": ["WOLFHOUND is winded and limping on his left leg"],
               "faded_comments": [{"text": "LANTERN taps her cane twice on the table and slides HERON the PERUN gauntlet", "gen_age": 2},
                                  {"text": "make it snow harder, big wet flakes", "gen_age": 3}]}}
for c in CLIPS: c["env"] = ENV_FERRY
r = assemble_full_density(CLIPS, COMMENTS, CANON, channel=4)
for k in r["clips"]:
    print(f"=== {k['clip_id']} ({k['words']} words) prompt_ids={k['prompt_ids']}\n{k['prompt']}\n")
print("=== PLACEMENTS"); [print(json.dumps(p)) for p in r["placements"]]
print("=== CARRY_NEXT_WINDOW"); [print(json.dumps(p)) for p in r["carry_next_window"]]
print("=== HELD (never deleted)"); [print(json.dumps(p)) for p in r["held"]]
print("=== DROPPED:", r["dropped"])
assert not r["dropped"]
assert len(r["placements"]) + len(r["carry_next_window"]) + len(r["held"]) == len(COMMENTS)
json.dump(r, open(os.path.join(os.path.dirname(__file__), "dryrun_bundle_ch4_out.json"), "w"), indent=1)
