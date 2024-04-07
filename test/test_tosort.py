import os
import subprocess

from the_jam_machine.embedding.decoder import TextDecoder
from the_jam_machine.embedding.encoder import (
    from_MIDI_to_sectionned_text,
    readFromFile,
    writeToFile,
)
from the_jam_machine.generating.generate import GenerateMidiText
from the_jam_machine.generating.playback import get_music
from the_jam_machine.generating.utils import (
    WriteTextMidiToFile,
    check_if_prompt_inst_in_tokenizer_vocab,
    define_generation_dir,
    plot_piano_roll,
)
from the_jam_machine.preprocessing.load import LoadModel
from the_jam_machine.utils import get_miditok

USE_FAMILIZED_MODEL = True
force_sequence_length = True

DEVICE = "cpu"
model_repo = "JammyMachina/elec-gmusic-familized-model-13-12__17-35-53"
n_bar_generated = 8

# define test directory
test_dir = define_generation_dir("test/results")


def test_generate():
    """Generate a MIDI_text sequence"""
    # define generation parameters
    temperature = 0.7

    instrument_promt_list = ["DRUMS", "4", "3"]
    # DRUMS = drums, 0 = piano, 1 = chromatic percussion, 2 = organ, 3 = guitar, 4 = bass, 5 = strings, 6 = ensemble, 7 = brass, 8 = reed, 9 = pipe, 10 = synth lead, 11 = synth pad, 12 = synth effects, 13 = ethnic, 14 = percussive, 15 = sound effects
    density_list = [3, 2, 3]

    # load model and tokenizer
    model, tokenizer = LoadModel(
        model_repo, from_huggingface=True
    ).load_model_and_tokenizer()

    # does the prompt make sense
    check_if_prompt_inst_in_tokenizer_vocab(tokenizer, instrument_promt_list)

    print(f"================= TEMPERATURE {temperature} =======================")

    # 1 - instantiate
    piece_by_track = []  # reset the piece by track
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
    print("=========================================")
    print(f"{generate_midi.generated_piece[:1000]} ...")
    print("=========================================")

    filename = WriteTextMidiToFile(
        generate_midi,
        test_dir,
    ).text_midi_to_file()

    return generate_midi, filename


def check_for_duplicated_subsequent_tokens(generated_text):
    """Check if there are duplicated tokens in the generated sequence"""
    for i, text in enumerate(generated_text.split(" ")):
        if (
            i < len(generated_text.split(" ")) - 1
            and text == generated_text.split(" ")[i + 1]
        ):
            print(f"DUPLICATED TOKENS {text} in position {i}")
            print(f"{generated_text.split(' ')[i - min([i,3]): i + 3]}")


def test_decode():
    filename = "test/test_decode.json"

    filename = filename.split(".")[0]  # remove extension

    generated_piece = readFromFile(f"{filename}.json", isJSON=True)["generated_midi"]

    decode_tokenizer = get_miditok()
    TextDecoder(decode_tokenizer, USE_FAMILIZED_MODEL).get_midi(
        generated_piece, filename=f"{filename}.mid"
    )
    inst_midi, _ = get_music(f"{filename}.mid")
    piano_roll_fig = plot_piano_roll(inst_midi)
    piano_roll_fig.savefig(f"{filename}_piano_roll.png", bbox_inches="tight")
    piano_roll_fig.clear()

    return filename


def test_encode():
    midi_filename = "midi/the_strokes-reptilia"

    piece_text = from_MIDI_to_sectionned_text(
        f"{midi_filename}", familized=USE_FAMILIZED_MODEL
    )
    print("=========================================")
    print(piece_text)
    writeToFile(f"{midi_filename}_from_midi.txt", piece_text)
    return piece_text


def simplify_events_for_comparison(generated_event, encoded_event):
    """Simplifies the 'NOTE' events, byt getting rid of the level of the note (e.g. 'NOTE=60' becomes 'NOTE')
    Why: because when the sequence is encoded as midi with pretty midi, the order of sequences of NOTE_OFF or NOTE_ON can be changed
    This does not changes the music, but then the text sequences will be different and won't match"""
    if "NOTE" in generated_event:
        generated_word = generated_event.split("=")[0]
    else:
        generated_word = generated_event

    if "NOTE" in encoded_event:
        encoded_word = encoded_event.split("=")[0]
    else:
        encoded_word = encoded_event

    return generated_word, encoded_word


def check_sequence_word_by_word(generated_text, encoded_text):
    """Check if the generated MIDI_text sequence and the encoded MIDI_text sequence are the same word by word"""
    generated_text = generated_text.split(" ")
    encoded_text = encoded_text.split(" ")
    absolutely_similar = True
    for i in range(len(generated_text)):
        generated_word, encoded_word = simplify_events_for_comparison(
            generated_text[i], encoded_text[i]
        )

        if generated_word != encoded_word:
            absolutely_similar = False
            print(
                f"Word {i} is different - Generated: {generated_text[i]} vs Encoded: {encoded_text[i]}"
            )
            print(f"generated: {generated_text[i - min([i, 4]) : i + 3]}")
            print(f"encoded: {encoded_text[i - min([i, 4]) : i + 3]}")
            print("------------------")
            # raise ValueError("Generated and encoded MIDI_text sequences are different")

    return absolutely_similar


def test_compare_generated_encoded(generated_text, encoded_text):
    """Compare the generated MIDI_text sequence and the encoded MIDI_text sequence"""
    absolutely_similar = False
    if generated_text == encoded_text:
        absolutely_similar = True
    else:
        similar_length = len(generated_text.split(" ")) == len(encoded_text.split(" "))

    if not absolutely_similar and similar_length:
        print(
            f"Lengths of generated and encoded sequences are the same: {len(encoded_text.split(' '))} words"
        )
        absolutely_similar = check_sequence_word_by_word(generated_text, encoded_text)

    if not absolutely_similar and not similar_length:
        print(
            f"Lengths of generated and encoded sequences are different: {len(generated_text.split(' '))} vs {len(encoded_text.split(' '))} words"
        )
        print("generated:")
        print(f"beginning: {generated_text[:120]}")
        print(f"end: {generated_text[-120:]}")
        print("encoded:")
        print(f"beginning: {encoded_text[:120]}")
        print(f"end: {encoded_text[-120:]}")
        print("------------------")
        # raise ValueError("Generated and encoded MIDI_text sequences are different")

    if absolutely_similar:
        print("Generated and encoded MIDI_text sequences are the same")


def test_gradio():
    # current_wd = os.getcwd()
    os.chdir("./source")
    subprocess.run(["gradio playground.py"], shell=True)
    # os.chdir(current_wd)
