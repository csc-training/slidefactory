## Install

Slidefactory consists of two parts: 1) a **git repo** containing files
defining the slide layout (aka themes), pandoc filters, and a convenience
script (`convert.py`) to ease the use of pandoc, and 2) a
**singularity container** with a self-contained software environment that is
tested to work with slidefactory.


### Download source code

```
git clone https://github.com/csc-training/slide-template
cd slide-template
```


### Install full slidefactory

To build the singularity container and install it together with the git
repository, you can simply say:
```
make install
```

| Note: In order to build the container image, singularity needs to be
| installed (https://sylabs.io/guides/latest/admin-guide/installation.html)
| and you will need sudo rights.

If you feel that `make` is too old skool (or your system doesn't have it),
there are also python scripts to do the same:
```
python3 setup/build.py
python3 setup/install.py
```


### Install only git repository (without container)

If you prefer to use your local software environment, you can also just
install the git repo without the singularity container:
```
make git
```

In order to use slidefactory, you need to also install all the dependencies:
  - python3
  - python3-pandocfilters
  - pandoc
  - fonts-noto
  - fonts-inconsolata
  - pandoc-types (1.17.5.4)
  - pandoc-emphasize-code
  - chromium-browser


### Set environment variable SLIDEFACTORY

After installation, you should edit your `.bashrc` or similar, to set the
environment variable `SLIDEFACTORY` to point to the installation location of
the git repository (as prompted by the installer) and to make sure the
directory containing the container image is in your `PATH`.

For example:
```
export SLIDEFACTORY=$HOME/lib/slidefactory
export PATH=$PATH:$HOME/bin
```


### Custom installation location

By default slidefactory will be installed under `bin/` and `lib/` in your
`$HOME` (i.e. `$HOME/bin/slidefactory.sif` and `$HOME/lib/slidefactory`). If
you prefer to install slidefactory in another location, you can use
environment variable `PREFIX` to point to your preferred location.

For example to install under `/some/path/bin` and `/some/path/lib`, you can
say:
```
PREFIX=/some/path make install
```

or to install just the git repo:
```
PREFIX=/some/path make git
```

The python installation script has a similar option, please see
`setup/install.py --help` for more details.

When uninstalling from a custom location, one needs to provide the same
`PREFIX` unless the environment variable `SLIDEFACTORY` is set correctly.
