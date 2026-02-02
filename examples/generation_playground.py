"""Example script demonstrating MIDI generation with The Jam Machine."""

from jammy.embedding.decoder import TextDecoder
from jammy.generating.generate import GenerateMidiText
from jammy.generating.playback import get_music
from jammy.generating.utils import (
    WriteTextMidiToFile,
    check_if_prompt_inst_in_tokenizer_vocab,
    define_generation_dir,
    plot_piano_roll,
)
from jammy.preprocessing.load import LoadModel
from jammy.utils import get_miditok

# Instrument family mapping:
# DRUMS = drums, 0 = piano, 1 = chromatic percussion, 2 = organ, 3 = guitar,
# 4 = bass, 5 = strings, 6 = ensemble, 7 = brass, 8 = reed, 9 = pipe,
# 10 = synth lead, 11 = synth pad, 12 = synth effects, 13 = ethnic,
# 14 = percussive, 15 = sound effects


def main() -> None:
    """Run the MIDI generation example."""
    # Configuration
    n_files_to_generate = 1
    temperatures_to_try = [0.7]
    use_familized_model = True

    if use_familized_model:
        model_repo = "JammyMachina/elec-gmusic-familized-model-13-12__17-35-53"
        n_bar_generated = 8
        instrument_prompt_list = ["DRUMS", "4", "3"]
        density_list = [3, 2, 2]
    else:
        model_repo = "misnaej/the-jam-machine"
        n_bar_generated = 8
        instrument_prompt_list = ["30"]
        density_list = [3]

    # Define generation directory
    generated_sequence_files_path = define_generation_dir(f"midi/generated/{model_repo}")

    # Load model and tokenizer
    model, tokenizer = LoadModel(model_repo, from_huggingface=True).load_model_and_tokenizer()

    # Validate prompt instruments
    check_if_prompt_inst_in_tokenizer_vocab(tokenizer, instrument_prompt_list)

    for temperature in temperatures_to_try:
        print(f"================= TEMPERATURE {temperature} =======================")  # noqa: T201
        for _ in range(n_files_to_generate):
            print("========================================")  # noqa: T201

            # Instantiate generator
            piece_by_track: list[str] = []
            generate_midi = GenerateMidiText(model, tokenizer, piece_by_track)
            generate_midi.set_nb_bars_generated(n_bars=n_bar_generated)

            # Generate piece
            generate_midi.generate_piece(
                instrument_prompt_list,
                density_list,
                [temperature for _ in density_list],
            )

            generate_midi.generated_piece = generate_midi.get_whole_piece_from_bar_dict()

            # Print generated sequence
            print("=========================================")  # noqa: T201
            print(generate_midi.generated_piece)  # noqa: T201
            print("=========================================")  # noqa: T201

            # Write to JSON file
            filename = WriteTextMidiToFile(
                generate_midi,
                generated_sequence_files_path,
            ).text_midi_to_file()

            # Decode to MIDI
            decode_tokenizer = get_miditok()
            TextDecoder(decode_tokenizer, use_familized_model).get_midi(
                generate_midi.generated_piece, filename=filename.split(".")[0] + ".mid"
            )

            # Generate piano roll visualization
            inst_midi, _ = get_music(f"{filename.split('.')[0]}.mid")
            piano_roll_fig = plot_piano_roll(inst_midi)
            piano_roll_fig.savefig(filename.split(".")[0] + "_piano_roll.png", bbox_inches="tight")
            piano_roll_fig.clear()

            print("Et voilà! Your MIDI file is ready! GO JAM!")  # noqa: T201


if __name__ == "__main__":
    main()
