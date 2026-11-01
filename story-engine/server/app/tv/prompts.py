"""TV-safe prompts for season bible, episode beats, and ads."""

SYSTEM_TV_SAFE = """
You write TV-safe scripts for thunder trundle, a home AI TV channel.
Rules you must follow:
- TV-safe only: no explicit sexual content, no graphic gore, no real-person likeness, no real brand/network/game IP names or logos.
- Parody formats and eras, never a specific real show.
- Invent original names. Prefer short, slightly absurd titles that do not start with "The".
- Output valid JSON only when asked for JSON. No markdown fences.
- Season = a show run. Episode = one airable segment outline (beats), not a novel chapter.
"""

BIBLE_USER = """
Build a SHORT show bible for this layered config.

CHANNEL:
{channel_json}

SHOW:
{show_json}

SLOT:
{slot_json}

CONTINUITY (prior state; may be empty):
{continuity_json}

Return JSON:
{{
  "season_title": "string",
  "season_summary": "2-3 sentences",
  "genre": "string",
  "tone": "string",
  "tv_safe_rules": ["..."],
  "cast": [{{"name":"","role":"","notes":""}}],
  "places": [{{"name":"","notes":""}}],
  "world_facts": ["..."],
  "season_arc": "one short paragraph for this season's A-plot"
}}
Keep it compact. Prefer the cast/places already in SHOW; expand lightly if needed.
"""

EPISODE_BEATS_USER = """
Using this short bible, write exactly {episode_count} episode beat sheets for thunder trundle.
Each episode is a short TV segment (not a novel chapter). Match slot length ~{length_minutes} minutes total across the set if possible, but prioritize clear clip-ready beats.

BIBLE:
{bible_json}

SLOT:
{slot_json}

Return JSON:
{{
  "season_title": "string",
  "episodes": [
    {{
      "episode_number": 1,
      "title": "string",
      "logline": "one sentence",
      "tone": "string",
      "runtime_seconds": 90,
      "beats": [
        {{"beat":1, "label":"cold_open|setup|turn|button", "location":"", "cast":[""], "action":"", "dialogue":[{{"speaker":"","line":""}}], "shot_notes":"one camera idea"}}
      ]
    }}
  ]
}}
Exactly {episode_count} episodes. 3-5 beats each. Dialogue short and speakable on camera.
"""

AD_USER = """
Write one TV-safe commercial script for thunder trundle.

CHANNEL:
{channel_json}

SHOW context (may sponsor the ad):
{show_json}

AD REQUEST:
{ad_json}

Duration target: {duration_seconds} seconds (between 10 and 30).

Return JSON:
{{
  "product": "string",
  "duration_seconds": {duration_seconds},
  "pitch_beats": ["hook", "demo", "tag"],
  "vo_lines": ["spoken lines in order"],
  "shot_list": [
    {{"shot":1, "seconds":3, "visual":"", "audio":"VO or SFX"}}
  ],
  "super_text_for_post": ["optional lower-third ideas; not in video prompt"],
  "legal_safety": "remind that product is fictional / parody"
}}
No real brands. No medical claims. No readable logos in visuals.
"""
