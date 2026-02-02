"""Tests for MIDI generation, encoding, and decoding pipeline."""

from __future__ import annotations

import os
import subprocess

from jammy.embedding.decoder import TextDecoder
from jammy.embedding.encoder import from_midi_to_sectioned_text
from jammy.generating.generate import GenerateMidiText
from jammy.generating.playback import get_music
from jammy.generating.utils import (
    WriteTextMidiToFile,
    check_if_prompt_inst_in_tokenizer_vocab,
    define_generation_dir,
    plot_piano_roll,
)
from jammy.preprocessing.load import LoadModel
from jammy.utils import get_miditok, read_from_file, write_to_file

USE_FAMILIZED_MODEL = True
force_sequence_length = True

DEVICE = "cpu"
model_repo = "JammyMachina/elec-gmusic-familized-model-13-12__17-35-53"
n_bar_generated = 8

# define test directory
test_dir = define_generation_dir("test/results")


def test_generate() -> tuple[GenerateMidiText, str]:
    """Generate a MIDI_text sequence.

    Returns:
        Tuple of the GenerateMidiText instance and the output filename.
    """
    # define generation parameters
    temperature = 0.7

    # DRUMS = drums, 0 = piano, 1 = chromatic percussion, 2 = organ, 3 = guitar,
    # 4 = bass, 5 = strings, 6 = ensemble, 7 = brass, 8 = reed, 9 = pipe,
    # 10 = synth lead, 11 = synth pad, 12 = synth effects, 13 = ethnic,
    # 14 = percussive, 15 = sound effects
    instrument_promt_list = ["DRUMS", "4", "3"]
    density_list = [3, 2, 3]

    # load model and tokenizer
    model, tokenizer = LoadModel(model_repo, from_huggingface=True).load_model_and_tokenizer()

    # does the prompt make sense
    check_if_prompt_inst_in_tokenizer_vocab(tokenizer, instrument_promt_list)

    print(f"================= TEMPERATURE {temperature} =======================")  # noqa: T201

    # 1 - instantiate
    piece_by_track: list[str] = []  # reset the piece by track
    generate_midi = GenerateMidiText(model, tokenizer, piece_by_track)
    # 0 - set the n_bar for this model
    generate_midi.set_nb_bars_generated(n_bars=n_bar_generated)
    # 1 - defines the instruments, densities and temperatures
    # 2 - generate the first 8 bars for each instrument
    generate_midi.generate_piece(
        instrument_promt_list,
        density_list,
        [temperature for _ in density_list],
    )
    generate_midi.generated_piece = generate_midi.get_whole_piece_from_bar_dict()

    # print the generated sequence in terminal
    print("=========================================")  # noqa: T201
    print(f"{generate_midi.generated_piece[:1000]} ...")  # noqa: T201
    print("=========================================")  # noqa: T201

    filename = WriteTextMidiToFile(
        generate_midi,
        test_dir,
    ).text_midi_to_file()

    return generate_midi, filename


def check_for_duplicated_subsequent_tokens(generated_text: str) -> None:
    """Check if there are duplicated tokens in the generated sequence.

    Args:
        generated_text: The generated MIDI text to check.
    """
    tokens = generated_text.split(" ")
    for i, text in enumerate(tokens):
        if i < len(tokens) - 1 and text == tokens[i + 1]:
            print(f"DUPLICATED TOKENS {text} in position {i}")  # noqa: T201
            print(f"{tokens[i - min([i, 3]) : i + 3]}")  # noqa: T201


def test_decode() -> str:
    """Decode a generated MIDI text file back to MIDI format.

    Returns:
        The filename (without extension) of the decoded file.
    """
    filename = "test/test_decode.json"

    filename = filename.split(".")[0]  # remove extension

    generated_piece = read_from_file(f"{filename}.json", is_json=True)["generated_midi"]

    decode_tokenizer = get_miditok()
    TextDecoder(decode_tokenizer, USE_FAMILIZED_MODEL).get_midi(
        generated_piece, filename=f"{filename}.mid"
    )
    inst_midi, _ = get_music(f"{filename}.mid")
    piano_roll_fig = plot_piano_roll(inst_midi)
    piano_roll_fig.savefig(f"{filename}_piano_roll.png", bbox_inches="tight")
    piano_roll_fig.clear()

    return filename


