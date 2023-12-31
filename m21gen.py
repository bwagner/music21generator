#!/usr/bin/env python
import warnings
from abc import ABC
from datetime import datetime
from pathlib import Path as P
from textwrap import dedent

from music21 import *

SCORE_NAME = "score"
HANDLES_ATTR = "handles"

if __name__ == "__main__":
    import sys

    import typer

"""
Containment Hierarchy:

Score
├── Metadata
├── TextBox
└── Part
    ├── Instrument
    ├── Slur
    └── Measure
        ├── Barline
        ├── Clef
        ├── KeySignature
        ├── Note
        ├── Rest
        ├── PageLayout
        ├── RehearsalMark
        ├── Repeat
        ├── SystemLayout
        ├── StaffLayout
        └── TimeSignature
"""

resolve_spanners = ""


class ElementHandler(ABC):
    handles = None
    insert = False  # by default, do not insert at the beginning of container
    _handlers = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, HANDLES_ATTR):
            if cls.handles:
                ElementHandler._handlers[cls.handles] = cls()
            elif cls.__name__ != "ContainerHandler":
                warnings.warn(
                    f"Subclass {cls.__name__} has no {HANDLES_ATTR} attribute set. It will not be registered."
                )
        elif (
            cls.__name__ != "ContainerHandler"
        ):  # using string here, otherwise ContainerHandler is not defined yet
            warnings.warn(
                f"Subclass {cls.__name__} is missing a {HANDLES_ATTR} attribute and will not be registered."
            )

    def generate_code(self, element, name: str) -> str:
        """
        May be implemented by subclasses.
        Returns a tuple: the code to generate this element and True if the element should be inserted
                         at the beginning, False if at the end of its container.
        """
        params = self.get_params(element)
        code_lines = [f"{name} = {self.get_hcls()}({params})"]
        if ct := self.custom_treatment(element, name):
            code_lines.extend(ct)
        return "\n".join(code_lines)

    def custom_treatment(self, element, name: str) -> list[str]:
        return []

    def get_params(self, element) -> str:
        params = []
        for prop in self.get_properties():
            if (value := getattr(element, prop, None)) is not None:
                params.append(f"{prop}='{value}'")

        return ", ".join(params)

    def get_properties(self) -> list[str]:
        return []

    @classmethod
    def get_handler(cls, element):
        element_type = type(element)
        while element_type is not None:
            if handler := cls._handlers.get(element_type):
                return handler
            # Move up the inheritance hierarchy
            element_type = element_type.__base__
        return None

    @classmethod
    def get_hcls(cls):
        """
        Gets the music21-class handled by this Handler as string, stripped of
        top level module "music21".
        """
        h = cls.handles
        return f"{h.__module__[h.__module__.index('.') + 1:]}.{h.__qualname__}"


class NoteHandler(ElementHandler):
    handles = note.Note

    def generate_code(self, element, name: str) -> str:
        params = self.get_params(element)
        code = dedent(
            f"""
        {name} = {self.get_hcls()}({params})
        generated_notes['{element.id}'] = {name}
        """
        )
        if element.lyric:
            # had to dedent manually, because there were multiline lyrics.
            code += f"""
{name}.lyric = '''{element.lyric}'''
        """
        return code

    def get_params(self, element) -> str:
        return f"'{element.pitch}', duration=duration.Duration({element.duration.quarterLength})"


class ChordHandler(ElementHandler):
    handles = chord.Chord

    def get_params(self, element) -> str:
        pitches = ", ".join([f"'{p}'" for p in element.pitches])
        return (
            f"[{pitches}], duration=duration.Duration({element.duration.quarterLength})"
        )


class ChordSymbolHandler(ElementHandler):
    handles = harmony.ChordSymbol

    def get_params(self, element) -> str:
        return f"'{element.figure}'"  # Get the chord symbol as a string, e.g., "Cmaj7"


class TimeSignatureHandler(ElementHandler):
    handles = meter.TimeSignature

    def get_params(self, element) -> str:
        return f"'{element.ratioString}'"


class ClefHandler(ElementHandler):
    handles = clef.Clef

    def generate_code(self, element, name: str) -> str:
        """
        Can't use the generic generate_code, because we're messing with the choice
        of constructor.
        """
        return f"{name} = clef.{type(element).__name__}()"


class KeySignatureHandler(ElementHandler):
    handles = key.KeySignature

    def get_params(self, element) -> str:
        return f"{element.sharps}"


class BarlineHandler(ElementHandler):
    handles = bar.Barline

    def get_params(self, element) -> str:
        return f"'{element.type}'"


