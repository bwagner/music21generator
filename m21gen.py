#!/usr/bin/env python

import warnings
from abc import ABC, abstractmethod
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
└── Part
    ├── Instrument
    └── Measure
        ├── Barline
        ├── Clef
        ├── Key
        ├── Note
        ├── SystemLayout
        ├── StaffLayout
        └── TimeSignature
"""


class ElementHandler(ABC):
    _handlers = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, HANDLES_ATTR):
            if cls.handles:
                ElementHandler._handlers[cls.handles] = cls()
            else:
                warnings.warn(
                    f"Subclass {cls.__name__} has no {HANDLES_ATTR} attribute set. It will not be registered."
                )
        elif (
            cls.__name__ != "ContainerHandler"
        ):  # using string here, otherwise ContainerHandler is not defined yet
            warnings.warn(
                f"Subclass {cls.__name__} is missing a {HANDLES_ATTR} attribute and will not be registered."
            )

    def generate_code(self, element, name):
        """
        May be implemented by subclasses.
        Returns a tuple: the code to generate this element and True if the element should be inserted
                         at the beginning, False if at the end of its container.
        """
        params, insert = self.get_params(element)
        return (
            f"{name} = {self.get_hcls()}({params})",
            insert,
        )

    def get_params(self, element, name) -> str:
        """
        Implemented by subclasses, if they don't implement generate_code.
        Returns a tuple:
        - A string consisting of the parameters for the constructor of the music21-class
          handled by this Handler.
        - True if the element should be inserted at the beginning, False if at the end
          of its container.
        Not declared abstractmethod, because sometimes generated_code is overridden
        and no get_params method is required.
        """
        raise NotImplementedError("abstract method: This code should never run.")

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
        return f"{h.__module__[h.__module__.index('.')+1:]}.{h.__qualname__}"


class NoteHandler(ElementHandler):
    handles = note.Note

    def get_params(self, element):
        return (
            f"'{element.pitch}', duration=duration.Duration({element.duration.quarterLength})",
            False,
        )


class ChordHandler(ElementHandler):
    handles = chord.Chord

    def get_params(self, element):
        pitches = ", ".join([f"'{p}'" for p in element.pitches])
        return (
            f"[{pitches}], duration=duration.Duration({element.duration.quarterLength})",
            False,
        )


class ChordSymbolHandler(ElementHandler):
    handles = harmony.ChordSymbol

    def get_params(self, element):
        chord_figure = element.figure  # Get the chord symbol as a string, e.g., "Cmaj7"
        return f"'{chord_figure}'", False


class TimeSignatureHandler(ElementHandler):
    handles = meter.TimeSignature

    def get_params(self, element):
        return f"'{element.ratioString}'", False


class ClefHandler(ElementHandler):
    handles = clef.Clef

    def generate_code(self, element, name):
        """
        Can't use the generic generate_code, because we're messing with the choice
        of constructor.
        """
        return f"{name} = clef.{type(element).__name__}()", False


class KeySignatureHandler(ElementHandler):
    handles = key.KeySignature

    def get_params(self, element):
        return f"{element.sharps}", False


class BarlineHandler(ElementHandler):
    handles = bar.Barline

    def get_params(self, element):
        return f"'{element.type}'", False


class InstrumentHandler(ElementHandler):
    handles = instrument.Instrument

    def generate_code(self, element, name):
        """
        Can't use the generic generate_code, because we're messing with the choice
        of constructor.
        """
        instrument_name = type(element).__name__
        return f"{name} = instrument.{instrument_name}()", True


class MetronomeMarkHandler(ElementHandler):
    handles = tempo.MetronomeMark

    def generate_code(self, element, name):
        """ """
        params, insert = self.get_params(element)
        placement = element.placement if hasattr(element, "placement") else "above"
        return (
            dedent(
                f"""
            {name} = {self.get_hcls()}({params})
            {name}.placement = '{placement}'
            """
            ),
            insert,
        )

    def get_params(self, element):
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

        return ", ".join(params), False


class StaffLayoutHandler(ElementHandler):
    handles = layout.StaffLayout

    def get_params(self, element):
        params = []

        # Handling properties of StaffLayout
        # Common properties include 'staffDistance', 'staffNumber', etc.
        properties = "staffDistance staffNumber".split()

        # Iterate over properties and set them if they are not None
        for prop in properties:
            value = getattr(element, prop, None)
            if value is not None:
                params.append(f"{prop}={value}")

        return ", ".join(params), False


class MetadataHandler(ElementHandler):
    handles = metadata.Metadata

    def get_params(self, element):
        return f"title='{element.title}', composer='{element.composer}'", True


class RestHandler(ElementHandler):
    handles = note.Rest

    def get_params(self, element):
        return (
            f"duration=duration.Duration({element.duration.quarterLength})",
            False,
        )


class TextBoxHandler(ElementHandler):
    handles = text.TextBox

    def generate_code(self, element, name):
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

        return f"{name} = {self.get_hcls()}(content='{content}')\n" + style_code, True


class ScoreLayoutHandler(ElementHandler):
    handles = layout.ScoreLayout

    def generate_code(self, element, name):
        # Generate code to recreate the ScoreLayout
        # Note: ScoreLayout can have various attributes. Adjust this to handle the attributes you're using.
        code_lines = [f"{name} = {self.get_hcls()}()"]

        if hasattr(element, "staffDistance"):
            code_lines.append(f"{name}.staffDistance = {element.staffDistance}")

        # Include other relevant attributes of ScoreLayout as needed
        # ...

        return "\n".join(code_lines), True


class SystemLayoutHandler(ElementHandler):
    handles = layout.SystemLayout

    def generate_code(self, element, name):
        # Generate code to recreate the SystemLayout
        # Note: SystemLayout can have various attributes. The example below covers a few.
        # You might need to adjust this to handle the specific attributes you're using.
        code_lines = []

        code_lines.append(f"{name} = {self.get_hcls()}(isNew={element.isNew})")

        if hasattr(element, "systemDistance"):
            code_lines.append(f"{name}.systemDistance = {element.systemDistance}")

        if hasattr(element, "topSystemDistance"):
            code_lines.append(f"{name}.topSystemDistance = {element.topSystemDistance}")

        return "\n".join(code_lines), True


class PageLayoutHandler(ElementHandler):
    handles = layout.PageLayout

    def generate_code(self, element, name):
        code_lines = [f"{name} = layout.PageLayout()"]

        # List of potential properties in PageLayout
        properties = [
            "leftMargin",
            "rightMargin",
            "topMargin",
            "bottomMargin",
            "pageHeight",
            "pageWidth",
            "isPortrait",
            # Add more properties here as needed
        ]

        # Iterate over properties and set them if they are not None
        for prop in properties:
            value = getattr(element, prop, None)
            if value is not None:
                code_lines.append(f"{name}.{prop} = {value}")

        return "\n".join(code_lines), True


class TextExpressionHandler(ElementHandler):
    handles = expressions.TextExpression

    def generate_code(self, element, name):
        # Escape single quotes in the text content
        content = element.content.replace("'", "\\'")
        return f"{name} = {self.get_hcls()}('{content}')\n", False


class StaffGroupHandler(ElementHandler):
    handles = layout.StaffGroup

    def generate_code(self, element, name):
        code_lines = [f"{name} = {self.get_hcls()}()"]

        for prop in "symbol barTogether connectsAtTop connectsAtBottom".split():
            value = getattr(element, prop, None)
            if value is not None:
                value_str = f"'{value}'" if isinstance(value, str) else str(value)
                code_lines.append(f"{name}.{prop} = {value_str}")

        for element in element.getSpannedElements():
            code_lines.append(
                f"{name}.addSpannedElements(generated_parts['{element.id}'])"
            )

        return "\n".join(code_lines), True


class ContainerHandler(ElementHandler):
    def generate_code(self, element, name):
        code_lines = [f"{name} = stream.{self.handles.__qualname__}()"]
        prefix = self.handles.__qualname__.lower()
        for i, sub_element in enumerate(element):
            if handler := ElementHandler.get_handler(sub_element):
                element_code, insert = handler.generate_code(
                    sub_element, f"{prefix}_e{i}"
                )
                code_lines.extend(element_code.split("\n"))
                if insert:
                    code_lines.append(f"{name}.insert(0, {prefix}_e{i})")
                else:
                    code_lines.append(f"{name}.append({prefix}_e{i})")
            else:
                raise NotImplementedError(
                    dedent(
                        f"""

                    No handler implemented for sub-element type {type(sub_element)} in {self.handles.__qualname__}.

                    Go ahead and contribute class {type(sub_element).__name__}Handler(ElementHandler)!

                 """
                    )
                )
        if ct := self.custom_treatment(element, name):
            code_lines.extend(ct)
        return "\n".join(code_lines), False

    def custom_treatment(self, element, name):
        return []


class PartHandler(ContainerHandler):
    handles = stream.Part

    def custom_treatment(self, element, name) -> str:
        return [
            f"generated_parts['{element.id}'] = {name}",
            f"{name}.partName = '{element.partName}'",
            f"{name}.partAbbreviation = '{element.partAbbreviation}'",
        ]


class MeasureHandler(ContainerHandler):
    handles = stream.Measure

    def custom_treatment(self, element, name) -> str:
        return [
            f"last_measure = {name}",  # save potentially last measure for final barline
            f"{name}.number = {element.number}",
        ]


class ScoreHandler(ContainerHandler):
    handles = stream.Score


class StreamHandler(ContainerHandler):
    handles = stream.Stream


def generate_code_for_music_structure(
    music_structure,
    add_boilerplate=False,
    musicxml_out_fn="output.musicxml",
    origin=None,
):
    code_lines = [
        "from music21 import *",
        "",
        f"# generated by {P(__file__).name} {datetime.now()} {'from ' + origin if origin else ''}",
        f"# {'with' if add_boilerplate else 'without'} boilerplate.",
        "",
        "generated_parts = dict()",
        "last_measure = None",  # save potentially last measure for final barline
    ]

    if handler := ElementHandler.get_handler(music_structure):
        element_code, insert = handler.generate_code(music_structure, f"{SCORE_NAME}")
        code_lines.extend(element_code.split("\n"))
    else:
        raise NotImplementedError(
            dedent(
                f"""

            No handler implemented for sub-element type {type(music_structure)} in MusicStructure.

            Go ahead and contribute class {type(music_structure).__name__}Handler(ElementHandler)!

         """
            )
        )

    code_lines.append(
        dedent(
            """
            last_measure.rightBarline = bar.Barline(type="final")
            """
        )
    )

    code_str = "\n".join(code_lines)

    if add_boilerplate:
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


def custom_help_check():
    if "-h" in sys.argv or "-?" in sys.argv:
        sys.argv[1] = "--help"


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


if __name__ == "__main__":

    def main(
        add_boilerplate: bool = typer.Option(
            True, "--add-no-boilerplate", "-n", help="Add boilerplate code"
        ),
        output_m21_structure: bool = typer.Option(
            False, "--output-m21-structure", "-m", help="Output m21 structure"
        ),
        musicxml_file_path: str = typer.Argument(
            ..., help="Path to musicxml file", show_default=False
        ),
    ):
        score = converter.parse(musicxml_file_path)

        if output_m21_structure:
            print2(lambda: score.show("text"))

        print("#!/usr/bin/env python\n")
        musicxml_out_fn = f"{P(musicxml_file_path).stem}_generated.musicxml"
        generated_code = generate_code_for_music_structure(
            score,
            add_boilerplate=add_boilerplate,
            musicxml_out_fn=musicxml_out_fn,
            origin=musicxml_file_path,
        )
        print(generated_code)

    custom_help_check()
    typer.run(main)
