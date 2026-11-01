# COMMENT-PROMPTS.jsonl row format (add-only)
{id: "cp-<12hex>", handle, text (original), gen_prompt (text-free + "no readable text, no signage lettering"),
 overlay_specs: [{text, kind: caption|price, position, start_s, end_s, style, prompt_id, blocked: [], airable}],
 date, state?, ...}
Overlay edit = new row {id, overlay_specs}; latest wins. No re-render.
Optional (Oct 28 2026): screen_inserts: [{ref "#58" or {lineage,gen}, surface, in, out, loop, treatment crt|scanlines|none}]. Resolved by story-engine/engine/resolve_embed.py (clean masters only); unknown ref = held, not deleted.
