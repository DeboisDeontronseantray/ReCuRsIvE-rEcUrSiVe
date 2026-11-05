import unittest,sys,os,json,glob,subprocess,tempfile
H=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0,f"{H}/tools")
import build_prompt_v4 as B, apply_check_v4 as G, meta_check as M, layers_v4 as L, palette_lut, stride_cut, lipcorr, ref_policy_v4 as RP
def base(**k):
    s={"clip_id":"X1","channel":"Ch11 Fist Theater","duration":8,"clip_type":"breather","setting":"Setting: the lobby.","camera":"Single shot: medium, static camera.",
       "start_frame":"/tmp/s.png","cast":[{"name":"GIDEON","keys":["faded burgundy porter uniform","loosened collar"],"ref":"/tmp/gideon_side.png","eyeline":"the brass bell"}],
       "beats":[{"t":1,"text":"GIDEON polishes the brass bell"}]}
    s.update(k); return s
def fails(s):
    r=B.build(s,strict=False)["report"]; return {k for k,v in r.items() if v[0]=="FAIL"}
class Fluid(unittest.TestCase):
    def test_deterministic(self): self.assertEqual(B.build(base())["args"]["prompt"],B.build(base())["args"]["prompt"])
    def test_varies_across_clips(self):
        ps={B.build(base(clip_id=f"X{i}"))["args"]["prompt"] for i in range(12)}; self.assertGreater(len(ps),3)
    def test_fixed_thread_conditional(self):
        b=B.build(base(clip_type="beat",arc_stage="call",act_goal="the key must reach the roof"))["args"]["prompt"]; self.assertIn("the key must reach the roof",b)
        q=B.build(base(arc_stage="call",act_goal="the key must reach the roof"))["args"]["prompt"]; self.assertNotIn("the key must reach the roof",q)
        t=B.build(base(arc_stage="call",act_goal="the key must reach the roof",detectors={"arc_goal_missing_clips":2}))["args"]["prompt"]; self.assertIn("the key must reach the roof",t)
    def test_fixed_threads_pending(self):
        ft=L.fixed_threads(); self.assertIn("PENDING",ft["_status"]); self.assertTrue(all(t["status"]=="PENDING" for t in ft["threads"]))
    def test_resolver_triggered_only(self):
        self.assertNotIn("drags",B.build(base(resolver_push="GIDEON drags the trolley to the lift"))["args"]["prompt"])
        self.assertIn("drags",B.build(base(resolver_push="GIDEON drags the trolley to the lift",detectors={"arc_goal_missing_clips":2}))["args"]["prompt"])
    def test_tier_decay(self):
        c={"text":"a torn left sleeve with grey tape","short":"torn taped sleeve","tier":"SCAR","episode":1,"still":True,"still_since_index":0}
        self.assertEqual(L.carry_text(c,1),"torn taped sleeve"); self.assertIsNone(L.carry_text(c,3))
        self.assertEqual(L.carry_text({**c,"still":False},5),c["text"])
        self.assertFalse(L.tier_alive({"tier":"FLASH","since_index":0},1,1,1)); self.assertTrue(L.tier_alive({"tier":"LEGEND"},9,9,99))
    def test_created_here_not_carried(self):
        p=B.build(base(consequences=[{"text":"cap on desk","tier":"SCAR","created_here":True}]))["args"]["prompt"]; self.assertNotIn("cap on desk",p)
    def test_state_still_replaces_identity(self):
        a=B.build(base(state_stills=[{"char":"GIDEON","path":"/tmp/GIDEON_QUILL_SU1.png","trait":"tape"}]))["args"]
        self.assertIn("/tmp/GIDEON_QUILL_SU1.png",a["reference_image_paths"]); self.assertNotIn("/tmp/gideon_side.png",a["reference_image_paths"]); self.assertIn("as they are now",a["prompt"])
