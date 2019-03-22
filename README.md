# Description

Experimental template to generate lecture slides in CSC style from markdown
(or reStructuredText).

# Usage

## Install

See Pandoc's install instructions (http://pandoc.org/installing.html) for
detailed instructions on how to install Pandoc.

## Convert markdown
```
$ cd /path/to/reveal-pandoc
$ python convert.py talk.md
```
And then browse to the output (`talk.html`):

- `$ open talk.html` (Mac)
- `$ firefox talk.html` (Linux)

## More information

Options for the helper script (`convert.py`) can be seen with
```
$ python convert.py --help
```

and more detailed information, such as configuration options and the exact
pandoc command, can be seen e.g. with
```
$ python convert.py --verbose talk.md
```

If needed, the URLs of the javascript libraries can also be changed. For more
info, see
```
$ python convert.py --debug talk.md
```


# Markdown file syntax

Every slide set should start with a metadata block (see [Syntax
Guide](docs/syntax-guide.md) for details) followed by slides in Markdown
syntax (Pandoc prefers Commonmark, but understands also other flavours).

Slides are separated by using first-level headers.

Even though Pandoc understands most flavours of Markdown syntax (and is quite
good in handling minor differences), to avoid conversion errors, it is a good
idea to be a bit picky about whitespaces etc. and to aim for consistent
syntax.

Please look at [example.md](example.md) for an example.


# Importing an existing presentation

In order to import an existing presentation, you need to:
1. convert all texts (bullet points, source code etc.) into Markdown syntax
2. convert all figures into separate files (e.g. into PNGs or SVGs)

If you want to convert a Powerpoint presentation, please see
[some tips for converting a Powerpoint](docs/import-powerpoint.md).

