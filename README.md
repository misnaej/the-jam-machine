# The Jam Machine

**A Generative AI that composes MIDI music**

[![Try it on HuggingFace](https://img.shields.io/badge/🤗-Try%20Demo-yellow)](https://huggingface.co/spaces/JammyMachina/the-jam-machine-app)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

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
  │    5000 MIDI Songs ──► Encoder ──► Text Tokens ──► Train GPT-2 Model    │
  │                                                                          │
  │    Example text: "PIECE_START TRACK_START INST=DRUMS DENSITY=3          │
  │                   BAR_START NOTE_ON=36 TIME_DELTA=2 NOTE_OFF=36..."     │
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
  │    Generated Text ──► Decoder ──► MIDI File ──► Audio Preview           │
  │                                                                          │
  │    Download the MIDI and import into GarageBand, Ableton, FL Studio...  │
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

👉 **[Launch on HuggingFace](https://huggingface.co/spaces/JammyMachina/the-jam-machine-app)**

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
from the_jam_machine.preprocessing.load import LoadModel
from the_jam_machine.generating.generate import GenerateMidiText
from the_jam_machine.embedding.decoder import TextDecoder
from the_jam_machine.utils import get_miditok

# Load model
model, tokenizer = LoadModel(
    "JammyMachina/elec-gmusic-familized-model-13-12__17-35-53",
    from_huggingface=True
).load_model_and_tokenizer()

# Generate
generator = GenerateMidiText(model, tokenizer)
generator.generate_piece(
    instrument_list=["DRUMS", "4", "3"],  # Drums, Bass, Guitar
    density_list=[3, 2, 3],
    temperature_list=[0.7, 0.7, 0.7],
)

# Get the generated text
piece_text = generator.get_whole_piece_from_bar_dict()

# Convert to MIDI
decoder = TextDecoder(get_miditok())
decoder.get_midi(piece_text, filename="my_song.mid")
```

### Example Script

For more experimental generation:

```bash
pipenv run python examples/generation_playground.py
```

---

## Project Structure

```
the-jam-machine/
├── app/
│   └── playground.py          # Gradio web interface
├── src/the_jam_machine/
│   ├── embedding/             # MIDI ↔ text conversion
│   │   ├── encoder.py         # MIDI → text
│   │   └── decoder.py         # text → MIDI
│   ├── generating/            # Music generation
│   │   ├── generate.py        # Main orchestrator
│   │   ├── generation_engine.py  # GPT-2 interaction
│   │   ├── piece_builder.py   # Multi-track piece assembly
│   │   ├── track_builder.py   # Single track generation
│   │   └── prompt_handler.py  # Token prompt construction
│   ├── preprocessing/         # Model loading
│   └── training/              # Model training pipelines
├── examples/                  # Example scripts
├── plans/                     # Refactoring plans and audits
└── test/                      # Test suite
```

---

## Development

### Running Tests

```bash
pipenv run pytest test/
```

### Code Quality

```bash
# Lint
pipenv run ruff check src/ app/

# Format
pipenv run ruff format src/ app/
```

See [CLAUDE.md](CLAUDE.md) for development guidelines.

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

**Have Fun Making Music! 🎵**
