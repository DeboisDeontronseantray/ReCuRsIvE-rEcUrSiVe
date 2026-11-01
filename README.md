# ReCuRsIvE-rEcUrSiVe

This is the private thundertrundle prompt-assembly code for the thundertrundle home AI TV network: the story engine, the v4 prompt system (builders, gates, layers and tests), and the briefs that drive the work. It is proprietary; see `LICENSE`.

## Folder map

| Folder | What it holds |
|---|---|
| `story-engine/` | Story engine: `engine/` (incl. `assemble_prompt.py`), `live/`, `server/`, `client/`, `queues/`, `channels/`, `data/` fixtures |
| `prompts/system-v4-20261030/` | Prompt system v4: `tools/` (builders `build_prompt_v4*`, gates `apply_check_v4*`, `layers_v4.py`), `config/`, `prompts_v4*/` outputs, `tests/` |
| `briefs/` | Task briefs and project notes (e.g. `PROMPT-ASSEMBLY-WIRING-BRIEF-v1.md`) |
<<<<<<< HEAD
| `docs/` | Plans, design docs, and canon notes (`docs/canon/`) |
=======
| `charmeta/` | Character-meta companion store, trait observations, promotion (see `docs/plans/CHARACTER-META-PLAN.md`) |
| `lineage/` | Shared LINEAGE helpers (`aired` index); lineage v1 validators extend this |
| `docs/` | Plans (`docs/plans/`) and specs (`docs/spec/`, e.g. `character-meta/`) |
| `tests/` | Unit tests and scrubbed fixtures (`tests/fixtures/`) |
>>>>>>> origin/cursor/character-meta-impl-m1-8490
