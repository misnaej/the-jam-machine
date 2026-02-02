# Genre Prediction Folder Audit Report

**Audited:** `genre_prediction/`
**Date:** 2026-02-02
**Status:** Complete

---

## Executive Summary

The genre_prediction folder is a **standalone system** with no integration to the main `src/the_jam_machine/` package. It suffers from critical issues: module-level code execution, significant code duplication (same functions copied 3-4 times), and poor separation of concerns. The code is functional but not maintainable or testable.

---

## 1. File Overview

| File | Lines | Classes | Functions | Purpose |
|------|-------|---------|-----------|---------|
| `midi_preprocessing.py` | 155 | 1 | 16 | Data preprocessing pipeline |
| `midi_train.py` | 113 | 0 | 2 | Model training script |
| `midi_prediction.py` | 72 | 0 | 5 | Genre prediction |
| `streamlit_app.py` | 188 | 0 | 4 | Streamlit web UI |
| `streamlit_app_utils.py` | 250 | 0 | 10 | MIDI stats and file utilities |
| **Total** | **778** | **1** | **37** | |

---

## 2. Module Analysis

### 2.1 `midi_preprocessing.py` - DataPreprocessing Class

**Responsibility:** Data preprocessing pipeline

**Key Methods:**
- Data cleaning: `drop_duplicates()`, `drop_nans()`, `drop_columns_to_drop()`
- Data typing: `def_categorical()`, `def_numerical()`, `force_numerical()`, `force_categorical()`
- Feature engineering: `drop_target()`, `split_data()`
- ML workflow: `process_fit()`, `process_predict_only()`

**Issues:**
- 155 lines in single class - violates SRP
- Hardcoded column names (lines 26-39)
- Mixes data loading, cleaning, splitting, and type casting
- Commented-out code throughout

---

### 2.2 `midi_train.py` - Training Script (CRITICAL)

**Responsibility:** Train a RandomForest classifier

**Issues:**
- **Not a module - it's a script** with module-level code execution
- Lines 19-27: Data loading at module level
- Lines 40-48: Inline model training code
- Lines 50-58: Duplicated preprocessing function
- **CRITICAL:** Importing this file executes training

---

### 2.3 `midi_prediction.py` - Prediction Functions (CRITICAL)

**Responsibility:** Load models and make predictions

**Issues:**
- **Module-level test code** (lines 66-72)
- Duplicated `pre_process_data()` function (identical to midi_train.py)
- Hardcoded pickle file paths
- `pandas` imported twice
- Unused imports (`streamlit`, `LogisticRegression`)

---

### 2.4 `streamlit_app.py` - Web UI

**Responsibility:** Streamlit interface for genre prediction

**Features:**
- File selection and exploration
- MIDI file statistics display
- Genre prediction
- File organization (move to good/meh/bad/delete)

**Issues:**
- Hardcoded test paths (5+ locations)
- Bare except clauses (5x)
- Variable `nlah` with no meaningful name
- Always-true conditional (`if True:`)
- Complex nested UI logic mixed with data processing

---

### 2.5 `streamlit_app_utils.py` - Utility Functions

**Responsibility:** MIDI statistics and file operations

**Key Functions:**
- MIDI analysis: `compute_statistics()`, `categorize_midi_instrument()`
- File management: `move_file()`, `delete_file()`, `get_midi_file_list()`
- Statistics: `compute_folder_statistics()`, `show_minimal_stat_table()`

**Issues:**
- `compute_statistics()` is 90+ lines, computes 22 statistics (should be split)
- Hardcoded file paths in `set_saving_path()`
- Missing error handling in file operations
- Bare except clauses
- Poor separation: file ops + MIDI analysis + UI utilities

---

## 3. Critical Issues

### 3.1 Code Duplication (Very High Priority)

**`pre_process_data()` duplicated in:**
- `midi_train.py` lines 51-58
- `midi_prediction.py` lines 26-37
- `streamlit_app.py` lines 37-48

**`load_pickles()` duplicated in:**
- `midi_prediction.py`
- `streamlit_app.py`

**`make_predictions()` duplicated in:**
- `midi_prediction.py`
- `streamlit_app.py`

### 3.2 Module-Level Execution (Critical)

```python
# midi_train.py - executes on import!
df = pd.read_csv("./data/statistics_v2.csv")  # line 19
model.fit(X_train, y_train)  # line 48

# midi_prediction.py - test code at module level
if __name__ == "__main__":  # MISSING!
    test_df = pd.read_csv(...)  # line 67
```

### 3.3 Hardcoded Paths

| File | Line | Path |
|------|------|------|
| midi_train.py | 19 | `"./data/statistics_v2.csv"` |
| midi_prediction.py | 51-53 | Three pickle paths |
| streamlit_app.py | 85, 154, 165, 174 | Test directory |
| streamlit_app_utils.py | 174-182 | User paths |

### 3.4 SRP Violations

**DataPreprocessing class does 6+ things:**
- Cleaning (duplicates, NaNs)
- Column management
- Type coercion
- Imputation
- Target extraction
- Train/test splitting

