# Test Plan

**Date:** 2026-03-25
**Current:** 23 tests, 55% coverage
**Target:** 80%+ coverage, unit tests for all core modules
**Supersedes:** `test-coverage-audit.md` (stale)

---

## Approach

1. Write **real unit tests first** — no mocking, fast, test actual behavior
2. Mock **only** when a test would take >5 seconds (model loading, generation)
3. Break into **one PR per module group** — each PR is independently mergeable
4. Keep the existing test structure (`test/embedding/`, `test/generating/`, etc.)

---

## Current Coverage Audit

### Fully covered (≥95%) — no work needed

| Module | Coverage | Tests exist |
|--------|----------|-------------|
| `tokens.py` | 100% | N/A (constants) |
| `constants.py` | 100% | N/A (constants) |
| `track_builder.py` | 100% | `test_track_builder.py` (10 tests) |
| `config.py` | 100% | `test_config.py` (8 tests) |
| `encoder.py` | 100% | `test_encoder.py` |
| `decoder.py` | 100% | `test_decoder.py` |
| `section_building.py` | 100% | via encoder tests |
| `time_processing.py` | 100% | via encoder tests |
| `text_parsing.py` | 97% | via decoder tests |
| `bar_processing.py` | 97% | via encoder tests |
| `generation_engine.py` | 100% | via generate tests |
| `midi_codec.py` | 98% | via encoder/decoder tests |
| `event_processing.py` | 95% | via decoder tests |

### Needs unit tests (20-80%) — core application code

| Module | Coverage | Missing | Priority | PR |
|--------|----------|---------|----------|-----|
| `piece_builder.py` | 78% | init_track, delete_track, get_track_config, set_temperature, get_track_count, get_track | HIGH | PR 1 |
| `generate.py` | 76% | set_force_sequence_length, set_improvisation_level, reset_temperature, generate_n_more_bars, _check_for_errors | HIGH | PR 1 |
| `prompt_handler.py` | 26% | build_next_bar_prompt, _truncate_prompt, _build_other_tracks_text | HIGH | PR 1 |
| `validation.py` | 52% | forcing_bar_count, check_if_prompt_inst_in_tokenizer_vocab | HIGH | PR 1 |
| `utils.py` | 74% | index_has_substring, compute_list_average | MEDIUM | PR 2 |
| `file_utils.py` | 54% | write_to_file, get_files, load_jsonl, FileCompressor | MEDIUM | PR 2 |
| `familizer.py` | 55% | replace_instrument_token, replace_instrument_in_text, replace_instruments, replace_tokens | MEDIUM | PR 3 |
| `playback.py` | 62% | get_music (needs FluidSynth) | LOW | PR 3 |
| `load.py` | 79% | error paths, local loading | LOW | PR 3 |
| `logging_config.py` | 82% | file logging path | LOW | PR 3 |

### 0% coverage — skip or defer

| Module | Lines | Reason |
|--------|-------|--------|
| `preprocessing/midi_stats.py` | 169 | Data analysis, not runtime. Defer. |
| `preprocessing/mmd_metadata.py` | 109 | Data prep, not runtime. Defer. |
| `preprocessing/picker.py` | 20 | Data prep utility. Defer. |
| `stats/track_stats_for_encoding.py` | 73 | Debugging tool. Defer. |
| `training/trainer.py` | 54 | Training pipeline. Defer. |
| `training/trainer_utils.py` | 83 | Training pipeline. Defer. |
| `embedding/preprocess.py` | 25 | Data prep script. Defer. |

These are data processing scripts or training pipelines — not part of the core encode/generate/decode flow. Testing them would require large datasets or model training infrastructure. Skip for now.

---

## PR Breakdown

### PR 1: Generating module tests (~50% of missing coverage)

**Files to test:** `piece_builder.py`, `prompt_handler.py`, `validation.py`, `generate.py`

**Test strategy:** These are all pure logic — no I/O, no model needed. Build state with `PieceBuilder`, test prompt construction with `PromptHandler`, test validation with known inputs.