class Gate(unittest.TestCase):
    def test_clean_passes(self): self.assertEqual(fails(base()),set())
    def test_held_still_fails(self):
        r=G.check_v4("Look: x. Eyelines: A looks at B. At 1 s, A waves. Everything settles into a held still. [Adults only. Nobody looks into the camera.]",{},{})
        self.assertEqual(r["A3_no_hold"][0],"FAIL"); self.assertEqual(r["V1_end_motion"][0],"FAIL")
    def test_ch4_ink_text_fails(self):
        self.assertIn("V2_ch4_photoreal",fails(base(channel="Ch4 Military Boutique / BLACK ICE",look_override="Flat 2D hand-inked comic art.",cast=[])))
    def test_ch4_photoreal_passes(self): self.assertEqual(fails(base(channel="Ch4 Military Boutique / BLACK ICE")),set())
    def test_ch4_ink_ref_fails(self):
        self.assertIn("V2b_ch4_refs",fails(base(channel="Ch4 Military Boutique / BLACK ICE",cast=[{"name":"HERON","keys":["white parka"],"ref":"/x/SHEET_HERON_shinkawa.jpg","eyeline":"the door"}])))
    def test_front_ref_fails(self): self.assertIn("V3_no_front_refs",fails(base(cast=[{"name":"GIDEON","keys":[],"ref":"/x/GIDEON_QUILL_front.png","eyeline":"x"}])))
    def test_tracking_needs_start(self): self.assertIn("V4_start_frame_for_camera",fails(base(start_frame=None,camera="Single shot: side-on dolly tracking at walking pace.")))
    def test_special_pov_needs_start(self): self.assertIn("V4_start_frame_for_camera",fails(base(start_frame=None,setting="Dashcam view through a windshield.")))
    def test_eyeline_required(self): self.assertIn("V6_eyeline_target",fails(base(cast=[])))
    def test_dialogue_cue(self):
        self.assertNotIn("V7_dialogue_cues",fails(base(beats=[{"t":2,"who":"GIDEON","line":"Going up."}])))
        self.assertIn("V7_dialogue_cues",fails(base(beats=[{"t":2,"text":'GIDEON says, "Going up."'}])))
    def test_multistage_camera_fails(self): self.assertIn("V5_one_move",fails(base(camera="Single shot: whip pan to the stairs, then hold medium-wide.")))
    def test_fight_grammar(self):
        s=base(clip_type="fight",beats=[{"t":1,"who":"GIDEON","move":"palm shove","landing":"the thug's shoulder","result":"the thug spins half around"}])
        p=B.build(s)["args"]["prompt"]; self.assertIn("travels toward the lens and lands",p); self.assertIn("visible jolt",p)
    def test_news_comedy(self):
        p=B.build(base(channel="Ch2 News",clip_type="news",cast=[{"name":"MARLA","keys":[],"eyeline":"the monitor"}]))["args"]["prompt"]; self.assertIn("clearly visible in frame",p)
        p=B.build(base(channel="Ch2 News",clip_type="news",serious=True,cast=[{"name":"MARLA","keys":[],"eyeline":"the monitor"}]))["args"]["prompt"]; self.assertNotIn("clearly visible in frame",p)
    def test_label_heron_not_ch4(self): self.assertIn("V11_label",fails(base(extra=["HERON waits."])))
    def test_gatefail_raises(self):
        with self.assertRaises(B.GateFail): B.build(base(start_frame=None,camera="Single shot: dolly tracking."))
    def test_commenter_ref_label(self):
        # NOT YET (trundle 10:48 PM CT Oct 30): commenter images switched off, never attached, gate FAILs
        a=B.build(base(commenter_refs=[{"path":"/tmp/duck.png","purpose":"prop","filtered":True,"what":"rubber duck"}]),strict=False)["args"]
        self.assertNotIn("is only a prop reference",a["prompt"]); self.assertNotIn("/tmp/duck.png",a.get("reference_image_paths",[]))
        self.assertIn("V17_commenter_images_not_yet",fails(base(commenter_refs=[{"path":"/tmp/duck.png","purpose":"prop","filtered":True}])))
class Sidecar(unittest.TestCase):
    def test_v2_fields(self):
        s=B.build(base(parent_clip="NP01",hints_planted=["H1"],saga="DEAD AIR",depth="D1",beats=[{"t":1,"text":"x","requester":"@fan1"}]))["sidecar"]
        for k in G.REQ_SIDE+["layers_on","prompt_sha256","fixed_threads_version"]: self.assertIn(k,s)
        self.assertEqual(s["schema_version"],"tt-clipmeta/v2"); self.assertEqual(s["beats"][0]["requester"],"@fan1"); self.assertEqual(s["depth"],"D1")
    def test_meta_check(self):
        f=M.check({"schema":"tt-clipmeta/v1","fixed_violations":[]},cards={}); kinds={x[0] for x in f}
        self.assertIn("NO_VERSION",kinds); self.assertIn("DEPRECATED",kinds)
        self.assertIn("fixed_hits",M.migrate({"fixed_violations":[1]}))
        self.assertIn("STALE",{x[0] for x in M.check({"schema_version":"v2","meta_version":"odyssey-v1"},episode_passed=True,cards={})})
        self.assertIn("CARD_DRIFT",{x[0] for x in M.check({"schema_version":"v2","meta_version":"system-v4-20261030","card_versions":{"HERON":"v0"}},cards={"HERON":"v1"})})
