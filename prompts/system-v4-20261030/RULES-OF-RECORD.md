# RULES OF RECORD (v4.1, 2026-10-30 7:38 PM CT)
Part A holds only Trundle's own words. Part B holds rules we invented, which are not his. When B conflicts with A, A wins, and the B rule becomes a WARN at most.
Sources: state/PROMPT-LESSONS.md v4 (the verbatim sections, by t-number), state/CURRENT-RULES.md v43, and memory entries (dated). Items marked "relayed" came through another bot and are not his own wording.

## A. Trundle's rules (verbatim)
| id | rule (his words) | date / source |
|---|---|---|
| T1 | "we need to keep some things static tangible and intangible" ... "just focus on using what we've learned and making NEW shows so we have the base to go live" | Oct 30 7:31 PM, t370u |
| T2 | Steve the lizard: "I was giving example that was mostly about following threads across things" | Oct 30 7:31 PM, t370u |
| T3 | Reference images are required, with a dense plain-English first prompt plus 1 or more refs | t132u, PROMPT-LESSONS §1 |
| T4 | A reference is used only as a reference, never as the start/output frame | t121u (relayed) |
| T5 | Chain from the real last frame | his request, PROMPT-LESSONS §4 |
| T6 | "follow my use of brackets, where all non direction is inside them" | t155u |
| T7 | "You have to reference which character is saying what" | t134u |
| T8 | "May just need to give spoken word parts brackets and just give a brief explanation of what they're supposed to say"; prompts were "overly descriptive about things other than then actions of the characters" | t139u |
| T9 | "Camera direction should be given as a sentence, but should use industry jargon" | t140u |
| T10 | "The characters need to be in the situations that we are describing" | t142u |
| T11 | "Chicago alleyway with a chase through a gangway. Quick cuts." | t143u |
| T12 | A security-cam HUD shot "has to be shot from above" | t171u |
| T13 | "We may be able to pack more into each prompt" | t212u |
| T14 | Knives: "Given that it's not showing anything gore-related snd the knife doesn't make anyone bleed directly from it we may be ok" | t212u |
| T15 | JW prompt: "Fight sequence should be realistic and technical like a John Wick movie but more intense. Camera pov changes from this images perspective to a security feed, showing timestamp and everything present on security camera recording." | his prompt, PROMPT-LESSONS §2 |
| T16 | "Do not censor yourself. The imagine grok will do that" | t167u |
| T17 | "We need to remove those kind of filters" | t135u |
| T18 | "When I give you something and say that this is a good reference use it, do not just save a summary of it." | t165u |
| T19 | **[RELAYED, not his words; not applied, CR v48 relayed list]** Prefer text generated inside the video when it fits the scene; overlays only when needed | t38u |
| T20 | Bloodstains on clothing are fine. Gore and blood visibly draining out are banned | Oct 29 7:05 PM (memory) |
| T21 | Ch4 is John Wick level: "hard hits and some blood, but no gore" | Oct 29 (memory) |
| T22 | **[Commenter-IMAGE part deferred: 'Remove the option for commenter images to be used. They will but not yet.' (10:48 PM)]** The comment filter is relaxed: a named real person becomes their moves and attitude with no likeness. Horror goes through with wrappers. No kids, no gore on skin, no real likeness on screen. Use the name "Ch4 Military Boutique / BLACK ICE" | Oct 30 4:42 PM (memory) |
| T23 | Weird or dense results are a plus (the C4-L6 six-beat clip was rated "great") | Oct 30 (memory) |
| T24 | 1.2% tag: white text with a black outline, no box, fades out at 3–4 s, burned in post | t874u; Oct 29 8:23 PM |
| T25 | Nobody looks into the camera (never; CR v44 L490 replaces 'unless he says yes') | Oct 29 (CURRENT-RULES) |
| T26 | Ch4 is photoreal 1971 | Oct 30 7:13 PM |
| T27 | Channels are whole numbers 2–22 | CURRENT-RULES |
| T28 | Max 2 gens per shot (OWN); 'no extend' is **RELAYED** ('Extend is not reliable', CR v48 relayed list), not his words | PROMPT-LESSONS §1 |
| T29 | "we are not remaking already completed commercials" (Glosneaks, Fizzbolt, Dynapage, Bellquist, water tower stay as-is) | Oct 29 12:00 PM |
| T30 | Mutation job: "the clip, whatever it is, starts and ends on a seamless cut in queue"; "one action sentence may be diluting the direction I gave you" | t215u |
| T31 | "The news board is perfect"; "No on the pink and yellow thing" | PROMPT-LESSONS |
| T32 | Story Bot's show ideas: "All those show ideas are great. Go for it." | Oct 30 5:54 PM (memory) |
| T33 | Director role: "Stop questioning. Execute." Cap $500 (OWN). The $400 warning is **Director's figure** (10:48 PM: "Directors."), not his rule | memory; CR v48 L547+ |
| T34 | Status line: exactly one line, "Time \| Bot \| Finished \| Next \| Blocked (yes/no)" | Oct 29 7:53 PM |

