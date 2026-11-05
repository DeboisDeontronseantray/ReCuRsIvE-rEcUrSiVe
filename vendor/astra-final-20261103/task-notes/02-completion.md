# Task 2 — complete offline adapter scope

Retained the gateway for D09, D13/D14, D15/D10, B01, B04, D08, A07, D12, D16/D17, B15 and render/inventory. Hardened the consumer audit against relative imports, aliased setter imports and constant-name reflected calls. Pure legacy helpers remain read-only and allowlisted.

Validation: 4 cumulative hardening tests pass; adapter audit PASS with per-callsite hashes. Static auditing is not a security sandbox for arbitrary Python. Production caller replacement cannot be performed under the output-only instruction; integration is documented, not claimed deployed.
