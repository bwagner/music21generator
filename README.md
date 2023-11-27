# m21gen

Takes a [music21](https://web.mit.edu/music21/)-structure and generates the
[Python](https://www.python.org/) code required to replicate this music21-structure.

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
```
pip install -r requirements.txt
```

## Use
```
m21gen.py MUSICXML_FILE > GENERATED_PYTHON_SCRIPT_NAME
Generates Python code to reproduce the given MUSICXML_FILE.

m21gen.py -b MUSICXML_FILE
Generates Python code to reproduce the given MUSICXML_FILE
and adds some boilerplate to save the music21-structure generated
by the generated Python script to a new MUSICXML_FILE.
```

## Contributing

## Tests
```
pytest
```

## Thanks
- [music21](https://web.mit.edu/music21/)
