# ReCuRsIvE-rEcUrSiVe

This is the private Thunder Trundle prompt-assembly code for the Thunder Trundle home AI TV network: the story engine, the v4 prompt system (builders, gates, layers and tests), and the briefs that drive the work. It is proprietary; see `LICENSE`.

## Folder map

| Folder | What it holds |
|---|---|
| `story-engine/` | Story engine: `engine/` (incl. `assemble_prompt.py`), `live/`, `server/`, `client/`, `queues/`, `channels/`, `data/` fixtures |
| `prompts/system-v4-20261030/` | Prompt system v4: `tools/` (builders `build_prompt_v4*`, gates `apply_check_v4*`, `layers_v4.py`), `config/`, `prompts_v4*/` outputs, `tests/` |
| `briefs/` | Task briefs and project notes (e.g. `PROMPT-ASSEMBLY-WIRING-BRIEF-v1.md`) |
| `charmeta/` | Character-meta companion store, trait observations, promotion (see `docs/plans/CHARACTER-META-PLAN.md`) |
| `lineage/` | Shared LINEAGE helpers (`aired` index, `derive_aired` CLI); see `lineage/MEDIA_LIBRARIAN_HOOK.md` |
| `docs/` | Plans (`docs/plans/`) and specs (`docs/spec/`, e.g. `character-meta/`) |
| `tests/` | Unit tests and scrubbed fixtures (`tests/fixtures/`) |
