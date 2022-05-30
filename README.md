# slidefactory

Generate lecture slides in CSC style from markdown (or reStructuredText).


## Usage

Convert slides from Markdown to HTML:
```bash
slidefactory.sif example.md
```

and add `--pdf` flag to generate also a PDF:
```bash
slidefactory.sif --pdf example.md
```

or the same if not using the singularity container:
```bash
python3 $SLIDEFACTORY/convert.py example.md
python3 $SLIDEFACTORY/convert.py --pdf example.md
```

To see more detailed information when running, such as configuration options
and the exact pandoc command, you can add `--verbose` to the commands above.

Use `--help` to see descriptions of all the available arguments.


## Install

Slidefactory consists of two parts: 1) a **git repo** containing files
defining the slide layout (aka themes), pandoc filters, and a convenience
script (`convert.py`) to ease the use of pandoc, and 2) a
**singularity container** with a self-contained software environment that is
tested to work with slidefactory.

Get the source code, build the singularity container and install
slidefactory:
```
git clone https://github.com/csc-training/slide-template
cd slide-template
make
make install
```

As prompted by the installer, please add the environment variable
`SLIDEFACTORY` to your `.bashrc` (or similar) and make sure that the directory
containing the container image is in the `PATH`.

If needed, please see [INSTALL.md](INSTALL.md) for more detailed installation
instructions (and alternative installation options).


### Uninstall

To uninstall slidefactory, you can say `slidefactory.sif --uninstall` (or
without the container `python3 $SLIDEFACTORY/setup/uninstall.py`). If in the
directory containing the source code, also `make uninstall` will work.


## Update

The installed git repo can be updated (to get new themes etc.) with:
```
slidefactory.sif --update
```

or without the singularity container:
```
python3 $SLIDEFACTORY/setup/update.py
```

or just simply by using git:
```
cd $SLIDEFACTORY
git pull
cd -
```

If you want to update the git repo included inside the container (used only if
no local installation is found), then you can add `--container` flag to the
command above. This will unpack the container, update it, and rebuild the
image.

If the container image definition has changed, you need to re-install
slidefactory to get a new version of the image.


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

