# Offline QC fixture, batch 2

`check_prompt(text, meta)` returns `(allowed, reason)` for the existing A07 gateway:

```python
from qc_fixture import QCLifecycle, check_prompt
from astra_lifecycle.adapters import Adapters

# After intake, pass the viewer's text and contributor metadata to the filter.
allowed, reason = check_prompt(text, meta)
Adapters(life).call('A07', 'filter', prompt_id=prompt_id,
                   allowed=allowed, reason=reason)
```

Construct `life` with `QCLifecycle(path)`. Its gate combines continuity failures
and QC failures, then retains the baseline gate's asset, placement, dependency,
and digest checks. It does not replace baseline filtering with automatic review.
Imports prefer the installed batch 1 package, with the brief's read-only baseline
parent added to `sys.path` only if that package is absent.

`check_clip(spec, prompt, meta)` returns `gate:<rule_id>` strings. The spec must
include `metadata.canon_ref` (show bible ID) and `metadata.audio` with numeric
`integrated_lufs: -16` and `true_peak_dbtp: -1.5` or lower. Other declarations
live in spec metadata or the supplied meta, which takes precedence:

- `kind`: camera and master-ad exceptions require exactly `ad`.
- `reference_images` or `reference_hashes`: nonempty lists of nonempty strings.
- `held_ad: true`, `held_ad_number: 1..16`, `kind: ad`: reference exemption.
  The source supplies no inventory IDs; these are offline declarations, not an
  authenticated held-ad registry. The baseline still requires registered assets.
- `commenter_images`: omitted, false, or empty list.
- `contributor_handles`: list; both @handles and supplied bare handles are blocked.
- `enabled_features`: list of feature IDs; FT1–FT4 are blocked.
- `approval_requested: true` requires nonempty `attached_media_paths`.
- `contains_ad_text`, `generation_overlays`, `contains_kids`,
  `looks_into_camera`: affirmative declarations also fail their respective rules.

Policy patterns are conservative lexical checks, not semantic or media analysis.
The viewer blocklist applies to viewer filtering; it is not applied wholesale to
assembled series prompts. Child, camera, overlay, handle, FT and advertising text
checks apply to generated prompts. The policy JSON records the deliberate
exclusion of owner-name terms to avoid storing the real name.

All reference and attachment checks are declarations only: no media is opened,
resolved or probed, and no network, subprocess, rendering or air operation runs.
The baseline independently verifies registered assets when planning/queuing;
tests use a synthetic text asset. No policy result grants approval or air rights.
The loader reads only its requested JSON, validates the complete rule set, and
rejects missing/unknown rules, invalid patterns, severities and configuration.
