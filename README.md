# The Jam Machine

**A Generative AI that composes MIDI music**

[![Try it on HuggingFace](https://img.shields.io/badge/🤗-Try%20Demo-yellow)](https://huggingface.co/spaces/JammyMachina/the-jam-machine-app)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Docstring Coverage](.githooks/badges/docstring-coverage.svg)
![Security](.githooks/badges/bandit.svg)
![Claude Code](https://img.shields.io/badge/Claude_Code-555?logo=claude)

---

## What is The Jam Machine?

The Jam Machine is an AI music composition tool that generates harmonious MIDI sequences. It's designed for musicians (beginners and professionals) looking for inspiration or backing tracks.

**Key Features:**
- Generate 8+ bars of multi-instrument MIDI music
- Control instruments, note density, and creativity level
- Download MIDI files to edit in your favorite DAW
- Runs locally or via web interface

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           THE JAM MACHINE                                   │
└─────────────────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  TRAINING (one-time, already done)                                       │
  │                                                                          │
  │    5000 MIDI Songs ──► Encoder ──► Text Tokens ──► Train GPT-2 Model     │
  │                                                                          │
  │    Example text: "PIECE_START TRACK_START INST=DRUMS DENSITY=3           │
  │                   BAR_START NOTE_ON=36 TIME_DELTA=2 NOTE_OFF=36..."      │
  └──────────────────────────────────────────────────────────────────────────┘

                                     │
                                     ▼

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  GENERATION (what happens when you use it)                               │
  │                                                                          │
  │                    ┌─────────────────┐                                   │
  │    Your Input ───► │   GPT-2 Model   │ ───► Generated Text               │
  │                    └─────────────────┘                                   │
  │                                                                          │
  │    • Instrument (Drums, Bass, Lead...)                                   │
  │    • Density (how many notes: 1-3)                                       │
  │    • Temperature (creativity: 0.1-1.0)                                   │
  └──────────────────────────────────────────────────────────────────────────┘

                                     │
                                     ▼

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  OUTPUT                                                                  │
  │                                                                          │
  │    Generated Text ──► Decoder ──► MIDI File ──► Audio Preview            │
  │                                                                          │
  │    Download the MIDI and import into GarageBand, Ableton, FL Studio...   │
  └──────────────────────────────────────────────────────────────────────────┘
```

### The Magic: Text-Based Music

The Jam Machine converts music into text, like a language:

| Musical Concept | Text Representation |
|-----------------|---------------------|
| Start of piece | `PIECE_START` |
| New instrument track | `TRACK_START INST=DRUMS` |
| Note density | `DENSITY=3` |
| Play a note | `NOTE_ON=60` (middle C) |
| Wait 1 beat | `TIME_DELTA=4` |
| Release note | `NOTE_OFF=60` |
| End of bar | `BAR_END` |

The GPT-2 model learns patterns from 5000 songs and generates new, coherent sequences.

---

## Quick Start

### Option 1: Try Online (No Installation)

**[Launch on HuggingFace](https://huggingface.co/spaces/JammyMachina/the-jam-machine-app)**

### Option 2: Local Installation

#### Prerequisites

- **Python 3.11+**
- **FluidSynth** (audio synthesis):
  ```bash
  # macOS
  brew install fluidsynth

  # Ubuntu/Debian
  sudo apt install fluidsynth

  # Windows - see https://github.com/FluidSynth/fluidsynth/wiki/Download
  ```

#### Installation

```bash
# Clone the repository
git clone https://github.com/misnaej/the-jam-machine.git
cd the-jam-machine

# Option A: Use setup script (recommended)
./scripts/setup-env.sh

# Option B: Manual setup
pip install pipenv
pipenv install -e ".[ci]"
pipenv shell
```

#### Run the App

```bash
pipenv run python app/playground.py
```

Open the URL shown in your terminal (usually http://localhost:7860).

---

## Usage Guide

### Web Interface

1. **Choose an instrument** for each track (Drums, Bass, Lead, etc.)
2. **Set creativity** (temperature) - higher = more experimental
3. **Set density** - how many notes per bar
4. **Click Generate** - wait a few seconds
5. **Listen** to the preview and view the piano roll
6. **Download** the MIDI file

### Python API

```python
from jammy.preprocessing.load import LoadModel
from jammy.generating.config import GenerationConfig, TrackConfig
from jammy.generating.generate import GenerateMidiText
from jammy.embedding.decoder import TextDecoder
from jammy.utils import get_miditok

# Load model
model, tokenizer = LoadModel(
    "JammyMachina/elec-gmusic-familized-model-13-12__17-35-53",
    from_huggingface=True
).load_model_and_tokenizer()

# Generate
tracks = [
    TrackConfig(instrument="DRUMS", density=3, temperature=0.7),
    TrackConfig(instrument="4", density=2, temperature=0.7),   # Bass
    TrackConfig(instrument="3", density=2, temperature=0.7),   # Guitar
]
generator = GenerateMidiText(model, tokenizer, config=GenerationConfig(n_bars=8))
generator.generate_piece(tracks)

# Get the generated text and convert to MIDI
piece_text = generator.get_piece_text()
decoder = TextDecoder(get_miditok())
decoder.get_midi(piece_text, filename="my_song.mid")
```

### Examples

```bash
# Generate new music
pipenv run python examples/generate.py

# Encode/decode a MIDI file (roundtrip demo)
pipenv run python examples/encode_decode.py
```

Output goes to `output/examples/`. See [examples/README.md](examples/README.md) for details.

---

## Project Structure

```
the-jam-machine/
├── app/
│   └── playground.py          # Gradio web interface
├── src/jammy/                 # Main package
│   ├── embedding/             # MIDI ↔ text conversion
│   ├── generating/            # Music generation (GPT-2)
│   ├── preprocessing/         # Model loading
│   ├── midi_codec.py          # Token encoding/decoding
│   ├── file_utils.py          # File I/O utilities
│   ├── tokens.py              # Token vocabulary constants
│   └── constants.py           # Configuration constants
├── examples/                  # Runnable example scripts
├── test/                      # Test suite
├── .claude/                   # Claude Code config (agents, skills, hooks)
└── .plans/                    # Refactoring plans and audits
```

---

## Development

### Running Tests

```bash
pipenv run pytest test/ -v
```

### Code Quality

```bash
# Lint
pipenv run ruff check src/ test/ app/ examples/

# Format
pipenv run ruff format src/ test/ app/ examples/

# Security audit
pipenv run pip-audit
```

### Contributing with Claude Code

Development of this repository is supported by [Claude Code](https://claude.ai/claude-code). The project includes custom skills and agents for a structured workflow:

| Skill | What it does |
|-------|-------------|
| `/check` | Run tests + lint + format |
| `/lint` | Run ruff check + format |
| `/commit` | Lint, commit, and push to current branch |
| `/review` | Run design + docs review agents |
| `/pr` | Generate squash merge message |

**Workflow:**
1. Create a feature branch from `main`
2. Make changes, run `/check` to verify
3. Run `/commit` to lint, commit, and push
4. Create a PR, run `/pr` for review and merge message
5. Squash and merge into `main`

See [CLAUDE.md](CLAUDE.md) for full development guidelines.

---

## Contributors

- **Jean Simonnet**: [GitHub](https://github.com/misnaej) / [LinkedIn](https://www.linkedin.com/in/jeansimonnet/)
- **Louis Demetz**: [GitHub](https://github.com/louis-demetz) / [LinkedIn](https://www.linkedin.com/in/ldemetz/)
- **Halid Bayram**: [GitHub](https://github.com/m41w4r3exe) / [LinkedIn](https://www.linkedin.com/in/halid-bayram-6b9ba861/)

---

## Resources

- **[Live Demo](https://huggingface.co/spaces/JammyMachina/the-jam-machine-app)**
- **[Presentation](https://pitch.com/public/417162a8-88b0-4472-a651-c66bb89428be)**
- **[Model on HuggingFace](https://huggingface.co/JammyMachina/elec-gmusic-familized-model-13-12__17-35-53)**

---

## Troubleshooting

### FluidSynth Issues

If you encounter errors with audio playback:
- Check [this guide](https://github.com/nwhitehead/pyfluidsynth/issues/40)
- Ensure FluidSynth is in your PATH
- On macOS: `brew reinstall fluidsynth`

### Model Download Issues

The model (~500MB) downloads automatically on first run. If it fails:
- Check your internet connection
- Try: `huggingface-cli login` if you have rate limits

---

## License

MIT License - feel free to use, modify, and distribute.
