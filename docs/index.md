---
layout: default
title: The Jam Machine
---

# The Jam Machine

A generative AI music composition tool that creates MIDI sequences using a GPT-2 model trained on ~5,000 MIDI songs.

[Try the Demo](https://huggingface.co/spaces/JammyMachina/the-jam-machine-app){: .btn }
[View on GitHub](https://github.com/misnaej/the-jam-machine){: .btn }

---

## How It Works

Music is converted to text, like a language. A GPT-2 model learns patterns from thousands of songs and generates new, coherent sequences.

```
5000 MIDI Songs ──► Encoder ──► Text Tokens ──► Train GPT-2

Your Input ──► GPT-2 Model ──► Generated Text ──► Decoder ──► MIDI File
```

### The Token Vocabulary

| Musical Concept | Text Representation |
|-----------------|---------------------|
| Start of piece | `PIECE_START` |
| New instrument track | `TRACK_START INST=DRUMS` |
| Note density | `DENSITY=3` |
| Play a note | `NOTE_ON=60` (middle C) |
| Wait 1 beat | `TIME_DELTA=4` |
| Release note | `NOTE_OFF=60` |
| End of bar | `BAR_END` |

The model's vocabulary has ~300 tokens covering 128 MIDI pitches, 16 instrument families, time steps, and structural markers.

---

## Documentation

- **[Encoding & Decoding Guide](encoding-decoding)** — How MIDI files become text tokens and back. The full pipeline, token format, quantization trade-offs, and a worked example using The Strokes - Reptilia.
- **[Embedding Explorer](exploring_the_embedding.html)** — Visualizations of the model's learned token embeddings, attention patterns, and next-token predictions. Compares trained vs untrained model.

---

## Quick Start

See the [README](https://github.com/misnaej/the-jam-machine#quick-start) for installation and usage instructions.

## Resources

- [Live Demo on HuggingFace](https://huggingface.co/spaces/JammyMachina/the-jam-machine-app)
- [Model on HuggingFace](https://huggingface.co/JammyMachina/elec-gmusic-familized-model-13-12__17-35-53)
- [Project Presentation](https://pitch.com/public/417162a8-88b0-4472-a651-c66bb89428be)