**streamlit_app.py mixes:**
- UI logic
- File operations
- Model inference
- Data processing

---

## 4. Dependency Map

```
midi_train.py (script)
├── DataPreprocessing [from midi_preprocessing]
├── RandomForestClassifier [sklearn]
├── LabelEncoder [sklearn]
└── (inline execution with hardcoded paths)

midi_prediction.py (module + test code)
├── DataPreprocessing [from midi_preprocessing]
├── streamlit [unused]
└── pickle [model loading]

streamlit_app.py (web interface)
├── streamlit_app_utils [all functions via *]
├── DataPreprocessing [from midi_preprocessing]
└── (pickle, os, pathlib)

streamlit_app_utils.py (utilities)
├── pretty_midi [MIDI analysis]
├── pandas [data operations]
└── os [file operations]
```

**No integration with main `src/the_jam_machine/` package**

---

## 5. Proposed Reorganization

### Option 1: Modular Package Structure (Recommended)

```
genre_prediction/
├── __init__.py
├── config.py                    # Constants and paths
├── preprocessing/
│   ├── __init__.py
│   ├── cleaner.py              # Data cleaning
│   ├── transformer.py          # Type coercion, imputation
│   └── pipeline.py             # Orchestration
├── training/
│   ├── __init__.py
│   └── trainer.py              # With if __name__ == '__main__'
├── prediction/
│   ├── __init__.py
│   ├── predictor.py            # Unified prediction API
│   └── model_loader.py         # Pickle loading
├── midi_utils/
│   ├── __init__.py
│   ├── analyzer.py             # compute_statistics
│   └── file_ops.py             # move_file, delete_file
└── app/
    ├── __init__.py
    └── streamlit_app.py        # UI only
```

### Option 2: Flatten but Separate Concerns

```
genre_prediction/
├── __init__.py
├── config.py                    # All paths and constants
├── preprocessing.py             # Refactored DataPreprocessing
├── midi_analyzer.py             # Statistics functions
├── file_manager.py              # File operations
├── model_utils.py               # Pickle loading, prediction
├── train.py                     # Training script
└── app.py                       # Streamlit UI
```

---

## 6. Specific Refactoring Recommendations

### 6.1 Extract Shared Functions into `model_utils.py`

```python
# model_utils.py - single source of truth
def load_models(paths: dict) -> tuple[Any, dict, Any]:
    """Load pickled model and encoders."""

def preprocess_features(df: pd.DataFrame, encoders: dict) -> pd.DataFrame:
    """Transform feature columns using label encoders."""

def preprocess_target(y: pd.Series, encoder: Any = None) -> tuple[np.ndarray, Any]:
    """Encode or decode target variable."""

def predict(features: pd.DataFrame, model: Any) -> np.ndarray:
    """Make predictions."""
```

### 6.2 Break DataPreprocessing into Focused Classes

```python
class DataCleaner:
    """Handle data cleaning operations."""

class FeatureTransformer:
    """Handle type coercion and imputation."""

class PreprocessingPipeline:
    """Orchestrate cleaning and transformation."""
```

### 6.3 Extract MIDI Analysis

```python
class MIDIStatistics:
    @staticmethod
    def extract_note_statistics(pm) -> dict:
        """Extract note-related statistics."""

    @staticmethod
    def extract_instrument_statistics(pm) -> dict:
        """Extract instrument-related statistics."""

    @classmethod
    def compute_all(cls, midi_file: str) -> dict:
        """Compute all statistics."""
```

### 6.4 Create Config Module

```python
# config.py
from pathlib import Path

DATA_PATH = Path("./data/statistics_v2.csv")
MODEL_PICKLE_PATH = Path("./midi_prediction_model.pkl")
LABEL_ENCODER_PATH = Path("./midi_prediction_label_encoders.pkl")
TARGET_ENCODER_PATH = Path("./midi_prediction_label_target_encoders.pkl")

CATEGORICAL_FEATURES = ["lyrics_bool"]
NUMERICAL_FEATURES = ["n_instruments", "number_of_instrument_families", ...]
COLUMNS_TO_DROP = ["md5", "instruments", "instrument_families", ...]
```

### 6.5 Fix midi_train.py Structure

```python
def main():
    """Main training pipeline."""
    # All current code here

if __name__ == "__main__":
    main()
```

---

## 7. Quick Wins (Easy Fixes)

1. Add `if __name__ == "__main__":` guards to midi_train.py and midi_prediction.py
2. Move all pickle path constants to config.py
3. Create model_utils.py with unified load/predict functions
4. Replace bare except clauses with specific exceptions
5. Remove duplicate imports and dead code

---

## 8. Issues by Severity

| Severity | Count | Examples |
|----------|-------|----------|
| Critical | 2 | Module-level execution in midi_train.py, midi_prediction.py |
| High | 3 | Code duplication (4+ copies), SRP violations |
| Medium | 4 | Hardcoded paths, large functions, bare excepts |
| Low | 5 | Naming issues, dead code, unused imports |

---

## Related Plans

- [Main Audit Plan](./code-audit-plan.md)
- [Main Package Audit](./audit-main-package.md)
