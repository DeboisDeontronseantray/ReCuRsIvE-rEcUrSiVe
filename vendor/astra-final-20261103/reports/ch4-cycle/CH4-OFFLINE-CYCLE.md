# Ch4 offline lifecycle proof

PASS: exactly one canon commit from one verified mock playback receipt; duplicate receipt was a no-op.

No render, network call, live air, bot contact, or spend occurred. Existing Ch4 SEED-S1 bytes supplied the mock transport and reference hashes. Comment/action observations and human approvals are synthetic; this is a state-machine proof, not a visual-content proof.

Source recipe: BLACK ICE BI01 handoff and BI02 comment fixture. Placeholder reference paths were replaced by an existing Ch4 last frame. The historical SEED-S1 held-frame prompt was not reused as a new production prompt.

Intake → filter → assembly → queue → mock dispatch → registered existing media → fixture approval → mock playback → one atomic canon commit.

Fixture input is replayed across intake restart; the receipt is replayed across commit restart. SEED-S2 last-frame bytes stand in for a reviewed new state still: acceptance leaves the primary unchanged, air promotes it and retires SEED-S1, and the next queued clip uses the updated reference. This does not establish that either image depicts the proposed state.

Every recorded event:

| # | Kind | Subject | Before | After |
|---|---|---|---|---|
| 1 | baseline | HERON | None | 1 |
| 2 | baseline_consequence | old-rain | None | FLASH |
| 3 | metadata | ch4-recipe-v1 | 0 | 1 |
| 4 | metadata | ch4-recipe-v2 | 0 | 1 |
| 5 | idea | keep-canister-open | None | open |
| 6 | prompt | ch4-comment-1 | None | eligible |
| 7 | prompt | ch4-comment-unseen | None | eligible |
| 8 | carry | ch4-comment-unseen | eligible | eligible |
| 9 | still | HERON:8c22852c1df23dff566051623d4f329c8f600fb91cd0678c3e5d65e2bee1b108 | None | candidate |
| 10 | still | HERON:8c22852c1df23dff566051623d4f329c8f600fb91cd0678c3e5d65e2bee1b108 | candidate | accepted |
| 11 | clip | ch4-proof-1 | None | planned |
| 12 | placement | ch4-comment-1 | eligible | eligible |
| 13 | clip | ch4-proof-1 | planned | queued |
| 14 | mock_dispatch | ch4-proof-1 | reserved | mock_dispatched |
| 15 | clip | ch4-proof-1 | queued | rendered |
| 16 | clip | ch4-proof-1 | rendered | approved |
| 17 | prompt | ch4-comment-1 | eligible | consumed |
| 18 | clip | ch4-proof-1 | approved | aired |
| 19 | alias | ch4-recipe-v1 | ch4-recipe-v1 | ch4-recipe-v2 |
| 20 | clip | ch4-pulled | None | planned |
| 21 | placement | ch4-comment-unseen | eligible | eligible |
| 22 | clip | ch4-pulled | planned | queued |
| 23 | clip | ch4-dependent | None | planned |
| 24 | clip | ch4-dependent | planned | queued |
| 25 | dependency | ch4-dependent | tentative | invalidated |
| 26 | clip | ch4-pulled | queued | pulled |

Final state:

- ch4-proof-1: aired in the simulator; HERON mood is resolute, summon count 1.
- ch4-comment-1: consumed after mock appearance and playback evidence.
- ch4-comment-unseen: eligible after pull; original text and placement attempt retained.
- ch4-dependent: queued but invalidated; dispatch refused.
- old-rain: incomplete LEGEND input normalized to FLASH and expired on the next aired clip.
- handoff-tension: FLASH, active for the single committed clip.
- SEED-S1, SEED-S2 and SEED-S3: excluded from generation inventory.
- The seam watcher proposed a free ffmpeg Zipper fix; no repair executed.

Final canon snapshot:

