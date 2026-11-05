"""Offline prompt recipe: explicit actions, beat spacing, sentiment and layer life."""
import re
from .characters import brief
from .contracts import require

LAYER_LIFE = {
    'spine': 'durable', 'rules': 'durable', 'visual_keys': 'durable', 'consequences': 'tier',
    'headline': 'clip', 'comments': 'clip', 'chaos': 'triggered', 'steering': 'triggered', 'style': 'triggered',
}


def sentiment(text):
    low = text.lower()
    if re.search(r'\b(love|great|amazing|yes|cheer)\b', low):
        return 'A bystander cheers and says'
    if re.search(r'\b(no|hate|awful|stop|boo)\b', low):
        return 'A bystander recoils and says'
    return 'A bystander reacts and says'


def route(prompts, cast_names, *, duration, reserved_beats=1):
    room = max(0, int(duration // 2.5) - reserved_beats)
    # Old carried work wins over recency; fit only breaks ties at the same wait age.
    ranked = sorted(prompts, key=lambda p: (-p['skipped'], -sum(n.lower() in p['original_text'].lower() for n in cast_names), p['received_at'], p['id']))
    if not ranked:
        return {'placed': [], 'carried': []}
    key = lambda p: (p['channel'], p.get('compatibility_key', 'show-default'))
    selected_key = key(ranked[0])
    compatible = [p for p in ranked if key(p) == selected_key]
    placed = compatible[:room]
    placed_ids = {p['id'] for p in placed}
    return {'placed': placed, 'carried': [p for p in ranked if p['id'] not in placed_ids]}


def assemble(*, cards, state_so_far, beats, comments=(), duration=8, arc='the handoff',
             saga='DEAD AIR: The Lost Remote', style_drift=False, style_lock='photoreal winter 1971',
             chaos_trigger=False, steering_trigger=False, handles=()):
    require(state_so_far and arc and saga, 'state, show arc and network saga required')
    times = []
    lines = ['State so far: ' + state_so_far, 'Show arc: ' + arc + '.', 'Network Saga: ' + saga + '.']
    lines.extend(brief(c) for c in cards)
    for b in beats:
        require(all(b.get(k) for k in ('who', 'what', 'how', 'with', 'causes')), 'beat needs who/what/how/with/causes')
        t = b['t']
        require(type(t) in (int, float) and 0 <= t < duration, 'beat timestamp outside clip')
        times.append(t)
        lines.append(f"At {t:g} s, {b['who']} {b['what']}, {b['how']}, with {b['with']}; this causes {b['causes']}.")
    for p in comments:
        t = p['t']
        require(0 <= t < duration, 'comment timestamp outside clip')
        times.append(t)
        # Original language remains exact; untagged reactions acquire an explicit actor.
        lines.append(f"At {t:g} s, {sentiment(p['original_text'])}: \"{p['original_text']}\"; stepping aside with an open hand, clearing the path.")
    require(times == sorted(times) and all(b - a >= 2.5 for a, b in zip(times, times[1:])), 'beat spacing below 2.5 seconds')
    if style_drift:
        lines.append('Correct detected style drift: ' + style_lock + '.')
    if chaos_trigger:
        lines.append('Chaos resolver: return this disruption to the current show arc.')
    if steering_trigger:
        lines.append('Steering: follow the selected viewer action within the locked story spine.')
    lines.append('Continue from the real last frame; motion carries through the free end frame.')
    result = '\n'.join(lines)
    require(all(not h or h.lower().lstrip('@') not in result.lower() for h in handles), 'contributor handle would leak into prompt')
    return result
