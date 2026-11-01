import sys,os,json;sys.path.insert(0,os.path.dirname(__file__));import build_prompt_v41 as B
H=B.H; O=f"{H}/prompts_v41/new-shows"
LOOK={"Ch13 Thriller":"Early-1980s paranoid thriller, 35mm, cool Fuji-style stock, green CRT spill.",
"Ch15 Border":"Late-1970s cold-war border thriller, live action, 35mm, muted steel-blue winter colour.",
"Ch17 War Noir":"Mid-2000s desert war film, 35mm pushed, bleach-bypass grade, heat shimmer.",
"Ch18 Late Night":"1980s late-night talk show, studio video, warm tungsten.",
"Ch19 Cooking":"1970s public-TV cooking show, soft studio video, orange and avocado set.",
"Ch20 Kaiju":"1960s Japanese giant-monster film, live action, miniatures, Eastmancolor.",
"Ch21 Workout":"1980s home-workout tape, bright VHS colour, spandex and mirrors.",
"Ch22 Western":"1960s spaghetti western, live action, Techniscope 35mm, sun-bleached."}
SH=[("NS13-1","Ch13 Thriller","STATION NINE","a buried arctic radar room, green consoles, reel-to-reel tape deck",
 [("LT. INGRID HALVORSEN",["grey wool sweater","blond braid"]),("SGT. MARCUS DELL",["olive parka","thick beard"])],
 "Single shot: slow push-in, 40mm, from behind the console, one continuous 10 s take.",
 [{"t":1,"text":"INGRID freezes as a blip crosses her scope and stops"},{"t":4,"text":"INGRID yanks the reel off the tape deck and stuffs it inside her sweater"},{"t":7,"who":"SGT. MARCUS DELL","line":"What did you just take?","cue":"quiet, from the doorway"}]),
("NS15-1","Ch15 Border","THE FERRY AT KOSTIN CROSSING","an ice-choked river landing at dusk, timber cable ferry, ferry hut with stove smoke",
 [("VERA KOST",["patched army greatcoat","rifle on her back"]),("PAVEL KOST",["torn deserter tunic","bandaged hand"])],
 "Single shot: wide static camera, 32mm, low on the landing, one continuous 10 s take.",
 [{"t":1,"text":"PAVEL stumbles out of the birches onto the planks"},{"t":4,"text":"VERA swings her rifle toward him, then lowers it"},{"t":7,"who":"VERA KOST","line":"Get on the boat. Don't talk.","cue":"hard, low"}]),
("NS17-1","Ch17 War Noir","DEBT OF IRON","an abandoned desert motor pool, one dusty armored truck, oil drums",
 [("DECLAN HARGROVE",["sweat-dark tan shirt","aviator sunglasses"]),("SAMIRA NADEER",["white headscarf","clipboard"])],
 "Single shot: handheld medium shot, 28mm, one continuous 10 s take.",
 [{"t":1,"text":"DECLAN kicks the truck's tire; dust bursts off it"},{"t":4,"who":"SAMIRA NADEER","line":"Your company is gone. The truck is all you have.","cue":"flat"},{"t":8,"text":"DECLAN slaps the hood and climbs in"}]),
("NS18-1","Ch18 Late Night","AFTER HOURS WITH GUS BELLWEATHER","a wood-panel talk-show set, city-skyline backdrop, coffee mug on the desk",
 [("GUS BELLWEATHER",["powder-blue tux","huge pompadour"]),("SIDEKICK LOU",["band leader's sequined jacket"])],
 "Single shot: medium two-shot, 35mm, static camera, one continuous 10 s take.",
 [{"t":1,"text":"GUS swivels his chair toward LOU"},{"t":3,"who":"GUS BELLWEATHER","line":"Lou, the static on channel nine is following me home.","cue":"deadpan"},{"t":7,"text":"the TV on the desk ripples with grey static and LOU backs away from it"}]),
("NS19-1","Ch19 Cooking","KITCHEN AT MIDNIGHT WITH ODILE","a 1970s TV kitchen, orange counters, avocado fridge, copper pans",
 [("CHEF ODILE",["white chef coat","red scarf","silver bun"])],
 "Single shot: medium shot, 50mm, eye level, static camera, one continuous 10 s take.",
 [{"t":1,"text":"ODILE cracks an egg; it pours out glowing green"},{"t":4,"who":"CHEF ODILE","line":"Do not be alarmed. That is flavor.","cue":"calm, proud"},{"t":7,"text":"the pan flares and ODILE claps a lid on it"}]),
("NS20-1","Ch20 Kaiju","GORUMBA VS. THE CITY","a miniature 1960s harbor city at night, searchlights",
 [("GORUMBA",["rubber-suit sea monster","yellow dorsal fins"]),("CAPTAIN MIYAKE",["navy uniform","binoculars"])],
 "Single shot: low wide shot, 25mm, static camera, one continuous 10 s take.",
 [{"t":1,"text":"GORUMBA rises out of the harbor, water sheeting off its fins"},{"t":4,"text":"GORUMBA swats a searchlight tower and it topples into the bay"},{"t":7,"who":"CAPTAIN MIYAKE","line":"It came back for the lighthouse.","cue":"shouting over sirens"}]),
("NS21-1","Ch21 Workout","SWEAT TAPE WITH BRANDI","a mirrored aerobics studio, neon stripes, boombox",
 [("BRANDI",["teal leotard","pink leg warmers","giant side ponytail"]),("THE BACK ROW",["three adult dancers in headbands"])],
 "Single shot: wide shot, 28mm, static camera, one continuous 10 s take.",
 [{"t":1,"text":"BRANDI leads high kicks, the back row follows"},{"t":4,"who":"BRANDI","line":"And kick! And kick! And never stop!","cue":"chirpy, a little scary"},{"t":7,"text":"the back row keeps kicking faster than BRANDI, sweat flying"}]),
("NS22-1","Ch22 Western","THE LAST STAGE TO SALT CREEK","a sun-blasted desert way station, hitching rail, stagecoach",
 [("ROSALIND 'ROE' VANCE",["black duster","silver spurs"]),("THE PREACHER",["dusty black suit","flat hat"])],
 "Single shot: extreme wide to medium, slow push-in, 40mm, one continuous 10 s take.",
 [{"t":1,"text":"ROE steps off the stagecoach, eyes on THE PREACHER at the rail"},{"t":4,"who":"THE PREACHER","line":"That coach was supposed to be empty.","cue":"slow drawl"},{"t":7,"text":"ROE lets her duster fall open, hand resting near her holster"}])]
B.STATIC["channels"].update({k:{"look":v} for k,v in LOOK.items()})
out=[]
for cid,ch,show,setting,cast,cam,beats in SH:
    spec={"clip_id":cid,"channel":ch,"show":show,"duration":10,"setting":"Setting: "+setting,"camera":cam,
          "cast":[{"name":n,"keys":k} for n,k in cast],"beats":beats,"refs_raw":[]}
    r=B.build(spec,strict=False); os.makedirs(O,exist_ok=True)
    json.dump({"args":r["args"],"fails":[k for k,v in r["report"].items() if v[0]=="FAIL"],"warns":[k for k,v in r["report"].items() if v[0]=="WARN"],"show":show},open(f"{O}/{cid}.draft.json","w"),indent=1)
    out.append((cid,show,r["args"]["prompt"],[k for k,v in r["report"].items() if v[0]=="FAIL"]))
for o in out: print(o[0],o[1],o[3])
print(out[1][2])
