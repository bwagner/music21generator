#!/usr/bin/env python

from abc import ABC, abstractmethod

from music21 import bar, chord, clef, duration, key, meter, note, stream, tempo


class ElementHandler(ABC):
    @abstractmethod
    def generate_code(self, element):
        pass


class NoteHandler(ElementHandler):
    def generate_code(self, element):
        return f"n = note.Note('{element.pitch}', duration=duration.Duration({element.duration.quarterLength}))\nmeasure.append(n)"


class ChordHandler(ElementHandler):
    def generate_code(self, element):
        pitches = ", ".join([f"'{p}'" for p in element.pitches])
        return f"c = chord.Chord([{pitches}], duration=duration.Duration({element.duration.quarterLength}))\nmeasure.append(c)"


class TimeSignatureHandler(ElementHandler):
    def generate_code(self, element):
        return f"ts = meter.TimeSignature('{element.ratioString}')\nmeasure.append(ts)"


class ClefHandler(ElementHandler):
    def generate_code(self, element):
        return f"cl = clef.{type(element).__name__}()\nmeasure.append(cl)"


class KeySignatureHandler(ElementHandler):
    def generate_code(self, element):
        return f"ks = key.KeySignature({element.sharps})\nmeasure.append(ks)"


class BarlineHandler(ElementHandler):
    def generate_code(self, element):
        return f"bl = bar.Barline('{element.type}')\nmeasure.append(bl)"


class MetronomeMarkHandler(ElementHandler):
    def generate_code(self, element):
        return f"tm = tempo.MetronomeMark(number={element.number})\nmeasure.append(tm)"


# Dictionary to map music21 element types to their respective handlers
element_handlers = {
    note.Note: NoteHandler(),
    chord.Chord: ChordHandler(),
    meter.TimeSignature: TimeSignatureHandler(),
    clef.Clef: ClefHandler(),
    key.KeySignature: KeySignatureHandler(),
    bar.Barline: BarlineHandler(),
    tempo.MetronomeMark: MetronomeMarkHandler(),
    # Add entries for other handlers if needed
}


def generate_code_for_element(element):
    handler = element_handlers.get(type(element))
    if handler:
        return handler.generate_code(element)
    else:
        return "# Unhandled element type"


def generate_code_for_music_structure(music_structure, score_name="score"):
    code = [
        "from music21 import stream, note, chord, duration, meter, clef, key, bar, tempo",
        "",
    ]
    code.append(f"{score_name} = stream.Score()")
    code.append("part = stream.Part()")
    code.append("measure = stream.Measure()")

    for element in music_structure.recurse():
        element_code = generate_code_for_element(element)
        if element_code:
            code.extend(element_code.split("\n"))

    code.append("part.append(measure)")
    code.append(f"{score_name}.append(part)")
    return "\n".join(code)


def main():
    s = stream.Score()
    p = stream.Part()
    m = stream.Measure()
    m.append(clef.TrebleClef())
    m.append(tempo.MetronomeMark(number=120))
    m.append(key.KeySignature(0))
    m.append(meter.TimeSignature("4/4"))
    m.append(note.Note("C4"))
    m.append(chord.Chord(["E4", "G4"]))
    m.append(bar.Barline("final"))
    p.append(m)
    s.append(p)

    generated_code = generate_code_for_music_structure(s)
    print(generated_code)


if __name__ == "__main__":
    main()
