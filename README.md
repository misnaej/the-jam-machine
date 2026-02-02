# The-Jam-Machine - a Generative AI composing MIDI music

## Summary

The-Jam-Machine is a source of inspiration for beginner or more proficient musicians. Based on a GPT (Generative Pretrained-Transformer) architecture, and trained on the text transcriptions of about 5000 MIDI songs, it can generate harmonious MIDI sequences.

You can check the App on [HuggingFace](https://huggingface.co/spaces/JammyMachina/the-jam-machine-app), with which you can generate 8 bars of downloadable MIDI music with up to 3 instruments playing in harmony.
_______________

## [Presentation](https://pitch.com/public/417162a8-88b0-4472-a651-c66bb89428be)

_______________

## Contributors

Jean Simonnet: [Github](https://github.com/misnaej) / [Linkedin](https://www.linkedin.com/in/jeansimonnet/) \
Louis Demetz:  [Github](https://github.com/louis-demetz) / [Linkedin](https://www.linkedin.com/in/ldemetz/) \
Halid Bayram:  [Github](https://github.com/m41w4r3exe) / [Linkedin](https://www.linkedin.com/in/halid-bayram-6b9ba861/)

_______________

## Setting up the Jam-Machine on your computer

This works for MacOS 12.6

### 1. Install fluidsynth

The Jam-Machine requires Fluidsynth, a software synthetizer.\
Make sure to install it on your system, and fopr this please check the github repo [here](https://github.com/FluidSynth/fluidsynth/wiki/Download).\
E.g.: with Mac OS X and Homebrew, run `brew install fluidsynth`

#### - if you encounter problems with fluidsynth while running the python code - check [this](https://github.com/nwhitehead/pyfluidsynth/issues/40) -

### 2. Clone the repository

```bash
git clone git@github.com:misnaej/the-jam-machine.git
cd the-jam-machine
```

### 3. Install the dependencies

We use [pipenv](https://pypi.org/project/pipenv/) for dependency management.

```bash
# Install pipenv if not already installed
pip install pipenv

# Install dependencies (including dev/test dependencies)
pipenv install -e ".[ci]"

# Activate the virtual environment
pipenv shell
```

Or use the setup script:

```bash
./scripts/setup-env.sh
```

### 4. Test the Jam-Machine

Run the tests from the project root:

```bash
pipenv run pytest test/
```

This tests encoding, generation, decoding, and consistency.

## Making Music with the Jam-Machine

### 1. With the Gradio app

Try it on [HuggingFace](https://huggingface.co/spaces/JammyMachina/the-jam-machine-app) first - you can generate 8 bars of MIDI music with up to 3 instruments playing in harmony.

To run locally:

```bash
pipenv run python app/playground.py
```

Then open the URL displayed in your terminal.

### 2. With the example script

For more experimental generation with longer tracks:

```bash
pipenv run python examples/generation_playground.py
```

Check out the code in `examples/generation_playground.py` for inspiration.

**Have Fun!**
