# Builds clip-prompts-v2-DRAFT.json/.md from storyboard-v1-DRAFT.md. Text only; no API calls.
import json, importlib.util
spec=importlib.util.spec_from_file_location("g","gen.py"); src=open("gen.py").read()
ns={}; exec(src.split("C=[]")[0],ns)   # reuse locked REFS, looks, NEG only
REFS,NEG=ns["REFS"],ns["NEG"]; LOOK={k:ns[k] for k in ("BILL","MIRA","TIM","OSM")}
NAME={"BILL":"Commander Bill D'bears","MIRA":"Lt. Mira S'mirin'","TIM":"Tim","OSM":"Osmund"}
STYLE="Photoreal grounded near-future remote forward outpost, lived-in steel and canvas interiors, warm practical lights against cold grey fog outside, late-90s broadcast polish, 4:3-safe center framing, no unintended text, no logos, no watermarks."
LOC={"MESS":"Small steel mess hall, one long table, fogged window screen-left, warm overhead light",
"HUT":"Cramped command hut, metal desk with a sealed blank envelope, map board with blank grid",
"BAY":"Outpost supply bay, steel shelving with packs and a frosted Sky Diffuser panel on the screen-right shelf, amber safety lights",
"BUNK":"Windowless bunk room, four bunks, keepsake shelf, plain ceiling",
"HATCH":"Outer hatch opening onto thick grey fog that never lifts, wind"}
S=[];BR=[]
def s(id,scene,loc,cast,d,cam,action,prev,match,lines,prod,lf,model=None):
    model=model or ("grok-imagine-video-1.5" if cast else "grok-imagine-video-1.5-lite")
    refs=[p for k in cast for p in REFS[k]] if model.endswith("1.5") else []
    S.append(dict(id=id,scene=scene,duration_s=d,model=model,camera=cam,location=LOC[loc],cast=[NAME[k] for k in cast],
      continues_from=prev,match=match,last_frame=lf,product_use=prod,
      visual_prompt=f"{STYLE} {' '.join(LOOK[k]+'.' for k in cast)} Setting: {LOC[loc]}. Continuing from: {prev} Action: {action} Camera: {cam}, one move. Cut match: {match}. Mood: grounded, warm, quietly funny, never slapstick.",
      dialogue=[dict(speaker=a,line=b) for a,b in lines],reference_images=refs,negative_prompt=NEG,status="DRAFT-not-sent"))
