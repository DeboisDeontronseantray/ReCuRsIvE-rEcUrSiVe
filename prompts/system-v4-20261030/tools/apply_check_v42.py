#!/usr/bin/env python3
"""Gate v4.2 = gate v4.1 + R-REFDESC (trundle t371u, Oct 30 8:01 PM CT):
"Why are you still describing characteristics of the image when the image is already in new prompts."
FAIL when an item that has an attached image (<IMAGE_n>) also gets restated visual characteristics.
Allowed next to a tag: a short label of WHAT the image is ("full body", "face", "as he is now", "is the teal tape measure now around his neck").
Allowed: text for things NOT shown in the image (a new costume piece, a change this clip), written as a change ("now in ...", "now around his neck").
Scope: OUR built prompts only. Viewer comments are never gated on images (comment text never needs an image; the builder attaches channel refs itself)."""
import re, apply_check_v41 as G41
CAM=G41.CAM
def _cimg_on():
    import json as _j,os as _o
    try: return bool(_j.load(open(_o.path.join(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))),"config","commenter_images.json"))).get("enabled"))
    except Exception: return False
VIS=r"(hair|bob|braid|curls|mustache|beard|coat|jacket|waistcoat|blazer|suit|tie|shirt|dress|apron|gloves|glove|scarf|headscarf|hat|cap|helmet|visor|armor|armour|uniform|tracksuit|cardigan|turtleneck|vest|hoodie|sweater|parka|boots|cane|key ring|tall|thin|short|glasses|sunglasses|red|blue|grey|gray|black|white|brown|green|teal|maroon|gold|purple|orange|yellow|plum|silver|tan|auburn|blonde|chrome|brass|staircase|chandeliers?|marble|carpet(ed)?|desk|rails?)"
def refdesc(p):
    hits=[]
    # (<IMAGE_n>; keys) or (<IMAGE_n>, keys) - keys after the tag inside the same parenthesis
    for m in re.finditer(r"\(([^()]*<IMAGE_\d+>[^()]*)\)",p):
        for seg in m.group(1).split(";"):
            seg=seg.strip()
            if not seg.startswith("<IMAGE_"): 
                if re.search(VIS,seg,re.I): hits.append(seg)
                continue
            for part in re.split(r",\s*",seg)[1:]:
                if not part.startswith("<IMAGE_") and re.search(VIS,part,re.I): hits.append(part)
    # NAME (<IMAGE_n>): keys
    for m in re.finditer(r"\(<IMAGE_\d+>\)\s*:\s*([^\]]+)",p):
        if re.search(VIS,m.group(1),re.I): hits.append(m.group(1))
    # as in <IMAGE_n>: set details / as <IMAGE_n>, set details
    for m in re.finditer(r"as (?:in |seen in )?<IMAGE_\d+>\s*[:,]\s*([^\]]+)",p):
        if re.search(VIS,m.group(1),re.I): hits.append(m.group(1))
    return hits
def check(p,args=None,spec=None,side=None):
    r=G41.check(p,args,spec,side); spec=spec or {}
    h=refdesc(p)
    # named cast that has an attached image (spec['ref_for']) but is still described in text
    for name in (spec.get("ref_for") or {}):
        m=re.search(re.escape(name)+r"\s*(?::|\((?!<IMAGE_))\s*([^\])]+)",p)
        if m and re.search(VIS,m.group(1),re.I): h.append(f"{name}: {m.group(1)}")
    # contributor accounts: data that follows the image/clip, never in prompt (trundle 10:48 PM CT Oct 30)
    hs=[c for c in (spec.get("contributors") or []) if c and re.search(r"(?<![\w@])@?"+re.escape(str(c).lstrip("@"))+r"\b",p,re.I)]
    hs+=re.findall(r"(?<![\w.])@[A-Za-z0-9_]{2,15}\b",p)
    r["R-NOHANDLES no contributor handles in prompt (10:48 PM)"]=("FAIL" if hs else "PASS",sorted(set(hs)))
    r["R-NOCOMMENTERIMG commenter images NOT YET (10:48 PM)"]=("FAIL" if (spec.get("commenter_refs") or any(str(x).startswith("commenter") for x in (spec.get("ref_sources") or []))) and not _cimg_on() else "PASS",)
    r["R-BRANDS parody brands, no names on screen (CR L34)"]=("PASS" if "no real brands or personal names on screen" in p else "FAIL",)
    r["R-REFDESC no restated looks when an image is attached (t371u)"]=("FAIL" if h else "PASS",h)
    return r
