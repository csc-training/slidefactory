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

    singularity pull slidefactory.sif docker://ghcr.io/csc-training/slidefactory:2.0.0


Convert the markdown slides to a PDF (default):

    ./slidefactory.sif --format pdf slides.md

or to a regular HTML (requires an internet access to display):

    ./slidefactory.sif --format html slides.md

or to a standalone HTML (images and other resources embedded within the file):

    ./slidefactory.sif --format html-standalone slides.md

The standalone HTML files are rather large.
For offline use, `--format html-local` with
[a local slidefactory installation](#local-slidefactory-installation)
can be more practical.

Change the theme with `--theme`:

    ./slidefactory.sif --theme csc-2016 slides.md


Use help for available themes and all other options:

    ./slidefactory.sif --help

See also [Advanced usage](#advanced-usage).


## Advanced usage


### Custom themes

It's possible to use theme from any path as long as the contents
follow similar structure as the existing themes
(see for example [csc-2016](theme/csc-2016)):

    ./slidefactory.sif --theme path/to/my/theme slides.md


### Local slidefactory installation

Install slidefactory files from the container to a local directory:

    ./slidefactory.sif --install ~/slidefactory

and create an alias for using the local installation:

    alias slidefactory="singularity exec ~/slidefactory/slidefactory.sif ~/slidefactory/slidefactory.py"


Then use the local slidefactory installation:

    slidefactory --format pdf slides.md

Local installation enables creating a local HTML
(doesn't require internet access but uses
the installed local copy of web resources):

    slidefactory --format html-local slides.md


## Known issues

* Standalone HTML: incorrect math font
  * Use local HTML or PDF instead
* Standalone and local HTML: Firefox displays incorrect fonts
  * Use Chromium or Chrome instead


## Building and updating the container image

The container recipe is encoded in `Dockerfile` and `Makefile`.

If you don't have docker or podman, install using

    sudo apt install podman-docker

If using podman, define

    export BUILDAH_FORMAT=docker

Build the image

    make build

Login using GitHub Personal Access Token in order to be able to push:

    docker login ghcr.io

Push the image

    make push

For testing, you can also convert the local image to singularity:

    make singularity
