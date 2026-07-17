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

    ./slidefactory_VERSION.sif slides --format pdf slides.md

Convert slides to a regular HTML (an internet access required to display):

    ./slidefactory_VERSION.sif slides --format html slides.md

Convert slides to a local HTML ([a local version of resources](#local-slidefactory-installation) used - no internet access required):

    ./slidefactory_VERSION.sif slides --format html-local slides.md

Convert slides to an embedded HTML (images and other resources embedded within the file):

    ./slidefactory_VERSION.sif slides --format html-embedded slides.md

The embedded HTML files are rather large and [buggy](#known-issues) so
the pdf or the local HTML format is recommended for offline use.
The local HTML requires [a local slidefactory installation](#local-slidefactory-installation).

Change the theme with `--theme`:

    ./slidefactory_VERSION.sif slides --theme .../path/to/any/theme slides.md

Use help for all other options:

    ./slidefactory_VERSION.sif slides --help


#### Themes

Two themes are bundled:

* `csc-2026` (default) - the current CSC brand: new color palette, the
  `Nunito Sans` font, and support for the [CC license badge](#license) on
  the title slide.
* `csc-old` - the previous CSC look (formerly named `csc-plain`), kept for
  continuity with older material.

Select a bundled theme by name by adding `--theme csc-old` with the run command. 


#### Illustrations

21 CSC brand illustrations (`CSC_Characters_01.png` - `CSC_Characters_21.png`)
are available for use in slides. They are not stored in this repository -
instead they are downloaded from an external source and bundled into the
container image at build time (see `Dockerfile`), the same way fonts and
reveal.js are handled. Reference them in `slides.md` by filename, without
needing to know where slidefactory is installed:

    ![](csc_illustrations/CSC_Characters_01.png)

Including the illustrations in the image is optional. They are included by
default; skip them with:

    make build INCLUDE_ILLUSTRATIONS=false


#### License

Add a `license` key to the YAML metadata block at the top of `slides.md`
to display a Creative Commons badge and link on the title slide (theme
`csc-2026` only):

    ---
    title:  My Slides
    license: by
    ---

Valid values are the standard CC 4.0 license slugs: `by`, `by-sa`, `by-nd`,
`by-nc`, `by-nc-sa`, `by-nc-nd`. If `license` is left out, no license
information is shown.


#### Build pages for a project

Use pages sub-command to create an index page and convert all slides:

    ./slidefactory_VERSION.sif pages about.yml build


#### Local slidefactory installation

Copy slidefactory files from the container to a local directory:

    ./slidefactory_VERSION.sif install my_slidefactory

and follow the instructions.


### Docker / podman

The commands below work identically with `docker` or `podman` - just swap
the binary name. 

Fetch the slidefactory container image:

    docker/podman pull ghcr.io/csc-training/slidefactory:VERSION

Convert the markdown slides to a PDF (default):

    docker/podman run -it --rm -v "$PWD:$PWD:Z" -w "$PWD" ghcr.io/csc-training/slidefactory:VERSION slides --format pdf slides.md

All the options work the same way as for singularity
but using the above docker/podman command instead.


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
