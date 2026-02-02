# Test Coverage Audit

**Date:** 2026-02-02
**Current Coverage:** 52%
**Test Results:** 3 passed, 2 failed, 1 error

---

## Executive Summary

The test suite has significant issues:
1. **Low coverage** (52%) with major modules at 0%
2. **Broken tests** - 2 failures due to missing files/wrong paths
3. **Structural issues** - tests return values instead of asserting, missing fixtures
4. **No unit tests** - only integration/E2E tests exist

---

## Current Test Results

| Test | Status | Issue |
|------|--------|-------|
| `test_generation_playground` | ✅ PASS | Runs example script |
| `test_generate` | ✅ PASS | But returns value instead of asserting |
| `test_encode` | ✅ PASS | But returns value instead of asserting |
| `test_decode` | ❌ FAIL | Missing `test/test_decode.json` file |
| `test_compare_generated_encoded` | ❌ ERROR | Missing pytest fixtures |
| `test_gradio` | ❌ FAIL | References old `./source` path |

---

## Coverage by Module

### Well Covered (>70%)

| Module | Coverage | Notes |
|--------|----------|-------|
| `constants.py` | 100% | Simple constants |
| `generation_engine.py` | 94% | Recently refactored |
| `encoder.py` | 93% | Core encoding logic |
| `decoder.py` | 89% | Core decoding logic |
| `piece_builder.py` | 82% | Recently refactored |
| `generate.py` | 71% | Recently refactored |

### Partial Coverage (20-70%)

| Module | Coverage | Missing |
|--------|----------|---------|
| `utils.py` (root) | 76% | File operations, edge cases |
| `generating/utils.py` | 81% | Visualization, validation |
| `preprocessing/load.py` | 77% | Error handling paths |
| `track_builder.py` | 77% | Some static methods |
| `familizer.py` | 56% | Batch operations |
| `playback.py` | 53% | Audio generation |
| `prompt_handler.py` | 20% | Most methods untested |

### No Coverage (0%)

| Module | Lines | Priority |
|--------|-------|----------|
| `logging_config.py` | 27 | LOW - utility |
| `embedding/preprocess.py` | 20 | MEDIUM |
| `preprocessing/midi_stats.py` | 159 | LOW - analysis |
| `preprocessing/mmd_metadata.py` | 101 | LOW - data prep |
| `preprocessing/picker.py` | 16 | LOW - utility |
| `stats/track_stats_for_encoding.py` | 72 | LOW - analysis |
| `training/trainer.py` | 49 | LOW - separate workflow |
| `training/trainer_utils.py` | 79 | LOW - separate workflow |

---

## Test File Issues

### `test/test_tosort.py`

**Issues:**

1. **Line 75, 105, 117** - Tests return values instead of using assertions
   ```python
   # Bad
   return generate_midi, filename

   # Good
   assert generate_midi.generated_piece is not None
   assert Path(filename).exists()
   ```

2. **Line 90-94** - Hardcoded missing file
   ```python
   filename = "test/test_decode.json"  # File doesn't exist
   ```

3. **Line 160** - Function expects fixtures that don't exist
   ```python
   def test_compare_generated_encoded(generated_text, encoded_text):
       # Should be a helper function, not a test
   ```

4. **Line 193** - Wrong directory path
   ```python
   os.chdir("./source")  # Should be "./app" or removed entirely
   ```

5. **Lines 155, 185** - Assertions commented out
   ```python
   # raise ValueError("...")  # Should actually assert
   ```

### `test/test_examples.py`

**Issues:**
- Only 6 lines, no actual assertions
- Just runs the example script without checking output

---

## Proposed Test Structure

```
test/
├── conftest.py                    # Shared fixtures
├── unit/
│   ├── test_constants.py
│   ├── embedding/
│   │   ├── test_encoder.py
│   │   ├── test_decoder.py
│   │   └── test_familizer.py
│   ├── generating/
│   │   ├── test_generation_engine.py
│   │   ├── test_piece_builder.py
│   │   ├── test_track_builder.py
│   │   ├── test_prompt_handler.py
│   │   └── test_utils.py
│   └── preprocessing/
│       └── test_load.py
├── integration/
│   ├── test_generation_pipeline.py
│   ├── test_encode_decode_roundtrip.py
│   └── test_playground.py
└── fixtures/
    ├── sample_midi.mid
    ├── sample_generated.json
    └── sample_encoded.txt
```

---

## Implementation Plan

### Phase 1: Fix Broken Tests (Immediate)