def test_encode() -> str:
    """Encode a MIDI file to text representation.

    Returns:
        The encoded piece as text.
    """
    midi_filename = "midi/the_strokes-reptilia"

    piece_text = from_midi_to_sectioned_text(f"{midi_filename}", familized=USE_FAMILIZED_MODEL)
    print("=========================================")  # noqa: T201
    print(piece_text)  # noqa: T201
    write_to_file(f"{midi_filename}_from_midi.txt", piece_text)
    return piece_text


def simplify_events_for_comparison(generated_event: str, encoded_event: str) -> tuple[str, str]:
    """Simplify NOTE events for comparison by removing note values.

    When the sequence is encoded as midi with pretty midi, the order of sequences
    of NOTE_OFF or NOTE_ON can be changed. This does not change the music, but
    then the text sequences will be different and won't match.

    Args:
        generated_event: The generated event token.
        encoded_event: The encoded event token.

    Returns:
        Tuple of simplified event names (without note values).
    """
    generated_word = generated_event.split("=")[0] if "NOTE" in generated_event else generated_event
    encoded_word = encoded_event.split("=")[0] if "NOTE" in encoded_event else encoded_event

    return generated_word, encoded_word


def check_sequence_word_by_word(generated_text: str, encoded_text: str) -> bool:
    """Check if generated and encoded sequences match word by word.

    Args:
        generated_text: The generated MIDI text sequence.
        encoded_text: The encoded MIDI text sequence.

    Returns:
        True if sequences are absolutely similar, False otherwise.
    """
    generated_tokens = generated_text.split(" ")
    encoded_tokens = encoded_text.split(" ")
    absolutely_similar = True
    for i in range(len(generated_tokens)):
        generated_word, encoded_word = simplify_events_for_comparison(
            generated_tokens[i], encoded_tokens[i]
        )

        if generated_word != encoded_word:
            absolutely_similar = False
            print(  # noqa: T201
                f"Word {i} is different - Generated: {generated_tokens[i]} "
                f"vs Encoded: {encoded_tokens[i]}"
            )
            print(f"generated: {generated_tokens[i - min([i, 4]) : i + 3]}")  # noqa: T201
            print(f"encoded: {encoded_tokens[i - min([i, 4]) : i + 3]}")  # noqa: T201
            print("------------------")  # noqa: T201

    return absolutely_similar


def test_compare_generated_encoded(generated_text: str, encoded_text: str) -> None:
    """Compare generated MIDI text sequence with encoded sequence.

    Args:
        generated_text: The generated MIDI text sequence.
        encoded_text: The encoded MIDI text sequence.
    """
    absolutely_similar = False
    similar_length = False
    if generated_text == encoded_text:
        absolutely_similar = True
    else:
        similar_length = len(generated_text.split(" ")) == len(encoded_text.split(" "))

    if not absolutely_similar and similar_length:
        gen_len = len(encoded_text.split(" "))
        print(  # noqa: T201
            f"Lengths of generated and encoded sequences are the same: {gen_len} words"
        )
        absolutely_similar = check_sequence_word_by_word(generated_text, encoded_text)

    if not absolutely_similar and not similar_length:
        gen_word_count = len(generated_text.split(" "))
        enc_word_count = len(encoded_text.split(" "))
        print(  # noqa: T201
            f"Lengths of generated and encoded sequences are different: "
            f"{gen_word_count} vs {enc_word_count} words"
        )
        print("generated:")  # noqa: T201
        print(f"beginning: {generated_text[:120]}")  # noqa: T201
        print(f"end: {generated_text[-120:]}")  # noqa: T201
        print("encoded:")  # noqa: T201
        print(f"beginning: {encoded_text[:120]}")  # noqa: T201
        print(f"end: {encoded_text[-120:]}")  # noqa: T201
        print("------------------")  # noqa: T201

    if absolutely_similar:
        print("Generated and encoded MIDI_text sequences are the same")  # noqa: T201


def test_gradio() -> None:
    """Test running the Gradio playground application."""
    os.chdir("./source")
    subprocess.run(["gradio", "playground.py"], check=False)  # noqa: S607
