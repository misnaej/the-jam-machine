# This streamlit app is used to predict the genre of a MIDI song based on a set of features
# It takes a pickled sklearn pipeline as input and predicts the genre of a MIDI song
# The user can upload a MIDI song and the app will predict the genre

import pickle
import os

import streamlit as st
import pandas as pd
import pretty_midi


def compute_list_average(l):
    """
    Given a list of numbers, compute the average.

    Parameters
    ----------
    l : list
        List of numbers.

    Returns
    -------
    average : float
        Average of the numbers in the list.
    """
    return sum(l) / len(l)


def categorize_midi_instrument(program_number):
    """
    Given a MIDI instrument program number, categorize it into a high-level
    instrument family.

    Parameters
    ----------
    program_number : int
        MIDI instrument program number.

    Returns
    -------
    instrument_family : str
        Name of the instrument family.
    """
    # See http://www.midi.org/techspecs/gm1sound.php

    if 0 <= program_number <= 7:
        return "Piano"
    elif 8 <= program_number <= 15:
        return "Chromatic Percussion"
    elif 16 <= program_number <= 23:
        return "Organ"
    elif 24 <= program_number <= 31:
        return "Guitar"
    elif 32 <= program_number <= 39:
        return "Bass"
    elif 40 <= program_number <= 47:
        return "Strings"
    elif 48 <= program_number <= 55:
        return "Ensemble"
    elif 56 <= program_number <= 63:
        return "Brass"
    elif 64 <= program_number <= 71:
        return "Reed"
    elif 72 <= program_number <= 79:
        return "Pipe"
    elif 80 <= program_number <= 87:
        return "Synth Lead"
    elif 88 <= program_number <= 95:
        return "Synth Pad"
    elif 96 <= program_number <= 103:
        return "Synth Effects"
    elif 104 <= program_number <= 111:
        return "Ethnic"
    elif 112 <= program_number <= 119:
        return "Percussive"
    elif 120 <= program_number <= 127:
        return "Sound Effects"


def compute_statistics(midi_file):
    """
    Given a path to a MIDI file, compute a dictionary of statistics about it

    Parameters
    ----------
    midi_file : str
        Path to a MIDI file.

    Returns
    -------
    statistics : dict
        Dictionary reporting the values for different events in the file.
    """
    pm = pretty_midi.PrettyMIDI(midi_file)
    # Extract informative events from the MIDI file
    statistics = {
        # track md5 hash name without extension
        "track_name": os.path.basename(midi_file).split(".")[0],
        # instruments
        "n_instruments": len(pm.instruments),
        "n_unique_instruments": len(set([i.program for i in pm.instruments])),
        "instruments": ", ".join([str(i.program) for i in pm.instruments]),
        "instrument_families": ", ".join(
            set([categorize_midi_instrument(i.program) for i in pm.instruments])
        ),
        "number_of_instrument_families": len(
            set([categorize_midi_instrument(i.program) for i in pm.instruments])
        ),
        # notes
        "n_notes": sum([len(i.notes) for i in pm.instruments]),
        "n_unique_notes": len(set([n.pitch for i in pm.instruments for n in i.notes])),
        "average_n_unique_notes_per_instrument": compute_list_average(
            [len(set([n.pitch for n in i.notes])) for i in pm.instruments]
        ),
        "average_note_duration": compute_list_average(
            [n.end - n.start for i in pm.instruments for n in i.notes]
        ),
        "average_note_velocity": compute_list_average(
            [n.velocity for i in pm.instruments for n in i.notes]
        ),
        "average_note_pitch": compute_list_average(
            [n.pitch for i in pm.instruments for n in i.notes]
        ),
        "range_of_note_pitches": (
            max([n.pitch for i in pm.instruments for n in i.notes])
            - min([n.pitch for i in pm.instruments for n in i.notes])
        ),
        "average_range_of_note_pitches_per_instrument": compute_list_average(
            [
                max([n.pitch for n in i.notes]) - (min([n.pitch for n in i.notes]))
                for i in pm.instruments
            ]
        ),
        "number_of_note_pitch_classes": len(
            set([n.pitch % 12 for i in pm.instruments for n in i.notes])
        ),
        "average_number_of_note_pitch_classes_per_instrument": compute_list_average(
            [len(set([n.pitch % 12 for n in i.notes])) for i in pm.instruments]
        ),
        "number_of_octaves": len(
            set([n.pitch // 12 for i in pm.instruments for n in i.notes])
        ),
        "average_number_of_octaves_per_instrument": compute_list_average(
            [len(set([n.pitch // 12 for n in i.notes])) for i in pm.instruments]
        ),
        "number_of_notes_per_second": len([n for i in pm.instruments for n in i.notes])
        / pm.get_end_time(),
        "shortest_note_length": min(
            [n.end - n.start for i in pm.instruments for n in i.notes]
        ),
        "longest_note_length": max(
            [n.end - n.start for i in pm.instruments for n in i.notes]
        ),
        # key signatures
        "main_key_signature": [k.key_number for k in pm.key_signature_changes][
            0
        ],  # hacky
        "n_key_changes": len(pm.key_signature_changes),
        # tempo
        "n_tempo_changes": len(pm.get_tempo_changes()[1]),
        "tempo_estimate": round(pm.estimate_tempo()),  # weird results
        # time signatures
        "main_time_signature": [
            str(ts.numerator) + "/" + str(ts.denominator)
            for ts in pm.time_signature_changes
        ][
            0
        ],  # hacky
        "n_time_signature_changes": len(pm.time_signature_changes),
        # track length
        "track_length_in_seconds": round(pm.get_end_time()),
        # lyrics
        "lyrics_nb_words": len([l.text for l in pm.lyrics]),
        "lyrics_unique_words": len(set([l.text for l in pm.lyrics])),
        "lyrics_bool": len(pm.lyrics) > 0,
    }
    return statistics


if __name__ == "__main__":
    st.title("Music Genre Prediction")
    st.subheader("Upload a MIDI file to predict its genre:")

    # Let user upload midi file
    uploaded_file = st.file_uploader("Choose a MIDI file", type="mid")

    # Do prediction if user clicks on predict button
    if st.button("Predict genre"):
        # Compute statistics on the midi file
        if uploaded_file is not None:
            try:
                statistics = compute_statistics(uploaded_file)
                # Convert statistics to dataframe
                statistics = pd.DataFrame(statistics, index=[0])
                # Load the pipeline
                pipeline = pickle.load(open("pipeline.pkl", "rb"))
                # Predict genre
                prediction = pipeline.predict(statistics)
                # Display prediction
                st.subheader("Predicted genre:")
                st.write(prediction)
            except Exception:
                st.write("Error: invalid MIDI file")
        else:
            st.write("No file uploaded")
