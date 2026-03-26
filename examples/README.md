# Examples

## Setup

```bash
pipenv install -e "."
```

## Available Examples

### Encode/Decode Roundtrip

Encodes a MIDI file (The Strokes - Reptilia) to text tokens, then decodes back to MIDI with a piano roll visualization.

```bash
pipenv run python examples/encode_decode.py
```

Output: `output/examples/encode_decode/`

### Generate New Music

Generates a multi-track piece (drums, bass, guitar) using the GPT-2 model, saves MIDI and piano roll.

```bash
pipenv run python examples/generate.py
```

Output: `output/examples/generation/`

### Track Statistics

Analyzes a MIDI file (The Strokes - Reptilia) and prints per-instrument statistics: note counts, coverage, start/end times.

```bash
pipenv run python examples/track_stats.py
```
