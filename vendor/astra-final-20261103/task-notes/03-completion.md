# Task 3 — complete offline

Reused durable intake, attempt history, merge-without-consumption, transitive invalidation and restart recovery. Filter decisions now require literal booleans plus evidence; each placement binds its review version into the manifest. Changed review blocks queue/render/air until a new attempt is assembled. Explicit human release clears review so it cannot silently revive an old filtered placement.

Validation: 7 cumulative hardening tests pass, including truthy filter rejection, review revision and release/re-review. Existing crash-after-seen, merged-but-never-aired and failed/pulled re-offer regressions are retained. This validates review plumbing; it is not real moderation or live chat capture.
