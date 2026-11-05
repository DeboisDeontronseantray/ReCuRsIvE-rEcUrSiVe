#!/usr/bin/env python3
"""Resolve a screen-insert ref (#58, 58, or 4.1:2) to its CLEAN master. Never returns a tagged copy.
Usage: resolve_embed.py <ref> [--host-global N --host-lineage 4.13 --host-gen 1]
With --host-*, also prints the LINEAGE row (origin: embed) for CNB to append."""
import json, os, sys, argparse
LINEAGE = "out-of-scope/fakenews/channel-ready/thunder-trundle/4_1_Military-Boutique/LINEAGE.jsonl"
BAD = ("outbox", "/cut/", "_tag", "tagged", "lowerthird", "readtag", "/held/")

def rows():
    with open(LINEAGE) as f:
        for line in f:
            line = line.strip()
            if line:
                try: yield json.loads(line)
                except json.JSONDecodeError: pass

def find(ref):
    ref = str(ref).strip().lstrip("#")
    if ":" in ref:
        lin, gen = ref.split(":"); gen = int(gen)
        m = [r for r in rows() if r.get("lineage") == lin and r.get("gen") == gen and "global_no" in r]
    else:
        n = int(ref); m = [r for r in rows() if r.get("global_no") == n]
    if not m: sys.exit(f"ERROR: no LINEAGE row for {ref}")
    return m

def clean_path(r):
    for k in ("clean_source", "clean_master", "file" if r.get("role") == "clean_master" else None):
        p = k and r.get(k)
        if p and os.path.exists(p) and not any(b in p for b in BAD):
            return p
    return None

def main():
    a = argparse.ArgumentParser(); a.add_argument("ref")
    a.add_argument("--host-global", type=int); a.add_argument("--host-lineage"); a.add_argument("--host-gen", type=int)
    o = a.parse_args()
    for r in reversed(find(o.ref)):          # newest row first
        p = clean_path(r)
        if p:
            out = {"ref": o.ref, "global_no": r.get("global_no"), "tag": r.get("tag"), "clean_master": p}
            if o.host_global:
                out["lineage_row"] = {"row_type": "embed", "origin": "embed", "lineage": o.host_lineage,
                    "gen": o.host_gen, "parent_global_no": o.host_global, "embeds": [r.get("global_no")],
                    "embed_source": p, "writer": "CNB", "trundle_air_yes": False}
            print(json.dumps(out, indent=1)); return
    sys.exit(f"ERROR: {o.ref} has no clean untagged master on disk; refusing tagged copies")

if __name__ == "__main__": main()
