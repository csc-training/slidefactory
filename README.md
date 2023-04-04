# slidefactory

Tool to generate lecture slides in CSC style from markdown.

This repository contains the recipe to build a new *slidefactory* container
image and the files needed by the tool to generate slides in CSC style.

If you are looking for an example of how to write slides using slidefactory,
please have a look at the empty
[slidefactory template](https://github.com/csc-training/slidefactory-template)
that can be used as a basis for new courses. Besides some convenience tooling,
it also contains a syntax guide and an example slide set.


## Usage

Convert slides from Markdown to HTML:
```bash
slidefactory.sif example.md
```

or the same if not using the singularity container:
```bash
python3 $SLIDEFACTORY/convert.py example.md
```

To see more detailed information when running, such as configuration options
and the exact pandoc command, you can add `--verbose` to the commands above.

Use `--help` to see descriptions of all the available arguments.


### option: `--pdf`

To generate also a PDF version of the slides, add `--pdf` to the command
above, e.g.:

```bash
slidefactory.sif --pdf example.md
```


### option: `--self-contained`

One can also use the option `--self-contained` to embed images and other
assets into the HTML file with the aim to produce a file that is as
"self-contained" as possible.

```bash
slidefactory.sif --self-contained example.md
```

Beware that **files produces in this way can become very large** and that not
everything will be contained in the HTML file, so e.g. math formulas will
require internet connection to work.


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
without the container `python3 $SLIDEFACTORY/setup/uninstall.py`). If one is
in the directory containing the source code, `make uninstall` will also work.


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


## Example: template for new courses

Examples and more information on how to write slides using slidefactory are
available in the
[slidefactory template](https://github.com/csc-training/slidefactory-template)
repository. The repository contains an empty template for slidefactory slides
that can be used as a basis for new courses. Please read the `README.md`
included in the repository for more details.
