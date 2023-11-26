#!/usr/bin/env python

import warnings
import pathlib
from abc import ABC, abstractmethod

from music21 import *
from textwrap import dedent

SCORE_NAME = "score"
PART_NAME = "part"
MEASURE_NAME = "measure"

if __name__ == "__main__":
    from music21 import converter
    import sys


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


class ChordSymbolHandler(ElementHandler):
    handles = harmony.ChordSymbol

    def generate_code(self, element):
        chord_figure = element.figure  # Get the chord symbol as a string, e.g., "Cmaj7"
        return f"c = harmony.ChordSymbol('{chord_figure}')\nmeasure.append(c)"


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

class InstrumentHandler(ElementHandler):
    handles = instrument.Instrument

    def generate_code(self, element):
        instrument_name = type(element).__name__
        return f"inst = instrument.{instrument_name}()\npart.insert(0, inst)"


class PartHandler(ElementHandler):
    handles = stream.Part

    def generate_code(self, element):
        code_lines = [f"{PART_NAME} = stream.Part()"]
        for sub_element in element:
#            print(f"# {sub_element=}")
            handler = ElementHandler.get_handler(sub_element)
            if handler:
                element_code = handler.generate_code(sub_element)
                code_lines.extend(element_code.split('\n'))
            else:
                raise NotImplementedError(
                    f"No handler implemented for sub-element type {type(sub_element)} in Part"
                )

            # TODO: sub_elements of Part should return their variable name, so they can
            #       be added to te part. Better yet: The parent handler (here: PartHandler)
            #       should define the name of the variable that the sub_element should name
            #       itself.
            # code_lines.append(f"{PART_NAME}.append(measure)")  # TODO: see comment just above

        code_lines.append(f"{SCORE_NAME}.append({PART_NAME})")
        return "\n".join(code_lines)


class MeasureHandler(ElementHandler):
    handles = stream.Measure

    def generate_code(self, element):
        code_lines = [f"{MEASURE_NAME} = stream.Measure()"]
        for sub_element in element:
            handler = ElementHandler.get_handler(sub_element)
            if handler:
                code_lines.append(handler.generate_code(sub_element))
            else:
                raise NotImplementedError(
                    f"No handler implemented for sub-element type {type(sub_element)} in Measure"
                )
        code_lines.append(f"{PART_NAME}.append({MEASURE_NAME})")  # TODO: see comment in PartHandler
        return "\n".join(code_lines)


class MetronomeMarkHandler(ElementHandler):
    handles = tempo.MetronomeMark

    def generate_code(self, element):
        return f"tm = tempo.MetronomeMark(number={element.number})\nmeasure.append(tm)"


class MetadataHandler(ElementHandler):
    handles = metadata.Metadata

    def generate_code(self, element):
        code_lines = []
        if element.title:
            code_lines.append(f"md = metadata.Metadata(title='{element.title}')")
            code_lines.append(f"{SCORE_NAME}.insert(0, md)")
        # You can add similar lines for other metadata fields like composer, date, etc.
        return "\n".join(code_lines)


class RestHandler(ElementHandler):
    handles = note.Rest

    def generate_code(self, element):
        return f"r = note.Rest(duration=duration.Duration({element.duration.quarterLength}))\nmeasure.append(r)"

class TextBoxHandler(ElementHandler):
    handles = text.TextBox

    def generate_code(self, element):
        # Escape single quotes in the text content
        content = element.content.replace("'", "\\'")
        # Generate code to recreate the TextBox
        return f"tb = text.TextBox(content='{content}')\n" \
               f"tb.style = '{element.style}'\n" \
               f"tb.positionX = {element.positionX}\n" \
               f"tb.positionY = {element.positionY}\n" \
               "score.insert(0, tb)"

class ScoreLayoutHandler(ElementHandler):
    handles = layout.ScoreLayout

    def generate_code(self, element):
        # Generate code to recreate the ScoreLayout
        # Note: ScoreLayout can have various attributes. Adjust this to handle the attributes you're using.
        code_lines = ["score_layout = layout.ScoreLayout()"]

        if hasattr(element, 'staffDistance'):
            code_lines.append(f"score_layout.staffDistance = {element.staffDistance}")

        # Include other relevant attributes of ScoreLayout as needed
        # ...

        code_lines.append("score.insert(0, score_layout)")

        return "\n".join(code_lines)


class SystemLayoutHandler(ElementHandler):
    handles = layout.SystemLayout

    def generate_code(self, element):
        # Generate code to recreate the SystemLayout
        # Note: SystemLayout can have various attributes. The example below covers a few.
        # You might need to adjust this to handle the specific attributes you're using.
        code_lines = []
        if element.isNew:
            code_lines.append("sys_layout = layout.SystemLayout(isNew=True)")
        else:
            code_lines.append("sys_layout = layout.SystemLayout()")

        if hasattr(element, 'systemDistance'):
            code_lines.append(f"sys_layout.systemDistance = {element.systemDistance}")

        if hasattr(element, 'topSystemDistance'):
            code_lines.append(f"sys_layout.topSystemDistance = {element.topSystemDistance}")

        code_lines.append("measure.insert(0, sys_layout)")

        return "\n".join(code_lines)


def generate_code_for_element(element):
    handler = ElementHandler.get_handler(element)
    if handler:
        return handler.generate_code(element)
    else:
        raise NotImplementedError(
            f"Unhandled element type {type(element)}. Candidates: {ElementHandler._handlers=}"
        )


def generate_code_for_music_structure(music_structure, add_boilerplate=False, musicxml_out_fn="output.musicxml"):
    code = [
        "from music21 import *",
        "",
        f"{SCORE_NAME} = stream.Score()",
    ]

    for element in music_structure:
        element_code = generate_code_for_element(element)
        code.extend(element_code.split("\n"))

    code_str = "\n".join(code)

    if add_boilerplate:
        print("# adding boilerplate")
        code_str += dedent(fr"""

        if not {SCORE_NAME}.isWellFormedNotation():
            print("The score is not well-formed. Check the structure and contents.")
            {SCORE_NAME}.show("text")


        file_path = "{musicxml_out_fn}"
        print(f"Saved to \"{musicxml_out_fn}\"")
        {SCORE_NAME}.write("musicxml", fp=file_path)
        """)
    else:
        print("# skipping boilerplate")

    return code_str


def main():

    if add_boilerplate := len(sys.argv) > 1 and sys.argv[1] == "-b":
        sys.argv.pop(0)

    musicxml_file_path = sys.argv[1]
    score = converter.parse(musicxml_file_path)
#    score.show("text")
    if not score.isWellFormedNotation():
        print("The score is not well-formed. Check the structure and contents.")
    else:
        print("#  The score is well-formed.")
    print("\n#  The Python-code to generate this score:\n")
    musicxml_out_fn = f"{pathlib.Path(musicxml_file_path).stem}_generated.musicxml"
    generated_code = generate_code_for_music_structure(score, add_boilerplate=add_boilerplate, musicxml_out_fn=musicxml_out_fn)
    print(generated_code)


if __name__ == "__main__":
    main()
