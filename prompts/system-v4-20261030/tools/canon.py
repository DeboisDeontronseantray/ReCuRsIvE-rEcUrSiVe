#!/usr/bin/env python3
"""Canon layer (Nov 2 2026): maps superseded source names/looks to show-bible canon before any prompt is built.
Table: config/canon_aliases.json (regex pairs, applied in order, per channel). Used by regen_pending_v4 (and so every regen_v4x)."""
import json,os,re
H=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE=json.load(open(f"{H}/config/canon_aliases.json"))["channels"]
def text(s,channel):
    if not isinstance(s,str): return s
    for old,new in TABLE.get(channel,[]): s=re.sub(old,new,s)
    return s
def deep(x,channel):
    if isinstance(x,str): return text(x,channel)
    if isinstance(x,list): return [deep(v,channel) for v in x]
    if isinstance(x,dict): return {text(k,channel):deep(v,channel) for k,v in x.items()}
    return x
