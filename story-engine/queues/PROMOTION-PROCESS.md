# Promotion process (pointer)
The single process doc is **/workspace/shared/streaming/CLIP-PROMOTION-PROCESS-20261027.md**. Follow it. This file only lists Story Bot's parts:
1. **Slot reserve:** pick a clean-break slot S (between clip A and clip B) from QUEUE-PLAN-<date>.json. Never mid-group. Order source: QUEUE-LOAD-<date>.json when it exists.
2. **Prompt from frames:** start ref = A's last frame, end frame = B's first frame, both from clean untagged masters (slot in_anchor/out_anchor). Prompt describes the bridging motion; camera, observational (no eye contact) and audio rules; must pass live/checker.py.
3. **Seam check:** new clip's first frame vs A-last and last frame vs B-first (color/brightness diff). Too far = back for re-render or move to another break.
4. **Queue diff:** new QUEUE-PLAN version with S filled (old versions kept, new first/last frames added, neighbors updated); hand Device Engineer + Smart Home Lead "insert X at S, vN -> vN+1". ErsatzTV loads only with trundle's yes.