s("S1A","S1 Mess hall","MESS",["MIRA","TIM"],8,"wide locked","Mira slides a small sealed ration tin across the table screen-right toward Tim hovering at the far end.","Scene start: fade from black on the mess hall.","action: Mira's sliding hand exits screen-right",[("Lt. Mira S'mirin'","Breakfast. And a question.")],"StrataClip Ration Tin (slid to Tim)","Tin mid-slide, Tim's optic turning toward it.")
s("S1B","S1 Mess hall","MESS",["TIM"],8,"medium on Tim","The tin arrives and clips onto Tim's ring with a soft click; Tim chirps, then his optic turns to the fogged window screen-left.","S1A last frame: tin sliding screen-right toward Tim.","action match on tin arriving; eyeline exits screen-left to window",[("Tim","(chirp)")],"StrataClip Ration Tin clips to Tim's ring (spec: clips to any strap)","Tim's optic aimed at window screen-left.")
s("S1C","S1 Mess hall","MESS",["MIRA","TIM"],8,"over-the-shoulder of Tim toward window","Grey fog fills the window; Mira's reflection in the glass watches Tim, understanding.","S1B last frame: Tim looks screen-left at window.","eyeline: we see what Tim sees; Mira reflected",[("Lt. Mira S'mirin'","A sunrise. Got it.")],None,"Fog window, Mira's reflection, hold.")
s("S2A","S2 Command hut","HUT",["BILL","MIRA"],8,"wide locked","Mira enters from screen-left; Bill at desk screen-right, a matte helmet beside the envelope.","Cut from S1C: Mira turning away from the window (scene change on her exit).","action: Mira's entrance continues her exit from S1C",[("Lt. Mira S'mirin'","Commander. I need the Sky Diffuser. For a project.")],"Quietline Helmet on desk (urgent order)","Bill's hand reaching toward the envelope.")
s("S2B","S2 Command hut","HUT",["BILL"],7,"close on desk","Bill slides the envelope aside, lifts the helmet, presses the liner; soft chirp. His fingers drum; a small forehead vein.","S2A last frame: Bill's hand reaching toward the envelope.","action match on the reach",[("Commander Bill D'bears","The helmet ships today. Everything else waits.")],"Quietline Helmet hush liner seats with a chirp (per spec)","Drumming fingers, envelope pushed to desk edge.")
s("S2C","S2 Command hut","HUT",["MIRA"],7,"medium on Mira","Mira's eyes drop to the envelope at the desk edge, then back to Bill.","S2B last frame: envelope at desk edge.","eyeline down to envelope",[("Lt. Mira S'mirin'","You still haven't opened that.")],None,"Mira holding Bill's gaze.")
s("S3A","S3 Supply bay","BAY",["OSM","MIRA"],8,"medium push-in","Osmund unzips a big insulated thermal ration pack; pull back reveals a molded cavity inside.","Scene start: Osmund already mid-unzip as Mira arrives.","action: zipper pull leads the cut",[("Osmund","Is this the priority brief?")],"Thermal Ration Pack (wrong pack, helmet cavity)","Open pack, cavity visible, Mira holding the helmet.")
s("S3B","S3 Supply bay","BAY",["MIRA","OSM"],7,"close on pack","Mira lowers the helmet into the cavity; it seats perfectly.","S3A last frame: Mira holding the helmet over the open pack.","action match on downward motion",[("Osmund","...It fits."),("Lt. Mira S'mirin'","It fits.")],"Thermal Ration Pack holds the Quietline Helmet exactly","Helmet seated; Mira's hand lifting away.")
s("S3C","S3 Supply bay","BAY",["MIRA"],7,"medium on Mira","Mira's eyes go to the frosted Sky Diffuser panel on the shelf screen-right; a second slot in the pack is exactly its size.","S3B last frame: Mira's hand lifting from the pack.","eyeline screen-right to the panel",[("Lt. Mira S'mirin'","Oh no.")],"Sky Diffuser on shelf (spec: paints slow sky color)","Mira looking screen-right at the panel. END SEGMENT 1.")
BR.append("AD BREAK 1 after S3C (clean break between segments)")
s("S4A","S4 Bunk room","BUNK",["TIM","OSM"],8,"wide locked","Tim drifts toward Osmund's keepsake shelf screen-right.","Scene start after ad break.","action: Tim's drift exits screen-right",[("Osmund","Careful, that's my... thing.")],"Valuables Motion Guard (on Osmund's keepsake box)","Tim near the box.")
s("S4B","S4 Bunk room","BUNK",["TIM"],7,"medium","Small fish-frogs croak in formation around Tim; a calm guard-dog detail herds him back two steps. Nobody touched, nobody hurt.","S4A last frame: Tim near the keepsake box.","action match on Tim's drift being reversed",[("Tim","(chirp chirp chirp - laughing rhythm)")],"Valuables Motion Guard herds the unauthorized person back (per spec)","Tim two steps back, frogs settling.")
s("S4C","S4 Bunk room","BUNK",["OSM","TIM"],7,"two-shot","Osmund kneels, apologises; both look down at the croaking frogs.","S4B last frame: frogs settling at Tim's base.","shared eyeline down to frogs",[("Osmund","They like you. That's new.")],None,"Both looking down; warm.")
s("S5A","S5 Command hut","HUT",["BILL","MIRA","OSM","TIM"],10,"wide four-shot","Mira steps forward from the group; the loaded pack sits on the desk, Sky Diffuser beside it.","Cut from S4C: Osmund rising (scene change on his rise).","action: Mira's step forward",[("Commander Bill D'bears","The route needs that panel as a fog beacon. Load it."),("Lt. Mira S'mirin'","It's for Tim. It's his birthday tomorrow.")],"Sky Diffuser as fog beacon (story use)","Mira forward, Bill seated.")
s("S5B","S5 Command hut","HUT",["BILL"],8,"medium on Bill","Bill rises slowly, stretches his neck, forehead vein bulging, fingers flexing; he holds it in.","S5A last frame: Mira steps forward, Bill seated.","action: Bill rising continues from his seat",[],None,"Bill standing, hand moving to envelope.")
s("S5C","S5 Command hut","HUT",["BILL","MIRA","OSM","TIM"],8,"close then rack to group","Bill's hand closes on the envelope; everyone's eyes go to it.","S5B last frame: hand moving to envelope.","action match on the grip; shared eyeline",[],None,"Bill holding envelope.")
s("S6A","S6 Hatch","HATCH",["BILL","TIM"],8,"medium at hatch","Bill opens the envelope at the open hatch, fog rolling in.","Cut from S5C: envelope in Bill's hand (match on the envelope).","match on envelope",[],None,"Card sliding out.")
s("S6B","S6 Hatch","HATCH",[],8,"insert close","A plain blank card in a large hand, fog behind; a single word to be added in post.","S6A last frame: card sliding out.","action match on card",[],None,"Card held; text added in post via on_screen_text registry ('Tomorrow').")
s("S6C","S6 Hatch","HATCH",["BILL","TIM"],8,"two-shot","Bill lowers the helmet gently over Tim's dome; both look out into the fog.","S6B last frame: card lowering out of frame.","action match on lowering hand; shared eyeline to fog",[("Commander Bill D'bears","Tomorrow can wait.")],"Quietline Helmet lets them hear each other in the wind (hush liner)","Both facing fog. END SEGMENT 2.")
BR.append("AD BREAK 2 (optional) after S6C")
s("S7A","S7 Bunk room sunrise","BUNK",["MIRA","OSM","BILL","TIM"],10,"wide, dark room","Dark bunk room; Mira switches on the frosted panel.","Scene start after optional break.","action: switch press",[],"Sky Diffuser switched on","First glow on ceiling.")
s("S7B","S7 Bunk room sunrise","BUNK",["MIRA","OSM","BILL","TIM"],8,"slow tilt up","Warm dawn color climbs across the ceiling; all heads tilt up; a small lamp flickers softly like candles.","S7A last frame: first glow on ceiling.","eyeline up; light continuity",[("Osmund","Is this the priority brief?")],"Sky Diffuser paints dawn; Lightning Lamp mood flicker (mood light only)","Ceiling full dawn.")
s("S7C","S7 Bunk room sunrise","BUNK",["BILL","TIM","MIRA","OSM"],10,"wide warm tableau","Bill rests a hand on Tim's ring; Tim chirps; everyone in warm light.","S7B last frame: ceiling full dawn, heads up.","eyeline down from ceiling to Bill and Tim",[("Commander Bill D'bears","Let's ship it forward... tomorrow."),("Tim","(chirp)")],None,"Hold; motto card then production card in post.")
P={"grok-imagine-video-1.5":0.08,"grok-imagine-video-1.5-lite":0.02}
for x in S: x["est_usd"]=round(P[x["model"]]*x["duration_s"]+0.01*len(x["reference_images"]),2)
tot=round(sum(x["est_usd"] for x in S),2)
out=dict(title="Forward Supply pilot - Cold Clearance (outpost rework) v2 DRAFT",status="DRAFT, not sent to CNB, not rendered",
  source="storyboard-v1-DRAFT.md; Bible continuity/ch04-military-boutique/bible-v2.yaml",ad_breaks=BR,shots=S,
  totals=dict(shots=len(S),runtime_s=sum(x["duration_s"] for x in S),est_480p_usd=tot,rates="1.5 $0.08/s + $0.01/ref; lite $0.02/s (render_clip_v2.py PRICE)"))
json.dump(out,open("clip-prompts-v2-DRAFT.json","w"),indent=2,ensure_ascii=False)
md=[f"# {out['title']}\n\nStatus: {out['status']}. {len(S)} shots, {out['totals']['runtime_s']} s, est. 480p ${tot} (not spent).\n"]
for x in S:
    md.append(f"## {x['id']} · {x['scene']} · {x['duration_s']} s · {x['model']} · refs {len(x['reference_images'])} · ~${x['est_usd']}\n- Cast: {', '.join(x['cast']) or 'none'}\n- Continues from: {x['continues_from']}\n- Match: {x['match']}\n- Camera: {x['camera']}\n- Product use: {x['product_use'] or '-'}\n- Dialogue: "+("; ".join(f"{d['speaker']}: \"{d['line']}\"" for d in x['dialogue']) or "-")+f"\n- Ends on: {x['last_frame']}\n")
    if x["id"]=="S3C": md.append("**--- AD BREAK 1 (clean break) ---**\n")
    if x["id"]=="S6C": md.append("**--- AD BREAK 2 (optional, clean break) ---**\n")
open("clip-prompts-v2-DRAFT.md","w").write("\n".join(md))
print(len(S),out['totals'])