class Tools(unittest.TestCase):
    @classmethod
    def setUpClass(c):
        c.T=tempfile.mkdtemp()
        for n,src in [("a","testsrc=size=854x480:rate=24"),("b","testsrc2=size=854x480:rate=24")]:
            subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-t","3","-i",src,"-f","lavfi","-t","3","-i","sine=f=300:r=48000","-shortest","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac",f"{c.T}/{n}.mp4"],check=True)
        subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-i","testsrc=size=64x64","-frames:v","1",f"{c.T}/ref.png"],check=True)
    def test_lut(self):
        o=palette_lut.make(f"{self.T}/ref.png",f"{self.T}/x.cube",size=5); l=open(o).read().splitlines(); self.assertEqual(len(l),1+125)
        subprocess.run(["ffmpeg","-v","error","-y","-i",f"{self.T}/a.mp4","-t","0.5","-vf",f"lut3d={o}",f"{self.T}/lut.mp4"],check=True)
    def test_stride_cut(self):
        cp=stride_cut.main(f"{self.T}/sc.mp4",[f"{self.T}/a.mp4",f"{self.T}/b.mp4"]); self.assertTrue(os.path.getsize(f"{self.T}/sc.mp4")>0); self.assertEqual(len(cp),2)
    def test_lipcorr(self): r=lipcorr.score(f"{self.T}/a.mp4",(300,200,100,60)); self.assertIn("r",r)
    def test_state_stills_and_distill(self):
        s=RP.state_stills(f"{self.T}/a.mp4",f"{self.T}/st","A",{"GIDEON":(10,10,100,200)},{"tape":(0,0,50,50)}); self.assertEqual(len(s),2); self.assertTrue(os.path.exists(s[0]["path"]))
        self.assertEqual(len(RP.distill(f"{self.T}/ref.png",3)["palette"]),3)
        self.assertFalse(RP.commenter_filter(f"{self.T}/ref.png")["filtered"])   # fail-closed
        d=RP.commenter_filter(f"{self.T}/st/A_last.png",{"no_face":1,"no_text":1}); self.assertFalse(d["filtered"]); self.assertTrue(d["disabled"])   # NOT YET switch wins over manual clear
        self.assertTrue(RP.commenter_filter(f"{self.T}/st/A_last.png",{"no_face":1,"no_text":1},enabled=True)["filtered"])   # mechanism kept for when trundle turns it on
    def test_static_flip_v3(self):
        # D9b: skip when the live-box v2 module or its CC-BY-SA REF media is absent.
        # The test is unchanged on the live box, where both exist. Do not import the clip.
        sf2="fixtures/thunder-trundle/prompts/experiments/round9-design-20261030/tools/static_flip_v2.py"
        if not os.path.exists(sf2):
            self.skipTest("static_flip_v2.py is not in this repo; the CC-BY-SA static clip is not imported (D9b)")
        import static_flip_v3 as S
        ref=getattr(getattr(S,"sf2",None),"REF",None)
        if not ref or not os.path.exists(ref):
            self.skipTest("static_flip_v2 reference media is not present; the CC-BY-SA static clip is not imported (D9b)")
        S.collapse_dot(f"{self.T}/a.mp4",f"{self.T}/dot.mp4"); self.assertTrue(os.path.getsize(f"{self.T}/dot.mp4")>0)
        steps=S.walk(f"{self.T}/w.mp4",f"{self.T}/a.mp4",[f"{self.T}/b.mp4"],f"{self.T}/b.mp4",wtf_pool=[f"{self.T}/a.mp4"],seed=3)
        self.assertTrue(os.path.getsize(f"{self.T}/w.mp4")>0); self.assertIn("snow",[x[0] for x in steps])
        self.assertTrue(any(any(x[0]=="wtf" for x in S.plan(["m"],["w"],seed=k)) for k in range(12)))
class Regen(unittest.TestCase):
    def test_all_v4_prompts_pass_gate(self):
        fs=glob.glob(f"{H}/prompts_v4/*/*.args.json"); fs=[f for f in fs if "/BLOCKED/" not in f]; self.assertGreater(len(fs),50)
        for f in fs:
            a=json.load(open(f)); p=a["prompt"]
            self.assertNotIn("held still",p); self.assertRegex(p.lower(),"motion carries on through the last half second|eases into the planned end image")
            self.assertNotRegex(p,r"(?i)hand-?inked|crosshatch"); self.assertTrue(all("_front" not in r and "SHEET_" not in r for r in a.get("reference_image_paths",[])),f)
if __name__=="__main__": unittest.main(verbosity=1)
