import gradio as gr
from load import LoadModel
from generate import GenerateMidiText
from constants import INSTRUMENT_CLASSES
from encoder import MIDIEncoder
from decoder import TextDecoder
from utils import get_miditok, index_has_substring
from playback import get_music
from matplotlib import pylab
import sys
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.modules["pylab"] = pylab

model_repo = "JammyMachina/elec-gmusic-familized-model-13-12__17-35-53"
model, tokenizer = LoadModel(
    model_repo, from_huggingface=True
).load_model_and_tokenizer()
genesis = GenerateMidiText(
    model,
    tokenizer,
)
miditok = get_miditok()
decoder = TextDecoder(miditok)


def plot_piano_roll(p_midi_note_list):
    piano_roll_fig = plt.figure()
    piano_roll_fig.tight_layout()
    piano_roll_fig.patch.set_alpha(0)
    note_time = []
    note_pitch = []
    for note in p_midi_note_list:
        note_time.append([note.start, note.end])
        note_pitch.append([note.pitch, note.pitch])

    plt.plot(
        np.array(note_time).T,
        np.array(note_pitch).T,
        color="orange",
        linewidth=1,
    )
    plt.xlabel("ticks")
    plt.axis("off")
    return piano_roll_fig


def define_prompt(state, genesis):
    if len(state) == 0:
        prompt = "PIECE_START"
    else:
        prompt = genesis.get_whole_piece_from_bar_dict()
    return prompt


def generator(regenerate, add_bars, temp, density, instrument, add_bar_count, state):

    inst = next(
        (inst for inst in INSTRUMENT_CLASSES if inst["name"] == instrument),
        {"family_number": "DRUMS"},
    )["family_number"]

    inst_index = index_has_substring(state, "INST=" + str(inst))

    # Regenerate
    if regenerate:
        state.pop(inst_index)
        genesis.delete_one_track(inst_index)
        generated_text = (
            genesis.get_whole_piece_from_bar_dict()
        )  # maybe not useful here
        inst_index = -1  # reset to last generated

    # Generate
    if not add_bars:
        # NEW TRACK
        prompt = define_prompt(state, genesis)
        generated_text = genesis.generate_one_new_track(
            inst, density, temp, input_prompt=prompt
        )
    else:
        # NEW BARS
        # genesis.generate_n_more_bars(add_bar_count, inst_index) # for only one instrument
        genesis.generate_n_more_bars(add_bar_count)  # for all instruments
        generated_text = genesis.get_whole_piece_from_bar_dict()

    decoder.get_midi(generated_text, "tmp/mixed.mid")
    _, mixed_audio = get_music("tmp/mixed.mid")

    inst_text = genesis.get_selected_track_as_text(inst_index)
    inst_midi_name = f"tmp/{instrument}.mid"
    decoder.get_midi(inst_text, inst_midi_name)
    inst_midi, inst_audio = get_music(inst_midi_name)
    piano_roll = plot_piano_roll(inst_midi.instruments[0].notes)
    state.append(inst_text)

    return inst_text, (44100, inst_audio), piano_roll, state, (44100, mixed_audio)


def instrument_row(default_inst):
    with gr.Row(variant="default", equal_height=True):
        with gr.Column(scale=1, min_width=10):
            inst = gr.Dropdown(
                [inst["name"] for inst in INSTRUMENT_CLASSES] + ["Drums"],
                value=default_inst,
                label="Instrument",
            )
            temp = gr.Number(value=0.75, label="Temperature")
            density = gr.Dropdown([0, 1, 2, 3], value=2, label="Density")
        with gr.Column(scale=3, min_width=100):
            with gr.Tab("Piano Roll"):
                piano_roll = gr.Plot(label="Piano Roll")
            with gr.Tab("Music text tokens"):
                output_txt = gr.Textbox(label="output", lines=6, max_lines=6)
        with gr.Column(scale=1, min_width=100):
            inst_audio = gr.Audio(label="Audio")
            regenerate = gr.Checkbox(value=False, label="Regenerate")
            add_bars = gr.Checkbox(value=False, label="Add Bars")
            add_bar_count = gr.Dropdown([1, 2, 4, 8], value=1, label="Add Bars")
            gen_btn = gr.Button("Generate")
            gen_btn.click(
                fn=generator,
                inputs=[
                    regenerate,
                    add_bars,
                    temp,
                    density,
                    inst,
                    add_bar_count,
                    state,
                ],
                outputs=[output_txt, inst_audio, piano_roll, state, mixed_audio],
            )


with gr.Blocks() as demo:
    state = gr.State([])
    mixed_audio = gr.Audio(label="Mixed Audio")
    instrument_row("Drums")
    instrument_row("Bass")
    instrument_row("Guitar")
    instrument_row("Piano")

demo.launch(debug=True)

""" 
TODO: regenerate and add bars button should not be activatblae together
TODO: make a global add bar button/tick box
TODO: row fuckikng height to fix
TODO: add a button to save the generated midi
TODO: improve the piano roll - maybe using librosa to check if it works/looks good already by default
TODO: adding a reset button to reload the model
TODO: update all piano_rolls, audio and text when adding bars
TODO: mapping instrument names to specific instrument and not random
"""