class InstrumentHandler(ElementHandler):
    handles = instrument.Instrument
    insert = True

    def generate_code(self, element, name: str) -> str:
        """
        Can't use the generic generate_code, because we're messing with the choice
        of constructor.
        """
        instrument_name = type(element).__name__
        return f"{name} = instrument.{instrument_name}()"


class MetronomeMarkHandler(ElementHandler):
    handles = tempo.MetronomeMark

    def generate_code(self, element, name: str) -> str:
        """ """
        params = self.get_params(element)
        placement = element.placement if hasattr(element, "placement") else "above"
        return dedent(
            f"""
            {name} = {self.get_hcls()}({params})
            {name}.placement = '{placement}'
            """
        )

    def get_params(self, element) -> str:
        params = []

        # Check for number attribute or derived tempo
        tempo_number = getattr(element, "number", None)
        if tempo_number is None and hasattr(element, "_tempo"):
            tempo_number = element._tempo

        if tempo_number is not None:
            params.append(f"number={tempo_number}")

        # Check for text attribute
        if element.text:
            params.append(f"text='{element.text}'")

        # Check for referent attribute
        if element.referent:
            referent_type = element.referent.type
            params.append(f"referent=duration.Duration(type='{referent_type}')")

        return ", ".join(params)


class StaffLayoutHandler(ElementHandler):
    handles = layout.StaffLayout

    def get_properties(self) -> list[str]:
        return "staffDistance staffNumber staffLines".split()


class MetadataHandler(ElementHandler):
    handles = metadata.Metadata
    insert = True

    def get_properties(self) -> list[str]:
        return "title composer lyricist".split()


class RestHandler(ElementHandler):
    handles = note.Rest

    def get_params(self, element) -> str:
        return f"duration=duration.Duration({element.duration.quarterLength})"


class TextBoxHandler(ElementHandler):
    handles = text.TextBox
    insert = True

    def generate_code(self, element, name: str) -> str:
        content = element.content.replace("'", "\\'")

        style_code = ""
        if element.style:
            style_code += f"{name}_style = style.TextStyle()\n"

            # Function to check if an attribute is scalar
            def is_scalar(attr):
                return isinstance(attr, (int, float, str, bool))

            # Iterate over attributes and handle only scalar values
            for attr in dir(element.style):
                if not attr.startswith("__") and not callable(
                    getattr(element.style, attr)
                ):
                    value = getattr(element.style, attr)
                    if is_scalar(value):
                        # String values need to be quoted
                        if isinstance(value, str):
                            value = f"'{value}'"
                        style_code += f"{name}_style.{attr} = {value}\n"

            style_code += f"{name}.style = {name}_style\n"

        return f"{name} = {self.get_hcls()}(content='{content}')\n{style_code}"


class ScoreLayoutHandler(ElementHandler):
    handles = layout.ScoreLayout
    insert = True

    def get_properties(self) -> list[str]:
        return "staffDistance".split()


class SystemLayoutHandler(ElementHandler):
    handles = layout.SystemLayout
    insert = True

    def generate_code(self, element, name: str) -> str:
        code_lines = [f"{name} = {self.get_hcls()}(isNew={element.isNew})"]

        code_lines.extend(self.get_lines(element, name))

        return "\n".join(code_lines)

    def get_lines(self, element, name) -> str:
        code_lines = []
        for prop in self.get_properties():
            if (value := getattr(element, prop, None)) is not None:
                code_lines.append(f"{name}.{prop}='{value}'")

        return code_lines

    def get_properties(self) -> list[str]:
        return "systemDistance topSystemDistance".split()


class PageLayoutHandler(ElementHandler):
    handles = layout.PageLayout
    insert = True

    def generate_code(self, element, name: str) -> str:
        code_lines = [f"{name} = {self.get_hcls()}()"]

        code_lines.extend(self.get_lines(element, name))

        return "\n".join(code_lines)

    def get_lines(self, element, name) -> str:
        code_lines = []
        for prop in self.get_properties():
            if (value := getattr(element, prop, None)) is not None:
                code_lines.append(f"{name}.{prop}='{value}'")

        return code_lines

    def get_properties(self) -> list[str]:
        return [
            "leftMargin",
            "rightMargin",
            "topMargin",
            "bottomMargin",
            "pageHeight",
            "pageWidth",
            "isPortrait",
            # Add more properties here as needed
        ]


