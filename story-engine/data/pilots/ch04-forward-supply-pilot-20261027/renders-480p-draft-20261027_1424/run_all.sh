set -u
LITE=" FS-P01-C01 FS-P01-C07 FS-P01-C10 FS-P01-C11 FS-P01-C12 FS-P01-C17 FS-P01-C20 FS-P01-C21 "
for n in 01 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21; do
 c=FS-P01-C$n; m=grok-imagine-video-1.5; [[ "$LITE" == *" $c "* ]] && m=grok-imagine-video-1.5-lite
 tot=$(python3 -c "import json;print(sum(json.loads(l)['cost_usd'] for l in open('log.jsonl')))")
 python3 -c "import sys;sys.exit(0 if $tot<15 else 1)" || { echo "HARD STOP total $tot"; break; }
 for a in 1 2; do python3 render_clip_v2.py $c $m && [ -f ${c}_480p_${m}_parody.mp4 ] && break; echo "attempt $a failed $c"; done
done; echo ALLDONE
