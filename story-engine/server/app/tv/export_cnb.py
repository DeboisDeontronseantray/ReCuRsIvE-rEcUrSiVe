"""Export episode beats / ad scripts to Commercial News Break clip prompts.

Formats follow out-of-scope/shared/streaming/grok-imagine-90s-news-guide.md and
templates/PROMPT-TEMPLATES.md: structured brief, no on-screen text, 4:3-safe,
one prompt per clip. Does NOT send anything to CNB — local files only.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STYLE_TAIL = (
    ", 1990s American local television production, shot on broadcast studio camera, "
    "natural skin texture, practical lighting, realistic proportions, "
    "center-weighted composition, no text, no logos, no watermarks"
)

NEGATIVES = (
    "no on-screen text, no letters, no subtitles, no logos, no brand names, "
    "no real people, no celebrity likeness, no extra fingers, no deformed hands, "
    "no warped faces, no modern smartphones, no flat screens, no LED lighting"
)


def _clip_brief(
    *,
    format_era: str,
    talent: str,
    shot: str,
    dialogue: str,
    performance: str,
    set_feel: str,
    duration: int,
    palette: str,
) -> str:
    return f"""FORMAT & ERA: {format_era} Duration {duration} seconds, one continuous shot, no cuts.
IMAGE & TAPE TEXTURE: Clean well-lit 1990s set/production design (grade VHS/CRT in post; do not prompt mushy VHS faces). Soft detail OK. No modern HDR look.
CAMERA & LENS: Broadcast zoom around 28-40mm equivalent, deep focus. {shot}
SHOT: Center-weighted for 4:3-safe framing. Leave bottom fifth and top-right clean for graphics.
TALENT (fictional): {talent}
SET & GRAPHICS FEEL: {set_feel} No readable text, no logos, no letters anywhere in the frame.
LIGHTING: Flat high-key three-point studio light unless field shot specified.
PALETTE: {palette}
PERFORMANCE: {performance}
DIALOGUE (spoken exactly, nothing more): "{dialogue}"
SOUND: Slightly compressed broadcast audio, faint tape hiss. Talent voice only unless noted.
AVOID: {NEGATIVES}.
STYLE: {STYLE_TAIL}
""".strip()


def export_cnb_prompts(
    *,
    channel: dict,
    show: dict,
    bible: dict,
    episodes: dict,
    ad: dict,
    out_dir: Path,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    clips_dir = out_dir / "clips"
    clips_dir.mkdir(exist_ok=True)

    palette = ", ".join(channel.get("look", {}).get("palette") or ["slate", "olive", "chrome"])
    cast_by_name = {c.get("name"): c for c in (bible.get("cast") or []) if c.get("name")}

    manifest = {
        "channel_id": channel.get("id"),
        "channel_name": channel.get("name"),
        "show_id": show.get("id"),
        "show_title": show.get("title") or bible.get("season_title"),
        "note": "LOCAL ONLY — do not hand to CNB until trundle reviews",
        "clips": [],
    }

    # Episode beat clips
    for ep in episodes.get("episodes") or []:
        ep_n = ep.get("episode_number")
        for beat in ep.get("beats") or []:
            cast_names = beat.get("cast") or []
            talent_bits = []
            for name in cast_names:
                c = cast_by_name.get(name) or {"name": name, "notes": "fictional talent"}
                talent_bits.append(f"{c.get('name')}: {c.get('notes') or c.get('role') or 'talent'}")
            talent = "; ".join(talent_bits) or "fictional catalog host, mid-30s, duty jacket"
            lines = beat.get("dialogue") or []
            if lines:
                dialogue = " ".join(
                    f"{d.get('speaker','')}: {d.get('line','')}".strip(": ") for d in lines
                )
            else:
                dialogue = (beat.get("action") or "Beat continues.")[:160]
            duration = 6
            brief = _clip_brief(
                format_era=(
                    f"A mid-1990s / near-future hybrid television segment for fictional station thunder trundle, "
                    f"channel {channel.get('id')} {channel.get('name')}, show {show.get('title')}."
                ),
                talent=talent,
                shot=beat.get("shot_notes") or "Locked-off medium shot, slow push-in.",
                dialogue=dialogue.replace('"', "'")[:220],
                performance="Measured broadcast delivery; one clear action only.",
                set_feel=f"{beat.get('location') or 'Catalog Floor'}; {beat.get('action') or ''}",
                duration=duration,
                palette=palette,
            )
            clip_id = f"ep{ep_n}_beat{beat.get('beat')}_{beat.get('label') or 'beat'}"
            clip_id = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in clip_id)
            md_path = clips_dir / f"{clip_id}.md"
            json_path = clips_dir / f"{clip_id}.json"
            md_path.write_text(brief + "\n")
            payload = {
                "clip_id": clip_id,
                "kind": "episode_beat",
                "episode_number": ep_n,
                "episode_title": ep.get("title"),
                "beat": beat,
                "prompt": brief,
                "duration_seconds": duration,
                "model_hint": "grok-imagine-video-1.5",
                "handoff": "local_only_awaiting_trundle",
            }
            json_path.write_text(json.dumps(payload, indent=2) + "\n")
            manifest["clips"].append(
                {"clip_id": clip_id, "json": str(json_path), "md": str(md_path), "kind": "episode_beat"}
            )

    # Ad shots
    for shot in ad.get("shot_list") or []:
        sec = int(shot.get("seconds") or 3)
        sec = max(2, min(8, sec))
        vo = shot.get("audio") or ""
        if not vo and ad.get("vo_lines"):
            # fall back to first unused style: join lightly
            vo = " / ".join(ad.get("vo_lines")[:2])
        brief = _clip_brief(
            format_era=(
                f"A {ad.get('duration_seconds', 15)}-second 1990s-style commercial break for fictional "
                f"thunder trundle house brand; product {ad.get('product')}."
            ),
            talent="fictional catalog demonstrator; no real person likeness",
            shot="Static or slow dolly; one product action.",
            dialogue=(vo or ad.get("product") or "Ship it forward.").replace('"', "'")[:200],
            performance="Enthusiastic but dry; absurd-serious.",
            set_feel=shot.get("visual") or "chrome olive catalog floor, product hero shot",
            duration=sec,
            palette=palette,
        )
        clip_id = f"ad_shot{shot.get('shot')}"
        md_path = clips_dir / f"{clip_id}.md"
        json_path = clips_dir / f"{clip_id}.json"
        md_path.write_text(brief + "\n")
        payload = {
            "clip_id": clip_id,
            "kind": "ad_shot",
            "product": ad.get("product"),
            "shot": shot,
            "prompt": brief,
            "duration_seconds": sec,
            "model_hint": "grok-imagine-video-1.5-lite",
            "handoff": "local_only_awaiting_trundle",
        }
        json_path.write_text(json.dumps(payload, indent=2) + "\n")
        manifest["clips"].append(
            {"clip_id": clip_id, "json": str(json_path), "md": str(md_path), "kind": "ad_shot"}
        )

    # Also dump full ad script markdown
    ad_md = out_dir / "ad_script.md"
    lines = [
        f"# Ad: {ad.get('product')}",
        f"Duration: {ad.get('duration_seconds')}s",
        "",
        "## Pitch beats",
        *[f"- {b}" for b in (ad.get("pitch_beats") or [])],
        "",
        "## VO",
        *[f"- {v}" for v in (ad.get("vo_lines") or [])],
        "",
        "## Shot list",
    ]
    for s in ad.get("shot_list") or []:
        lines.append(f"- Shot {s.get('shot')} ({s.get('seconds')}s): {s.get('visual')} | {s.get('audio')}")
    lines += ["", f"Legal: {ad.get('legal_safety') or 'fictional parody product'}"]
    ad_md.write_text("\n".join(lines) + "\n")

    man_path = out_dir / "manifest.json"
    man_path.write_text(json.dumps(manifest, indent=2) + "\n")
    index_md = out_dir / "README.md"
    index_md.write_text(
        "# CNB export (LOCAL ONLY)\n\n"
        "Do not send to Commercial News Break until trundle reviews.\n\n"
        f"Clips: {len(manifest['clips'])}\n"
        f"Manifest: {man_path}\n"
    )
    return {
        "manifest": str(man_path),
        "clips_dir": str(clips_dir),
        "ad_script": str(ad_md),
        "clip_count": len(manifest["clips"]),
    }