class TextExpressionHandler(ElementHandler):
    handles = expressions.TextExpression

    def generate_code(self, element, name: str) -> str:
        # Escape single quotes in the text content
        content = element.content.replace("'", "\\'")
        return f"{name} = {self.get_hcls()}('{content}')\n"


class StaffGroupHandler(ElementHandler):
    handles = layout.StaffGroup
    insert = True

    def generate_code(self, element, name: str) -> str:
        code_lines = [f"{name} = {self.get_hcls()}()"]

        for prop in "symbol barTogether connectsAtTop connectsAtBottom".split():
            value = getattr(element, prop, None)
            if value is not None:
                value_str = f"'{value}'" if isinstance(value, str) else str(value)
                code_lines.append(f"{name}.{prop} = {value_str}")

        code_lines.extend(
            f"{name}.addSpannedElements(generated_parts['{element.id}'])"
            for element in element.getSpannedElements()
        )
        return "\n".join(code_lines)


class ContainerHandler(ElementHandler):
    def generate_code(self, element, name: str) -> str:
        code_lines = [f"{name} = stream.{self.handles.__qualname__}()"]
        prefix = self.handles.__qualname__.lower()
        for i, sub_element in enumerate(element):
            if not (handler := ElementHandler.get_handler(sub_element)):
                raise NotImplementedError(
                    dedent(
                        f"""

                    No handler implemented for sub-element type {type(sub_element)} in {self.handles.__qualname__}.

                    Go ahead and contribute class {type(sub_element).__name__}Handler(ElementHandler)!

                 """
                    )
                )
            element_code = handler.generate_code(sub_element, f"{prefix}_e{i}")
            code_lines.extend(element_code.split("\n"))
            if hasattr(handler, "insert") and handler.insert:
                code_lines.append(f"{name}.insert(0, {prefix}_e{i})")
            else:
                code_lines.append(f"{name}.append({prefix}_e{i})")
        if ct := self.custom_treatment(element, name):
            code_lines.extend(ct)
        return "\n".join(code_lines)

    def custom_treatment(self, element, name: str) -> list[str]:
        return []


class PartHandler(ContainerHandler):
    handles = stream.Part

    def custom_treatment(self, element, name: str) -> list[str]:
        return [
            f"generated_parts['{element.id}'] = {name}",
            f"{name}.partName = '{element.partName}'",
            f"{name}.partAbbreviation = '{element.partAbbreviation}'",
        ]


class MeasureHandler(ContainerHandler):
    handles = stream.Measure

    def custom_treatment(self, element, name: str) -> list[str]:
        return [
            f"last_measure = {name}",  # save potentially last measure for final barline
            f"{name}.number = {element.number}",
        ]


class ScoreHandler(ContainerHandler):
    handles = stream.Score


class StreamHandler(ContainerHandler):
    handles = stream.Stream


class RehearsalMarkHandler(ElementHandler):
    # TODO:
    #
    # RehearsalMarks in musicxml are embedded in a direction element:
    #
    # <direction placement="above">
    #   <direction-type>
    #     <rehearsal>A</rehearsal>
    #   </direction-type>
    # </direction>
    #
    # But in the musicxml we generate it ends up:
    #
    # <direction>
    #   <direction-type>
    #     <rehearsal enclosure="none" halign="center" valign="middle">A</rehearsal>
    #   </direction-type>
    # </direction>
    #
    # enclosure, halign, valign were not in the original rehearsal mark, and the
    # placement="above" attribute in the containing direction is missing.
    # This attibute would be essential to have the rehearsalmark above the staff.
    # I don't know how to get at that enclosing direction element from the rehearsal
    # mark.

    handles = expressions.RehearsalMark
    insert = True

    def get_properties(self) -> list[str]:
        return "content".split()


class RepeatHandler(ElementHandler):
    handles = bar.Repeat

    def get_params(self, element):
        params = []

        # Handle direction of the repeat (start or end)
        if hasattr(element, "direction"):
            params.append(f"direction='{element.direction}'")

        # Add other attributes as needed based on the properties of the Repeat
        # ...

        return ", ".join(params)


