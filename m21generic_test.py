#!/usr/bin/env python

import pytest

from m21gen import SCORE_NAME, generate_code_for_music_structure


def parts_are_equal(part1, part2):
    """
    Compares two music21 Part objects for equivalence using elementsEqual.
    """
    if len(part1) != len(part2):
        return False

    for elem1, elem2 in zip(part1, part2):
        if not elem1.elementsEqual(elem2):
            return False

    return True


def measures_are_equal(measure1, measure2):
    """
    Compares two music21 Measure objects for equivalence in notes, rests, and chords.
    """
    for elem1, elem2 in zip(measure1.notesAndRests, measure2.notesAndRests):
        if type(elem1) != type(elem2):
            return False
        if hasattr(elem1, "pitch") and elem1.pitch != elem2.pitch:
            return False
        if elem1.duration != elem2.duration:
            return False
    return True


def execute_python_code(code_string):
    local_variables = {}
    exec(code_string, globals(), local_variables)
    return local_variables[SCORE_NAME]


def test_generated_code_matches_original():
    original_code = f"""
from music21 import *

{SCORE_NAME} = stream.Score()
part = stream.Part()
measure = stream.Measure()
cl = clef.TrebleClef()
measure.append(cl)
tm = tempo.MetronomeMark(number=120)
measure.append(tm)
ks = key.KeySignature(0)
measure.append(ks)
ts = meter.TimeSignature('4/4')
measure.append(ts)
n = note.Note('C4', duration=duration.Duration(1.0))
measure.append(n)
c = chord.Chord(['E4', 'G4'], duration=duration.Duration(1.0))
measure.append(c)
bl = bar.Barline('final')
measure.append(bl)
part.append(measure)
{SCORE_NAME}.append(part)
"""

    created_object = execute_python_code(original_code)
    generated_code = generate_code_for_music_structure(created_object)
    recreated_object = execute_python_code(generated_code)

    #    assert generated_code.strip() == original_code.strip()

    for part1, part2 in zip(recreated_object.parts, created_object.parts):
        for measure1, measure2 in zip(
            part1.getElementsByClass("Measure"), part2.getElementsByClass("Measure")
        ):
            assert measures_are_equal(
                measure1, measure2
            ), "Measures in the generated score do not match the expected measures"


def main():
    pytest.main([__file__])


if __name__ == "__main__":
    main()