| Test file | Tests to add |
|-----------|-------------|
| `test/generating/test_piece_builder.py` | `test_init_track`, `test_add_bars`, `test_delete_track`, `test_get_track_config`, `test_set_temperature`, `test_get_track_count`, `test_build_piece_text`, `test_build_track_text` |
| `test/generating/test_prompt_handler.py` | `test_build_next_bar_prompt`, `test_truncate_prompt_under_limit`, `test_truncate_prompt_over_limit`, `test_build_other_tracks_text` |
| `test/generating/test_validation.py` | `test_bar_count_check_exact`, `test_bar_count_check_mismatch`, `test_forcing_bar_count_trims`, `test_forcing_bar_count_too_short`, `test_check_inst_in_vocab` |
| `test/generating/test_generate.py` | `test_set_force_sequence_length`, `test_set_improvisation_level`, `test_reset_temperature` (these are simple setters, fast, no model needed) |

**Mocking needed:** None. `PieceBuilder` and `PromptHandler` are pure state. `validation.py` works on strings. The setter tests on `generate.py` just need a constructed `GenerateMidiText` (model is already session-scoped in conftest).

**Expected impact:** Coverage of generating/ jumps from ~65% to ~90%.

### PR 2: Utility module tests

**Files to test:** `utils.py`, `file_utils.py`, `midi_codec.py` (gap at line 244)

**Test strategy:** Pure functions, all testable without any setup.

| Test file | Tests to add |
|-----------|-------------|
| `test/test_utils.py` | `test_index_has_substring_found`, `test_index_has_substring_not_found`, `test_compute_list_average`, `test_get_datetime_format`, `test_get_miditok_singleton` |
| `test/test_file_utils.py` | `test_write_to_file_string`, `test_write_to_file_dict_json`, `test_write_to_file_creates_dirs`, `test_get_files_extension`, `test_get_files_recursive`, `test_load_jsonl` |
| `test/embedding/test_midi_codec.py` | `test_get_event_time_delta_zero` (the line 244 gap) |

**Mocking needed:** None. All pure functions or file I/O with `tmp_path`.

**Expected impact:** Coverage of utils/file_utils jumps from ~60% to ~95%.

### PR 3: Embedding + remaining modules

**Files to test:** `familizer.py`, `playback.py`, `load.py`, `logging_config.py`

**Test strategy:**
- `familizer.py` — pure logic, test token replacement with known inputs
- `playback.py` — needs FluidSynth (system dep). Test with the Reptilia MIDI that already exists.
- `load.py` — test error paths (invalid path, missing tokenizer). Happy path already covered by conftest fixture.
- `logging_config.py` — test file logging creates output directory

| Test file | Tests to add |
|-----------|-------------|
| `test/embedding/test_familizer.py` | `test_get_family_number`, `test_get_program_number`, `test_replace_instrument_token_family`, `test_replace_instrument_token_program`, `test_replace_instrument_in_text`, `test_drums_passthrough` |
| `test/generating/test_playback.py` | `test_get_music_returns_midi_and_audio` |
| `test/preprocessing/test_load.py` | `test_load_invalid_path_raises`, `test_load_missing_tokenizer_raises` |
| `test/test_logging_config.py` | `test_setup_logging_file_output` |

**Mocking needed:** `test_load.py` — mock `GPT2LMHeadModel.from_pretrained` for the error path tests to avoid downloading the model. `test_playback.py` — no mock, but skip if FluidSynth is not installed.

**Expected impact:** Overall coverage from ~55% to ~75-80%.

---

## Fixtures to add

Add to `test/conftest.py`:

```python
@pytest.fixture
def piece_builder_with_tracks():
    """PieceBuilder pre-loaded with 2 tracks for testing."""

@pytest.fixture
def sample_encoded_text():
    """A short encoded MIDI text for testing (from the Reptilia fixture)."""

@pytest.fixture
def prompt_handler():
    """PromptHandler with default settings."""
```

---

## What NOT to test

- **0% coverage modules** (training, stats, preprocessing) — data pipelines, not core app
- **`app/playground.py`** — Gradio UI, tested manually
- **Existing 100% modules** — don't add redundant tests
- **Randomized generation output** — test structure, not content (generation is non-deterministic)

---

## Order of execution

1. **PR 1** (generating/) — biggest coverage impact, all fast unit tests
2. **PR 2** (utils/) — simple, independent
3. **PR 3** (embedding + misc) — some require FluidSynth, mock for load.py

Each PR should:
- Run `/check` to verify all tests pass
- Run `/review` on the test files
- Target: all new tests run in <5 seconds total (per PR)

---

## Verification

After all 3 PRs merged:

```bash
# Should show 80%+ total coverage
./scripts/run-tests.sh

# No test should take >5 seconds individually
pipenv run pytest test/ -v --durations=10
```