class SlurHandler(ElementHandler):
    handles = spanner.Slur
    insert = True

    def generate_code(self, element, name: str) -> str:
        global resolve_spanners
        params = self.get_params(element)
        # The Notes we're referring to here are only generated later, so we need store the code to resolve the spanners
        # to be executed at the end.
        # To keep the reference to the right spanner (Slur), we store it under the id of its first note. This should be
        # unique. We could have used the id of the freshly generated slur, too.
        resolve_spanners += dedent(
            f"""
            generated_spanners['{element.getFirst().id}'].addSpannedElements(generated_notes['{element.getFirst().id}'])
            generated_spanners['{element.getFirst().id}'].addSpannedElements(generated_notes['{element.getLast().id}'])
        """
        )
        return dedent(
            f"""
            {name} = {self.get_hcls()}({params})
            generated_spanners['{element.getFirst().id}'] = {name}
        """
        )

    def get_params(self, element):
        params = []

        # Handle the type of the slur (start or stop)
        # MusicXML 'type' attribute maps to Slur's start/stop methods in music21
        if hasattr(element, "type"):
            params.append(f"type='{element.type}'")

        # Handle the placement of the slur (above or below)
        if hasattr(element, "placement"):
            params.append(f"placement='{element.placement}'")

        # Handle the number attribute (if used for identifying slurs in MusicXML)
        if hasattr(element, "number"):
            params.append(f"number={element.number}")

        # Add other attributes as needed based on the properties of the Slur
        # ...

        return ", ".join(params)


class UnpitchedHandler(ElementHandler):
    handles = note.Unpitched

    def get_properties(self) -> list[str]:
        return "displayStep displayOctave".split()


def generate_code_for_music_structure(
    music_structure,
    omit_boilerplate=False,
    musicxml_out_fn="output.musicxml",
    origin=None,
):
    code_lines = [
        "from music21 import *",
        "",
        f"# generated by {P(__file__).name} {datetime.now()} {f'from {origin}' if origin else ''}",
        f"# {'without' if omit_boilerplate else 'with'} boilerplate.",
        "",
        "generated_parts = dict()",
        "generated_notes = dict()",
        "generated_spanners = dict()",
        "last_measure = None",  # save potentially last measure for final barline
    ]

    if not (handler := ElementHandler.get_handler(music_structure)):
        raise NotImplementedError(
            dedent(
                f"""

            No handler implemented for sub-element type {type(music_structure)} in MusicStructure.

            Go ahead and contribute class {type(music_structure).__name__}Handler(ElementHandler)!

         """
            )
        )

    element_code = handler.generate_code(music_structure, f"{SCORE_NAME}")
    code_lines.extend(element_code.split("\n"))
    code_lines.append(
        dedent(
            """
            last_measure.rightBarline = bar.Barline(type="final")
            """
        )
    )

    code_str = "\n".join(code_lines)

    code_str += resolve_spanners

    if not omit_boilerplate:
        code_str += dedent(
            rf"""

        if not {SCORE_NAME}.isWellFormedNotation():
            print("The score is not well-formed. Check the structure and contents.")
            {SCORE_NAME}.show("text")


        file_path = "{musicxml_out_fn}"
        print(f"Saved to \"{musicxml_out_fn}\"")
        {SCORE_NAME}.write("musicxml", fp=file_path)
        import subprocess
        subprocess.run(f"open {musicxml_out_fn}".split())
        """
        )

    return code_str


if __name__ == "__main__":

    def print2(func):
        """
        Swaps stdout and stderr, then calls func, then swaps stdout and stderr again.

        Classically, this would be attained by using:
        with contextlib.redirect_stdout:
            func()
        which would even render this function print2 obsolete, but doing so gave an error:
        TypeError: 'ABCMeta' object does not support the context manager protocol
        """
        sys.stdout, sys.stderr = sys.stderr, sys.stdout
        func()
        sys.stdout, sys.stderr = sys.stderr, sys.stdout

    def custom_help_check():
        """
        Adds command line options "-h" and "-?" to the default "--help" to
        show help output.
        """
        if "-h" in sys.argv or "-?" in sys.argv:
            sys.argv[1] = "--help"

    def main(
        omit_boilerplate: bool = typer.Option(
            False, "--omit-boilerplate", "-n", help="Omit boilerplate code"
        ),
        display_m21_structure: bool = typer.Option(
            False,
            "--display-m21-structure",
            "-m",
            help="Display m21 structure (for debugging)",
        ),
        musicxml_file_path: str = typer.Argument(
            ..., help="Path to musicxml file", show_default=False
        ),
    ):
        score = converter.parse(musicxml_file_path)

        if display_m21_structure:
            print2(lambda: score.show("text"))

        print("#!/usr/bin/env python\n")
        musicxml_out_fn = f"{P(musicxml_file_path).stem}_generated.musicxml"
        generated_code = generate_code_for_music_structure(
            score,
            omit_boilerplate=omit_boilerplate,
            musicxml_out_fn=musicxml_out_fn,
            origin=musicxml_file_path,
        )
        print(generated_code)

    custom_help_check()
    typer.run(main)
