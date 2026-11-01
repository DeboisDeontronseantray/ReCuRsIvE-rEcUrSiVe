"""Slot split, diff and gate report for assembled prompts (v42 fixed slot order)."""
import json
import re

SLOTS = ("look", "setting", "cast", "thread", "continue", "camera", "eyelines", "beats", "ending", "rules")
ALLOWED_CHANGED_SLOTS = {"continue", "beats"}
LEAD_BRACKET = re.compile(r"\s*(\[([^\]]*)\])")
CONTINUE = re.compile(r"Continue from <IMAGE_0>[^.]*\.\s*")
ENDING = re.compile(r"\s*(Motion carries on through the last half second\.|The last 0\.4 s eases into the planned end image\.)$")
FIRST_BEAT = re.compile(r"At [\d.]+ s,")
EYELINES = re.compile(r"Eyelines:|Everyone looks at each other")
BEAT_SPLIT = re.compile(r"(?=At [\d.]+ s,)")


def slot_split(prompt):
    s = dict.fromkeys(SLOTS, "")
    rules_at = prompt.rfind("[Adults")
    s["rules"] = prompt[rules_at:].strip()
    head, i, cast = prompt[:rules_at], 0, []
    while m := LEAD_BRACKET.match(head, i):
        label, i = m.group(2), m.end()
        key = next((k for k, p in (("look", "Look:"), ("setting", "Setting:"), ("thread", "Thread:")) if label.startswith(p)), None)
        if key:
            s[key] = m.group(1)
        else:
            cast.append(m.group(1))
    s["cast"] = " ".join(cast)
    d = head[i:].strip()
    if m := CONTINUE.match(d):
        s["continue"], d = m.group(0).strip(), d[m.end():]
    if m := ENDING.search(d):
        s["ending"], d = m.group(1), d[:m.start()]
    if m := FIRST_BEAT.search(d):
        s["beats"], d = d[m.start():].strip(), d[:m.start()]
    if m := EYELINES.search(d):
        s["eyelines"], d = d[m.start():].strip(), d[:m.start()]
    s["camera"] = d.strip()
    return s


def beats_of(prompt):
    return [b.strip() for b in BEAT_SPLIT.split(slot_split(prompt)["beats"]) if b.strip()]


def diff_slots(old_prompt, new_prompt):
    a, b = slot_split(old_prompt), slot_split(new_prompt)
    return {k: {"old": a[k], "new": b[k]} for k in SLOTS if a[k] != b[k]}


def _dict_diff(old, new):
    return {k: {"old": old.get(k), "new": new.get(k)} for k in sorted(set(old) | set(new)) if old.get(k) != new.get(k)}


def diff(current, assembled, sources, locked_thread=None):
    """current/assembled: {"args", "sidecar"} from the v42 builder. sources: placement sources (beat t, requester, id).
    locked_thread: the D7 hard-constraint thread text; the thread slot may change only to carry it."""
    slots = diff_slots(current["args"]["prompt"], assembled["args"]["prompt"])
    allowed = set(ALLOWED_CHANGED_SLOTS)
    if locked_thread and locked_thread in slots.get("thread", {}).get("new", ""):
        allowed.add("thread")
    args = _dict_diff({k: v for k, v in current["args"].items() if k != "prompt"},
                      {k: v for k, v in assembled["args"].items() if k != "prompt"})
    side = _dict_diff(current["sidecar"], assembled["sidecar"])
    new_beats = beats_of(assembled["args"]["prompt"])
    attributed = [{"beat": b, **({"requester": s["requester"], "source": s["id"]} if s else {"requester": "base", "source": "base spec"})}
                  for b, s in zip(new_beats, list(sources) + [None] * (len(new_beats) - len(sources)))]
    return {"changed_slots": sorted(slots), "disallowed_slots": sorted(set(slots) - allowed),
            "identical_prompt": current["args"]["prompt"] == assembled["args"]["prompt"],
            "slots": slots, "args": args, "sidecar": side,
            "old_beats": beats_of(current["args"]["prompt"]), "new_beats": attributed}


def gate_summary(clip_id, rep):
    return {"clip_id": clip_id, "fails": sorted(k for k, v in rep.items() if v[0] == "FAIL"),
            "warns": sorted(k for k, v in rep.items() if v[0] == "WARN"), "report": {k: list(v) for k, v in rep.items()}}


def diff_markdown(base_id, clip_id, d, gate):
    out = [f"# DIFF {clip_id} vs current v42 build of {base_id}", "",
           f"- Changed slots: {', '.join(d['changed_slots']) or 'none'}",
           f"- Slots outside beats/continue that changed: {', '.join(d['disallowed_slots']) or 'none'}",
           f"- Prompt identical: {d['identical_prompt']}",
           f"- Gate v44 FAIL: {', '.join(gate['fails']) or 'none'}; WARN: {', '.join(gate['warns']) or 'none'}", ""]
    out += ["## Beats", "", f"### {base_id} (current builder)", ""] + [f"- {b}" for b in d["old_beats"]] + [""]
    out += [f"### {clip_id} (assembled)", ""] + [f"- [{b['requester']}: {b['source']}] {b['beat']}" for b in d["new_beats"]] + [""]
    out += ["## Other slots", ""]
    others = {k: v for k, v in d["slots"].items() if k != "beats"}
    for k, v in others.items():
        out += [f"### {k}", "", f"- old: `{v['old']}`", f"- new: `{v['new']}`", ""]
    if not others:
        out += ["No other slot text changed.", ""]
    out += ["## Args (excluding prompt)", ""] + [f"- `{k}`: `{json.dumps(v['old'])}` -> `{json.dumps(v['new'])}`" for k, v in d["args"].items()] + [""]
    out += ["## Sidecar", ""] + [f"- `{k}`: `{json.dumps(v['old'])}` -> `{json.dumps(v['new'])}`" for k, v in d["sidecar"].items()] + [""]
    return "\n".join(out)
