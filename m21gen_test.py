# test_music_script.py

from m21gen import generate_code_for_music_structure
from music21 import stream, note, chord

def test_generate_code_for_note():
    s = stream.Stream()
    s.append(note.Note("C4"))
    generated_code = generate_code_for_music_structure(s)
    assert "note.Note('C4'" in generated_code

def test_generate_code_for_chord():
    s = stream.Stream()
    s.append(chord.Chord(["E4", "G4"]))
    generated_code = generate_code_for_music_structure(s)
    assert "chord.Chord(['E4', 'G4'" in generated_code

