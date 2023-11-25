#!/usr/bin/env python

from music21 import stream, note, chord, duration, meter, clef, key, bar, tempo

def generate_code_for_element(element):
    code_lines = []
    if isinstance(element, note.Note):
        code_lines.append(f"n = note.Note('{element.pitch}', duration=duration.Duration({element.duration.quarterLength}))")
        code_lines.append("measure.append(n)")
    elif isinstance(element, chord.Chord):
        pitches = ', '.join([f"'{p}'" for p in element.pitches])
        code_lines.append(f"c = chord.Chord([{pitches}], duration=duration.Duration({element.duration.quarterLength}))")
        code_lines.append("measure.append(c)")
    elif isinstance(element, meter.TimeSignature):
        code_lines.append(f"ts = meter.TimeSignature('{element.ratioString}')")
        code_lines.append("measure.append(ts)")
    elif isinstance(element, clef.Clef):
        code_lines.append(f"cl = clef.{type(element).__name__}()")
        code_lines.append("measure.append(cl)")
    elif isinstance(element, key.KeySignature):
        code_lines.append(f"ks = key.KeySignature({element.sharps})")
        code_lines.append("measure.append(ks)")
    elif isinstance(element, bar.Barline):
        code_lines.append(f"bl = bar.Barline('{element.type}')")
        code_lines.append("measure.append(bl)")
    elif isinstance(element, tempo.MetronomeMark):
        code_lines.append(f"tm = tempo.MetronomeMark(number={element.number})")
        code_lines.append("measure.append(tm)")
    return '\n'.join(code_lines)

def generate_code_for_music_structure(music_structure, score_name="score"):
    code = ["from music21 import stream, note, chord, duration, meter, clef, key, bar, tempo", ""]
    code.append(f"{score_name} = stream.Score()")
    code.append("part = stream.Part()")
    code.append("measure = stream.Measure()")

    for element in music_structure.recurse():
        element_code = generate_code_for_element(element)
        if element_code:
            code.extend(element_code.split('\n'))

    code.append("part.append(measure)")
    code.append(f"{score_name}.append(part)")
    return '\n'.join(code)

def main():
    s = stream.Score()
    p = stream.Part()
    m = stream.Measure()
    m.append(clef.TrebleClef())
    m.append(tempo.MetronomeMark(number=120))
    m.append(key.KeySignature(0))
    m.append(meter.TimeSignature('4/4'))
    m.append(note.Note("C4"))
    m.append(chord.Chord(["E4", "G4"]))
    m.append(bar.Barline('final'))
    p.append(m)
    s.append(p)

    generated_code = generate_code_for_music_structure(s)
    print(generated_code)

if __name__ == "__main__":
    main()
