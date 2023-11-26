#!/usr/bin/env python

import warnings
from abc import ABC, abstractmethod

from music21 import bar, chord, clef, duration, key, meter, note, stream, tempo


class ElementHandler(ABC):
    _handlers = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "handles"):
            if cls.handles:
                ElementHandler._handlers[cls.handles] = cls()
            else:
                warnings.warn(
                    f"Subclass {cls.__name__} has no handles attribute set. It will not be registered."
                )
        else:
            warnings.warn(
                f"Subclass {cls.__name__} is missing a handles attribute and will not be registered."
            )

    @abstractmethod
    def generate_code(self, element):
        pass

    @classmethod
    def get_handler(cls, element):
        element_type = type(element)
        while element_type is not None:
            handler = cls._handlers.get(element_type)
            if handler:
                return handler
            # Move up the inheritance hierarchy
            element_type = element_type.__base__
        return None


class NoteHandler(ElementHandler):
    handles = note.Note

    def generate_code(self, element):
        return f"n = note.Note('{element.pitch}', duration=duration.Duration({element.duration.quarterLength}))\nmeasure.append(n)"


class ChordHandler(ElementHandler):
    handles = chord.Chord

    def generate_code(self, element):
        pitches = ", ".join([f"'{p}'" for p in element.pitches])
        return f"c = chord.Chord([{pitches}], duration=duration.Duration({element.duration.quarterLength}))\nmeasure.append(c)"


class TimeSignatureHandler(ElementHandler):
    handles = meter.TimeSignature

    def generate_code(self, element):
        return f"ts = meter.TimeSignature('{element.ratioString}')\nmeasure.append(ts)"


class ClefHandler(ElementHandler):
    handles = clef.Clef

    def generate_code(self, element):
        return f"cl = clef.{type(element).__name__}()\nmeasure.append(cl)"


class KeySignatureHandler(ElementHandler):
    handles = key.KeySignature

    def generate_code(self, element):
        return f"ks = key.KeySignature({element.sharps})\nmeasure.append(ks)"


class BarlineHandler(ElementHandler):
    handles = bar.Barline

    def generate_code(self, element):
        return f"bl = bar.Barline('{element.type}')\nmeasure.append(bl)"


class PartHandler(ElementHandler):
    handles = stream.Part

    def generate_code(self, element):
        code_lines = ["part = stream.Part()"]
        for sub_element in element:
            handler = ElementHandler.get_handler(sub_element)
            if handler:
                code_lines.append(handler.generate_code(sub_element))
            else:
                code_lines.append("# Unhandled sub-element type")
        return "\n".join(code_lines)


class MeasureHandler(ElementHandler):
    handles = stream.Measure

    def generate_code(self, element):
        code_lines = ["measure = stream.Measure()"]
        for sub_element in element:
            handler = ElementHandler.get_handler(sub_element)
            if handler:
                code_lines.append(handler.generate_code(sub_element))
            else:
                raise NotImplementedError(
                    f"No handler implemented for sub-element type {type(sub_element)} in Measure"
                )
        return "\n".join(code_lines)


class MetronomeMarkHandler(ElementHandler):
    handles = tempo.MetronomeMark

    def generate_code(self, element):
        return f"tm = tempo.MetronomeMark(number={element.number})\nmeasure.append(tm)"


def generate_code_for_element(element):
    handler = ElementHandler.get_handler(element)
    if handler:
        return handler.generate_code(element)
    else:
        raise NotImplementedError(
            f"Unhandled element type {type(element)}. Candidates: {ElementHandler._handlers=}"
        )


def generate_code_for_music_structure(music_structure, score_name="score"):
    code = [
        "from music21 import stream, note, chord, duration, meter, clef, key, bar, tempo",
        "",
    ]
    code.append(f"{score_name} = stream.Score()")

    for element in music_structure:
        if isinstance(element, stream.Part):
            part_code = generate_code_for_element(element)
            code.extend(part_code.split("\n"))
        elif not isinstance(element, stream.Measure):
            # Handling non-measure, non-part top-level elements
            element_code = generate_code_for_element(element)
            code.extend(element_code.split("\n"))

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
