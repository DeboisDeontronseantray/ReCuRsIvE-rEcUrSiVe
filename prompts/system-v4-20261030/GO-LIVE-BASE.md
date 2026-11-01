# GO-LIVE BASE (v4.1 only). 2026-10-30 7:42 PM CT. Design only: nothing rendered
Cost basis: $0.068/s at 480p (ledger, COMMERCIALS.md). All costs are estimates; worst case is ×2 (max 2 gens per shot).

## 1. Ready to render now (gate OK, 42 prompts, 363 s, ≈ $24.68, worst ≈ $49.37)
| Channel / show | Prompts (prompts_v41/) | s | est |
|---|---|---|---|
| Ch11 Fist Theater / THE NIGHT PORTER, starter chain NP01→NP16 + SU2–SU6 | 17 odyssey (SU1 is at its 2-gen max; it needs his yes) | 121 | $8.23 |
| Ch2 News P02-3/4 + lipsync LS1–LS4 | 6 | 52 | $3.54 |
| Ch3 Clean Job P03-3, Ch5 Night Patrol P05-3, Ch6 Shopping P06-3, Ch7 Monster Hour P07-2/3, Ch8 Sitcom P08-2/3, Ch9 Iron League P09-2/3, Ch10 Action P10-2/3, Ch12 90s P12-2/3, Ch14 Music P14-1/2/3, Ch16 DOSSIER P16-1/2 | 18 pilot chain clips (10 s each; -2/-3 chain from the real last frame of -1/-2) | 180 | $12.24 |
| Ad: AD-Steve-Cold-Blooded-promo (spin-off promo of the Steve thread) | 1 | 10 | $0.68 |

## 2. New shows (channels with no show): bibles + Ep1 openers (prompts_v41/new-shows/*.draft.json)
Each opener is 10 s, $0.68. All are BLOCKED only on R-REF: each needs a cast look-sheet image first (GenerateImage, paid, needs his yes).
| Ch | Show | Static tangible (look / setting / keys) | Static intangible (want / relationship / arc / world rule / running thread) |
|---|---|---|---|
| 13 Thriller | STATION NINE | early-80s paranoid 35mm; arctic radar room; INGRID grey sweater, blond braid; DELL olive parka, beard | get the tape out / she can't trust DELL / the truth about the downed flight / the station is cut off / static on the scope = H4 |
| 15 Border | THE FERRY AT KOSTIN CROSSING | late-70s cold-war 35mm; ice river ferry landing; VERA greatcoat + rifle; PAVEL deserter tunic, bandaged hand | smuggle her brother across / sister vs deserter brother vs COLONEL REYD / one night, one boat / the ice decides / the ferry bell |
| 17 War Noir | DEBT OF IRON | 2000s desert bleach-bypass; motor pool + armored truck; DECLAN tan shirt, aviators; SAMIRA headscarf, clipboard | sell the truck in 48 h / partners who lie / the rotten choice / the war is "over" / the truck changes hands |
| 18 Late Night | AFTER HOURS WITH GUS BELLWEATHER | 80s talk-show set; GUS powder-blue tux, pompadour; LOU sequined jacket | keep the show on air / GUS + LOU double act / guests from other channels (thread mentions) / channel static stalks GUS / running "static follows me" |
| 19 Cooking | KITCHEN AT MIDNIGHT WITH ODILE | 70s public-TV kitchen; ODILE chef coat, red scarf, silver bun | finish one dish per night / ODILE vs her ingredients / the dishes get stranger each night / food reacts / the green egg |
| 20 Kaiju | GORUMBA VS. THE CITY | 60s miniatures; harbor city; GORUMBA rubber suit, yellow fins; CAPT. MIYAKE navy, binoculars | save the lighthouse / monster and captain linked / GORUMBA keeps coming back / Tekken-style absurd powers allowed / the lighthouse |
| 21 Workout | SWEAT TAPE WITH BRANDI | 80s VHS aerobics; mirrored studio; BRANDI teal leotard, pink leg warmers, side ponytail | never stop / BRANDI vs the back row / the tape gets faster / weird is a plus (T23) / the boombox |
| 22 Western | THE LAST STAGE TO SALT CREEK | 60s Techniscope; desert way station; ROE black duster, silver spurs; PREACHER dusty black suit | deliver what's on the coach / ROE vs THE PREACHER / hero's journey to Salt Creek / the coach is never empty / the strongbox |
Ep1 = 3 clips each (opener + 2 chained), 30 s ≈ $2.04/show, $16.32 for all 8; worst $32.64. Look sheets: 8 images (price per the plan's image rate, not in the ledger).
Shows 15 and 17 reuse the Director's Oct 27 pitches. The other six are new Director concepts. No Story Bot concepts file is on the box (story/approvals/AIR-APPROVALS.jsonl is empty), so the round9 P-series pilots are treated as the approved concepts for Ch2–16.

## 3. Ads
- 16 new ads are BLOCKED on R-REF (no mascot/product ref image). They need 16 ref images (paid), then 16 × $0.68 = $10.88 (worst $21.76).
- AD-Dynapage is a remake: do not render (Oct 29 12:00 PM order). Completed ads air as-is.

## 4. IDs and flips
- Channel IDs: whole numbers 2–22, Ch4 always "Ch4 Military Boutique / BLACK ICE".
- Flips: authentic CRT static between channels, static marks travel between Depths (GLOBAL-STORY.md). These are post/edit, $0.
- 1.2% tag: post burn-in, $0.

## Totals (estimates)
Ready now: $24.68. New-show Ep1s: $16.32 + 8 look sheets. Ads: $10.88 + 16 refs. Video total ≈ $51.88 (worst ≈ $103.76), well under the $500 cap.

> **v48 sync note (Oct 30 ~11:00 PM CT, Director):** See RULES-OF-RECORD T42-T45. Commenter images OFF (config/commenter_images.json); contributors sidecar-only + gate R-NOHANDLES; brand/name line in every bracket + gate R-BRANDS. **Stored prompts_v42 outputs predate the bracket change and need a (free) rebuild before go-live; R-REF hard FAIL is HELD pending Trundle.**