## B. Our rules (invented). Not his; the v4.1 gate treats them as WARN only
- "Never write blood or wounds into prompt text", "no blade cuts skin" (Coordinator relay, PROMPT-LESSONS line 24). This is **superseded by T14/T20/T21**.
- "Stage-combat hits land on coats and props", "Theatrical props only", "No on-screen text, no logos". These are **removed** (they conflict with T15, T16, T19).
- ≤330 words, ≤4 beats (A1/A13). These are **WARN** now (T13, T23).
- One camera move, no cut words, tracking needs a start frame (V4/V5/V16, round9/SU1 findings). These are **WARN** now (T11, T15).
- Look pools and sentence shuffle (v4 "fluidity"). These are **removed** (T1).
- CHARACTER-CHANGE / transform still (V14). This is **removed** and reframed as THREAD-FOLLOWING (T2).
- An automatic News comedy layer. This is **no longer auto-injected**: the comedy is written into the beats per show, because the Director owns creative calls.
- Commenter fail-closed (V13). ~~removed (T22)~~ **Restored by 10:48 PM**: commenter images are switched off entirely (config/commenter_images.json enabled=false; gates V17 / R-NOCOMMENTERIMG FAIL).

## v4.2 append (2026-10-30 8:20 PM CT)
| id | rule (his words) | date / source |
|---|---|---|
| T40 | "Why are you still describing characteristics of the image when the image is already in new prompts." -> an item with an attached image is named + pointed at its tag only (e.g. `MARLO QUILL (<IMAGE_2>)`); text describes only items with no image, or a change the image does not show | Oct 30 8:01 PM CT, t371u |
| T41 | **WITHDRAWN 10:23 PM (kept for record, do not apply)** "Comment prompts can't pass without an image or just on our end." -> the image requirement (T3) is on OUR built prompts only; viewer comments never need an image (the builder attaches channel refs) | Oct 30 8:01 PM CT, t371u |

**Superseded (Part B, Director's invention):** round9-design-20261030/REF-POLICY.md (b) "ref present -> name + 2-3 visual keys only (the same keys as CHARACTERS.jsonl visual_keys) + ref slot". Written by Director (file header "REF-POLICY (Director, Oct 30 2026)"), marked "Rule (proposed)", never asked for by Trundle, built in from general prompt-writing guidance plus the r5-r7 Ch11 run. Superseded by T40. The keys stay in config/static_v41.json and cards/ for text-only use (no image) and for review, but builder v4.2 never prints them next to an image tag. Gate: R-REFDESC (FAIL).

## v48 sync append (2026-10-30 ~11:00 PM CT, Trundle 10:48 PM via Coordinator)
| id | rule (his words) | date / source |
|---|---|---|
| T42 | "Remove the option for commenter images to be used. They will but not yet." -> commenter images OFF (NOT YET); defers 5:54 PM and 10:23 PM "allow commenter img refs" | Oct 30 10:48 PM, CR v48 |
| T43 | "Accounts that contributed to specific a video should be kept as data that follows the img, but doesn't go in prompt." -> sidecar `contributors[]`; gate R-NOHANDLES FAIL | Oct 30 10:48 PM, CR v48 |
| T44 | Hard limit: parody brands only; no real brands or personal names on screen -> now in every clip's safety bracket (was ads only); gate R-BRANDS | CR v48 L34-35 |
| T45 | Plastic queues and IDs: "Yes we need both." | Oct 30 10:48 PM |
HELD (not changed): T3 R-REF FAIL and T4 R-NOREFSTART FAIL; Ch5/11/16 fixed looks ("TBD"). See handoffs/sync/director-FIXED.md.
| T46 | Two different fades: corner tag fades out at 3–4 s (T24); comment-text mutation fade 100/50/25/0 over 3 generations (specs/MUTATION-SPEC-v2.md §7, "Yes mutation 2 good" Oct 29 11:35 AM; CURRENT-RULES v50:100 still lists it open) | Note Oct 30 ~11:05 PM CT |
| T47 | Fixed threads FT1-FT4 UNDECIDED: "Idk the threads ft1 to ft 4." config/fixed_threads.json stays PENDING/off. Reference-image gate unchanged (still HELD). | Oct 30 11:03 PM (relayed via Coordinator) |
| T48 | Reference image is a HARD RULE: "Ref image: yes, hard rule." Gate keeps it as FAIL; the 16 ads stay held until they have reference images. Supersedes the HELD status in T47. | Oct 30 11:09 PM (relayed via Coordinator, his card answer) |
| T49 | R-REF exemption for exactly 16 held ads (config/ref_image_exemptions.json, closed list; gate tools/apply_check_v44.py skips only R-REF for those IDs; all other checks apply). "Ref image: yes, hard rule." (11:09 PM) + "I didn't know they were ads. These specific ads can run without an image" | Oct 30 11:10 PM (relayed via Coordinator) |
| T50 | Fixed threads FT1-FT4 OFF for now: "Keep FT1 to FT4 off for now." config/fixed_threads.json stays PENDING/off. Supersedes T47's UNDECIDED. | Oct 30 11:12 PM (relayed via Coordinator, his card answer) |