**Goal:** Get all existing tests passing

1. **Fix `test_decode`**
   - Create `test/fixtures/` directory
   - Generate sample JSON file from `test_generate` output
   - Update path to use fixture

2. **Fix `test_compare_generated_encoded`**
   - Rename to `_compare_generated_encoded` (helper, not test)
   - Or convert to proper test with fixtures in `conftest.py`

3. **Fix `test_gradio`**
   - Delete (not a real test) or
   - Convert to proper integration test that doesn't require subprocess

4. **Fix return values**
   - Add assertions to `test_generate`, `test_encode`
   - Remove return statements

### Phase 2: Add Unit Tests for Core Modules (High Priority)

**Target:** 80% coverage on recently refactored modules

1. **`test_generation_engine.py`**
   ```python
   def test_tokenize_returns_tensor():
   def test_generate_produces_track_end():
   def test_decode_returns_string():
   def test_set_improvisation_level():
   ```

2. **`test_piece_builder.py`**
   ```python
   def test_init_track_adds_to_state():
   def test_add_bars_appends_correctly():
   def test_build_piece_text_format():
   def test_delete_track_removes():
   ```

3. **`test_track_builder.py`**
   ```python
   def test_get_last_track():
   def test_extract_tracks():
   def test_strip_track_ends():
   def test_get_new_content():
   ```

4. **`test_prompt_handler.py`**
   ```python
   def test_build_next_bar_prompt():
   def test_enforce_length_limit():
   ```

### Phase 3: Add Integration Tests (Medium Priority)

1. **`test_generation_pipeline.py`**
   - Full generation flow with assertions
   - Test different instruments, densities, temperatures

2. **`test_encode_decode_roundtrip.py`**
   - Encode MIDI → text → decode → compare

### Phase 4: Add Fixtures and Mocks (Medium Priority)

1. **Create `conftest.py`**
   ```python
   @pytest.fixture
   def model_and_tokenizer():
       """Load model once for all tests."""

   @pytest.fixture
   def sample_generated_text():
       """Sample generated MIDI text."""

   @pytest.fixture
   def sample_midi_file(tmp_path):
       """Create temporary MIDI file."""
   ```

2. **Create sample fixture files**
   - `fixtures/sample_midi.mid`
   - `fixtures/sample_generated.json`

### Phase 5: Improve Coverage on Remaining Modules (Low Priority)

Focus on modules actually used in production:
- `familizer.py` (56% → 80%)
- `playback.py` (53% → 70%)
- `prompt_handler.py` (20% → 70%)

Skip modules with specialized purposes:
- `training/` (separate workflow)
- `preprocessing/midi_stats.py` (analysis only)
- `stats/` (debugging tools)

---

## Quick Fixes (Can Do Now)

### 1. Rename helper function

```python
# test_tosort.py line 160
# Before
def test_compare_generated_encoded(generated_text, encoded_text):

# After
def _compare_generated_encoded(generated_text, encoded_text):
```

### 2. Skip broken tests temporarily

```python
import pytest

@pytest.mark.skip(reason="Missing test fixture file")
def test_decode():
    ...

@pytest.mark.skip(reason="References old source path")
def test_gradio():
    ...
```

### 3. Add assertions to passing tests

```python
def test_generate():
    # ... existing code ...

    # Add assertions instead of return
    assert generate_midi.generated_piece is not None
    assert "PIECE_START" in generate_midi.generated_piece
    assert "TRACK_END" in generate_midi.generated_piece
    assert os.path.exists(filename)
```

---

## Coverage Targets

| Phase | Target | Timeline |
|-------|--------|----------|
| Phase 1 | All tests passing | Immediate |
| Phase 2 | 70% coverage | Short-term |
| Phase 3 | 80% coverage on core modules | Medium-term |
| Phase 4 | Proper fixtures/mocks | Medium-term |
| Phase 5 | 80% overall | Long-term |

---

## Files to Create

| File | Purpose |
|------|---------|
| `test/conftest.py` | Shared pytest fixtures |
| `test/fixtures/sample_generated.json` | Sample generated output |
| `test/unit/generating/test_piece_builder.py` | Unit tests |
| `test/unit/generating/test_track_builder.py` | Unit tests |
| `test/unit/generating/test_generation_engine.py` | Unit tests |

---

## Related Documents

- [Code Audit Plan](./code-audit-plan.md) - Phase 5: Testing Improvements
- [Design Audit Implementation Plan](./design-audit-implementation-plan.md)
