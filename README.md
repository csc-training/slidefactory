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

Fetch the slidefactory container image:
```bash
singularity pull slidefactory.sif docker://ghcr.io/csc-training/slidefactory:2.0.0
```

Convert the markdown slides to a PDF (default):
```bash
./slidefactory.sif --format pdf slides.md
```
or to a regular HTML (requires an internet access to display):
```bash
./slidefactory.sif --format html slides.md
```
or to a standalone HTML with images and other resources embedded within the file:
```bash
./slidefactory.sif --format html-standalone slides.md
```

Change the theme with `--theme`:
```bash
./slidefactory.sif --theme csc-2016 slides.md
```

Use help for available themes and all other options:
```bash
./slidefactory.sif --help
```
See also [Advanced usage](#advanced-usage).


## Advanced usage


### Custom themes

It's possible to use theme from any path as long as the contents
follow similar structure as the existing themes
(see for example [csc-2016](theme/csc-2016)):
```bash
./slidefactory.sif --theme path/to/my/theme slides.md
```

### Local slidefactory installation

Install slidefactory files from the container to a local directory:
```bash
./slidefactory.sif --install $HOME/slidefactory
```
and create an alias for using the local installation:
```bash
alias local-slidefactory="singularity exec ./slidefactory.sif $HOME/slidefactory/convert.py"
```

Then use the local slidefactory installation:
```bash
local-slidefactory --format pdf slides.md
```

Local installation enables creating a local HTML
(doesn't require internet access but uses
the installed local copy of web resources):
```bash
local-slidefactory --format html-local slides.md
```


## Building and updating the container image

The container recipe is encoded in `Dockerfile` and `Makefile`.

Set image path for building and pushing:
```bash
export IMAGE_ROOT=ghcr.io/csc-training
```

Login using GitHub personal access token:
```bash
podman login ${IMAGE_ROOT%%/*}
```

Build and push the image:
```bash
make
make push
```

For testing, convert the local image to singularity:
```bash
make singularity
```
