# music21generator

Takes a [music21](https://web.mit.edu/music21/)-structure and generates the
[Python](https://www.python.org/) code required to replicate this music21-structure.

```console

 Usage: m21gen.py [OPTIONS] MUSICXML_FILE_PATH

╭─ Arguments ────────────────────────────────────────────────────────────────╮
│ *    musicxml_file_path      TEXT  Path to musicxml file [required]        │
╰────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────╮
│ --omit-boilerplate       -n        Omit boilerplate code [default: False]  │
│ --display-m21-structure  -m        Display m21 structure (for debugging)   │
│ --help                             Show this message and exit.             │
╰────────────────────────────────────────────────────────────────────────────╯

```

## Purpose
As a beginner using music21, it can be intimidating to find the entry into the
library. But you might be experienced with a score editor like
[musescore](https://musescore.org), [finale](https://www.finalemusic.com),
[sibelius](https://www.avid.com/sibelius). So, you could start by creating a
score using any of those editors, export it as
[musicxml](https://www.musicxml.com), pass it to m21gen.py, which generates the
Python code that reproduces this document.  Finally, use this generated
skeleton Python script as a stepping stone and add procedural or generative
aspects.

## Installation
```console
git clone https://github.com/bwagner/music21generator.git
cd music21generator
pip install -r requirements.txt
```

## Use
```console

/path/to/music21generator/m21gen.py MUSICXML_FILE > GENERATED_PYTHON_SCRIPT_NAME

# Generates Python code to reproduce the given MUSICXML_FILE on stdout
# and adds some boilerplate to save the music21-structure generated
# by the generated Python script to a new MUSICXML_FILE. In the above incantation,
# stdout is captured in GENERATED_PYTHON_SCRIPT_NAME.

/path/to/music21generator/m21gen.py MUSICXML_FILE | python

# Generates Python code to reproduce the given MUSICXML_FILE and executes it right away.
```

## Limitations
For now,
[articulations](https://web.mit.edu/music21/doc/moduleReference/moduleArticulations.html) and
many other features of music21 are missing.
It's uncertain whether these will ever be implemented, since this tool is only supposed to give
you a head start.

## Contributing
```console
git clone https://github.com/bwagner/music21generator.git
cd music21generator
pip install -r requirements.txt -r dev-requirements.txt
pre-commit install
```

## Tests
```console
cd music21generator
pytest
```

## Thanks
- [music21](https://web.mit.edu/music21/)