```json
{
  "commits": [
    {
      "channel": "Ch4",
      "clip_id": "ch4-proof-1",
      "id": 1,
      "index": 1,
      "receipt_id": "ch4-mock-playback-1"
    }
  ],
  "clocks": {
    "Ch4": {
      "away": 0,
      "episode": 1,
      "index": 1,
      "season": 1
    }
  },
  "cards": {
    "HERON": {
      "abilities": [
        "Systema turn"
      ],
      "field_versions": {
        "abilities": 1,
        "id": 1,
        "locked": 1,
        "locked.color": 1,
        "locked.signature_prop": 1,
        "locked.silhouette": 1,
        "memory_log": 2,
        "name": 1,
        "plastic": 1,
        "plastic.carried_consequences": 2,
        "plastic.gear": 1,
        "plastic.health": 1,
        "plastic.mood": 2,
        "plastic.relationships": 1,
        "refs": 2,
        "summon_count": 2,
        "version": 1,
        "voice": 1,
        "writein_level": 2
      },
      "id": "HERON",
      "locked": {
        "color": "dark coat",
        "signature_prop": "KOLOKOL-7 resonance baton",
        "silhouette": "dark fur greatcoat"
      },
      "memory_log": [
        {
          "clip_id": "ch4-proof-1",
          "index": 1,
          "patch": {
            "mood": "resolute"
          }
        }
      ],
      "name": "HERON",
      "plastic": {
        "carried_consequences": [
          "handoff-tension"
        ],
        "gear": [
          "baton"
        ],
        "health": "steady",
        "mood": "resolute",
        "relationships": {}
      },
      "refs": [
        {
          "evidence": "synthetic fixture state-still annotation; not a real visual QC claim",
          "hash": "8c22852c1df23dff566051623d4f329c8f600fb91cd0678c3e5d65e2bee1b108",
          "state_digest": "b0fe47682d482bf2667444b6db9dea724288f70d264cb7eea2328a9910b98da9"
        }
      ],
      "summon_count": 1,
      "version": 2,
      "voice": "unassigned",
      "writein_level": 1
    }
  },
  "stills": {
    "HERON:8c22852c1df23dff566051623d4f329c8f600fb91cd0678c3e5d65e2bee1b108": {
      "character_id": "HERON",
      "evidence": "fixture review only; no visual QC claim",
      "hash": "8c22852c1df23dff566051623d4f329c8f600fb91cd0678c3e5d65e2bee1b108",
      "state": "primary",
      "state_digest": "08adc88180c42f1fd545ff4df67fdcc347c3e6e3192d07a55b93a451c4b930ab",
      "version": 3
    },
    "HERON:9e23b7dd27db1531479c7764190227bd6c76c47864fbcb8c77fa9219884935e5": {
      "character_id": "HERON",
      "evidence": "fixture current-state baseline",
      "hash": "9e23b7dd27db1531479c7764190227bd6c76c47864fbcb8c77fa9219884935e5",
      "state": "retired",
      "state_digest": "42c7f32433d46e5a29da365f259c29cfa427f471a500a95f7dfc5b45a9f9d664",
      "version": 2
    }
  },
  "consequences": {
    "handoff-tension": {
      "active": true,
      "channel": "Ch4",
      "character_id": "HERON",
      "content_hash": "68bd906edf3f33a98ae2cbed1cf483bf4a7b096bfccef1888e83dd63f1d5d132",
      "episode": 1,
      "evidence": "synthetic fixture annotation",
      "id": "handoff-tension",
      "ref": "8c22852c1df23dff566051623d4f329c8f600fb91cd0678c3e5d65e2bee1b108",
      "season": 1,
      "since_index": 1,
      "source": "ch4-proof-1",
      "text": "the handoff sharpens HERON\u2019s resolve",
      "tier": "FLASH",
      "version": 1
    },
    "old-rain": {
      "active": false,
      "channel": "Ch4",
      "character_id": "HERON",
      "content_hash": "96051f98d5b8676da0596b98e6254abb545b14a0e5bda053ea35de283a172ab5",
      "episode": 1,
      "id": "old-rain",
      "season": 1,
      "since_index": 0,
      "source": "baseline",
      "text": "rain-slick coat",
      "tier": "FLASH",
      "version": 1
    }
  },
  "ledger": [
    {
      "aired": true,
      "aired_at": "2026-11-04T00:13:38.991312+00:00",
      "appeared_text": "HERON follows him across the bridge",
      "channel": "Ch4",
      "clip_id": "ch4-proof-1",
      "contributor_id": "fixture-contributor-1",
      "delivery_status": "appeared",
      "landed": true,
      "observation_evidence": "mock appearance observation; existing seed media does not establish this action",
      "prompt_id": "ch4-comment-1",
      "receipt_id": "ch4-mock-playback-1",
      "requested_hash": "e7fd4020912008c1d5e989f628947020b66f4acc7374e1d78c22708730b646ed",
      "requested_text": "heron should follow him across the bridge",
      "score": 1,
      "subject_matter": [],
      "version": 2,
      "votes": 0
    },
    {
      "aired": false,
      "aired_at": null,
      "appeared_text": "",
      "channel": "Ch4",
      "clip_id": "ch4-pulled",
      "contributor_id": "fixture-contributor-2",
      "delivery_status": "pending",
      "landed": false,
      "observation_evidence": null,
      "prompt_id": "ch4-comment-unseen",
      "receipt_id": null,
      "requested_hash": "6a5e2ceca02fbf2593735a3e81a6454eb4d2b4e7467a13e0c838e9d75b882b28",
      "requested_text": "keep the microfilm canister moving",
      "score": 0,
      "subject_matter": [],
      "version": 1,
      "votes": 0
    }
  ],
  "aliases": {
    "ch4-recipe-v1": "ch4-recipe-v2"
  }
}
```
