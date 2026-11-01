"""Comment sanitizer. Text is inserted raw (D4); this only removes what may never reach a prompt and applies hard canon.

Order: handles / e-mails / contributor ids -> URLs -> never-words and block list -> bend() and hard limits -> brackets and quotes.
Statuses: KEPT (inserted as is, minus removed identity/URL tokens), BENT (rule-breaking wording bent), HELD (hard limit;
never emitted), DROPPED (never-word, block list, or nothing left)."""
import re

import paths
from adapters.story_engine_bridge import NEVER_WORDS, PROTECTED, bend

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
HANDLE = re.compile(r"(?<![\w.])@\w+")
CONTRIBUTOR_ID = re.compile(r"\bcp-[0-9a-f]{6,}\b", re.I)
URL = re.compile(r"https?://\S+|www\.\S+|(?<![\w@.-])[a-z0-9-]+(\.[a-z0-9-]+)*\.(com|net|org|io|tv|gg|co|me|ly|app|dev|xyz|info|biz|link|us|uk)\b(/\S*)?", re.I)
CAMERA_LOOK = re.compile(r"\b(look|looks|looking|stare|stares|staring|glance|glances|glancing|gaze|gazes|gazing|peer|peers|peering|"
                         r"wink|winks|winking|eyes|faces|facing|turns? to face|breaks? the fourth wall)\b(?! past| aside)[^.;,]{0,30}?"
                         r"\b(camera|lens|viewers?|audience)\b", re.I)
FOURTH_WALL = re.compile(r"\b(break|breaks|breaking|broke|broken) the fourth wall\b", re.I)
BRACKETED = re.compile(r"\[([^\]]*)\]")
QUOTES = re.compile(r"[\"\u201c\u201d]")


def _in_form(verb, ing, s, base, past=None):
    w = verb.split()[0].lower()
    if w.endswith("ing"):
        return ing
    if past and w in ("broke", "broken"):
        return past
    return s if w.endswith("s") else base


def _past_the_lens(m):
    return _in_form(m.group(1), "looking past the lens", "looks past the lens", "look past the lens")


def _in_the_scene(m):
    return _in_form(m.group(1), "staying in the scene", "stays in the scene", "stay in the scene", "stayed in the scene")


EXTRA_BENDS = [(re.compile(r"\b(looks?) (in|into|at) (the )?lens\b", re.I), _past_the_lens),
               (re.compile(r"\b(stares?|glances?|turns?) (in|into|at|to|toward) (the )?(camera|lens)\b", re.I),
                lambda m: _in_form(m.group(1), "glancing aside", "glances aside", "glance aside"))]


def _result(text, status, reasons):
    return {"text": text, "status": status, "reasons": reasons}


def _block_list(cfg):
    words = [w for w in (cfg or paths.config("assembly"))["comment_block_list"] if w.strip()]
    return re.compile(r"\b(" + "|".join(map(re.escape, words)) + r")\b", re.I) if words else None


def _bracket(m):
    label = m.group(1).split(":", 1)[0].strip().lower().replace(" ", "_")
    return " " if label in PROTECTED else f" {m.group(1)} "


def sanitize(text, *, cfg=None):
    reasons = []
    t = text
    for pat, why in ((EMAIL, "e-mail removed"), (HANDLE, "mention removed"), (CONTRIBUTOR_ID, "contributor id removed"),
                     (URL, "url removed")):
        t, n = pat.subn(" ", t)
        if n:
            reasons.append(why)
    if NEVER_WORDS.search(t):
        return _result(None, "DROPPED", reasons + ["never-word"])
    block = _block_list(cfg)
    if block and block.search(t):
        return _result(None, "DROPPED", reasons + ["block list"])
    bent, held = bend(t)
    if held:
        return _result(None, "HELD", reasons + [held])
    for pat, rep in EXTRA_BENDS:
        bent = pat.sub(rep, bent)
    bent = FOURTH_WALL.sub(_in_the_scene, CAMERA_LOOK.sub(_past_the_lens, bent))
    status = "BENT" if bent != t else "KEPT"
    if status == "BENT":
        reasons.append("bent")
    t = bent
    t2 = BRACKETED.sub(_bracket, t).replace("[", " ").replace("]", " ")
    if t2 != t:
        reasons.append("brackets stripped")
    t3 = QUOTES.sub("", t2)
    if t3 != t2:
        reasons.append("quotes stripped")
    t = re.sub(r"\s+", " ", t3).strip(" ,;:")
    if not t:
        return _result(None, "DROPPED", reasons + ["empty after sanitize"])
    return _result(t, status, reasons)
