# Dependency Tree — src/jammy/

Generated 2026-03-31. Shows internal import relationships.

## Layer Diagram

```
Layer 7 (Integration):
  app/playground.py ─── imports from layers 1-4

Layer 6 (Analysis):
  analysis/activation.py ──┐
  analysis/attention.py  ──┤── imports from analysis/__init__
  analysis/embedding.py  ──┤
  analysis/head_roles.py ──┘

Layer 5 (Training — isolated, no external consumers):
  training/trainer.py ──── imports trainer_utils
  training/trainer_utils.py

Layer 4 (Generating):
  generating/generate.py ──── imports config, generation_engine,
  │                           piece_builder, prompt_handler,
  │                           track_builder, validation
  generating/generation_engine.py ── imports tokens
  generating/piece_builder.py ────── imports tokens
  generating/track_builder.py ────── imports tokens
  generating/prompt_handler.py ───── imports tokens
  generating/config.py ───────────── imports tokens
  generating/validation.py ───────── imports constants, tokens
  generating/file_io.py ──────────── imports file_utils, utils
  generating/visualization.py ────── imports constants
  generating/playback.py ─────────── (no jammy imports)

Layer 3 (Embedding):
  embedding/encoder.py ──── imports bar_processing, time_processing,
  │                         track_setup, midi_codec, utils
  embedding/decoder.py ──── imports event_processing, text_parsing,
  │                         familizer
  embedding/preprocess.py ─ imports encoder, file_utils, utils
  embedding/familizer.py ── imports constants, file_utils, tokens
  embedding/bar_processing.py ──── imports constants, midi_codec
  embedding/event_processing.py ── imports midi_codec
  embedding/time_processing.py ─── imports midi_codec
  embedding/text_parsing.py ────── imports tokens, midi_codec
  embedding/track_setup.py ─────── imports constants

Layer 2 (Codec):
  midi_codec.py ──── imports constants, tokens

Layer 1 (Foundation — no internal imports):
  tokens.py         (19+ importers)
  constants.py      (11+ importers)
  file_utils.py     (7 importers)
  utils.py          (8 importers)
  logging_config.py (5 importers)
  load.py           (4 importers)
```

## Preprocessing (data pipeline — partially isolated)

```
preprocessing/midi_stats.py ──────────── imports constants, file_utils, utils
preprocessing/mmd_metadata.py ────────── imports file_utils
preprocessing/picker.py ──────────────── imports file_utils
preprocessing/track_stats_for_encoding.py ── (no jammy imports, standalone)
```

External consumers:
- `examples/track_stats.py` → imports track_stats_for_encoding
- No tests import preprocessing modules directly

## Isolated / No External Consumers

| Module | Imported by anything outside src/jammy/? |
|--------|------------------------------------------|
| `training/trainer.py` | No |
| `training/trainer_utils.py` | No (only by trainer.py) |
| `preprocessing/picker.py` | No |
| `preprocessing/preprocess.py` | No |
| `preprocessing/mmd_metadata.py` | No |
| `preprocessing/midi_stats.py` | No (only by preprocessing internals) |

These modules are data pipeline / training code. They work but have
no tests and no consumers outside their own package.
