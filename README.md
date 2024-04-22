# slidefactory

Tool to generate lecture slides in CSC style from markdown.

This repository contains the recipe to build a new *slidefactory* container
image and the files needed by the tool to generate slides in CSC style.

If you are looking for an example of how to write slides using slidefactory,
please have a look at the
[slidefactory template](https://github.com/csc-training/slidefactory-template)
that can be used as a basis for new courses. Besides some convenience tooling,
it also contains a syntax guide and an example slide set.


## Usage

The container can be run via singularity / apptainer or docker / podman.

### Singularity / apptainer

Fetch the slidefactory container image:

    singularity pull docker://ghcr.io/csc-training/slidefactory:VERSION

Convert the markdown slides to a PDF (default):

    ./slidefactory_VERSION.sif --format pdf slides.md

Convert slides to a regular HTML (an internet access required to display):

    ./slidefactory_VERSION.sif --format html slides.md

Convert slides to a local HTML ([a local version of resources](#local-slidefactory-installation) used - no internet access required):

    ./slidefactory_VERSION.sif --format html-local slides.md

Convert slides to an embedded HTML (images and other resources embedded within the file):

    ./slidefactory_VERSION.sif --format html-embedded slides.md

The embedded HTML files are rather large and [buggy](#known-issues) so
the pdf or the local HTML format is recommended for offline use.
The local HTML requires [a local slidefactory installation](#local-slidefactory-installation).

Change the theme with `--theme`:

    ./slidefactory_VERSION.sif --theme .../path/to/any/theme slides.md

Use help for all other options:

    ./slidefactory_VERSION.sif --help

#### Local slidefactory installation

Copy slidefactory files from the container to a local directory:

    ./slidefactory_VERSION.sif --install my_slidefactory

and follow the instructions.


### Docker / podman

Fetch the slidefactory container image:

    docker pull ghcr.io/csc-training/slidefactory:VERSION

Convert the markdown slides to a PDF (default):

    docker run -it --rm -v "$PWD:$PWD:Z" -w "$PWD" ghcr.io/csc-training/slidefactory:VERSION --format pdf slides.md

All the options work the same way as for singularity
but using the above docker command instead.


## Known issues

* Embedded HTML: incorrect math font
  * Use local HTML or PDF instead
* Embedded and local HTML: Firefox displays incorrect fonts
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
