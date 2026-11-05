"""Pure continuity checks; Lifecycle owns persistence and gate failures."""
import re

HELD = re.compile(r'held[- ](?:still|frame)|hold (?:on )?(?:the |a )?(?:last |final )?frame|freeze[- ]frame|ending.*(?:standing still|no motion)', re.I)


def failures(spec, prompt, cards, away_count):
    errors = []
    if not isinstance(spec, dict) or not isinstance(prompt, str):
        return ['structured_spec_and_prompt_required']
    depth = spec.get('depth')
    if type(depth) is not int or not 0 <= depth <= 2:
        errors.append('max_nest_depth_2')
    if depth != 0 and away_count >= 2:
        errors.append('return_D0_within_3_clips')
    if type(spec.get('big_changes')) is not int or not 0 <= spec['big_changes'] <= 1:
        errors.append('one_big_change')
    if not str(spec.get('state_so_far', '')).strip() or 'State so far: ' + str(spec.get('state_so_far', '')) not in prompt:
        errors.append('state_so_far_required')
    cast = spec.get('cast')
    if not isinstance(cast, list) or not cast or not all(isinstance(c, str) for c in cast) or len(set(cast)) != len(cast):
        errors.append('cast_required')
        cast = []
    for cid in cast:
        card = cards.get(cid)
        if not card or any(not card['locked'].get(k) or card['locked'][k] not in prompt
                           for k in ('silhouette', 'color', 'signature_prop')):
            errors.append('three_fixed_visual_keys:' + cid)
    if HELD.search(prompt) or spec.get('held_still') is not False:
        errors.append('no_held_still_ending')
    if spec.get('end_mode') not in ('free', 'pinned'):
        errors.append('end_mode_required')
    if spec.get('end_mode') == 'pinned' and not str(spec.get('pin_reason', '')).strip():
        errors.append('pin_reason_required')
    if not spec.get('corner_tag'):
        errors.append('corner_tag_required')
    if (spec.get('portal') or spec.get('pivot')) and spec.get('transition_method', 'prompt') != 'prompt':
        errors.append('portal_pivot_must_come_from_prompt')
    return errors
