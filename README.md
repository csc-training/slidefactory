# Description

Experimental template to generate lecture slides in CSC style from markdown
(or reStructuredText).

# Usage

## Install

### Pandoc

See Pandoc's install instructions (http://pandoc.org/installing.html) for
detailed instructions on how to install Pandoc.

Known to work using pandoc 1.17.2 (Debian 9) and on latest Ubuntus.

### Fonts

Additional fonts (Noto Sans and Inconsolata) are needed for the slides. These
can be easily installed on most distros using the package manager.

For example, on Debian 9 the command would be:
```bash
sudo apt-get install fonts-noto fonts-inconsolata
```

## Singularity

### Building the container

Singularity definitions for the Ubuntu Bionic version are in the
`slidefactory.def` file. You can build the container with command:
``` bash
sudo singularity build slidefactory build slidefactory.sqfs slidefactory.def
```
Please note that you have to install the `debootstrap` utility for CentOS/RHEL
before building.

## Convert Markdown to HTML slides

### Quick start

```bash
cd /path/to/slide-template
python convert.py talk.md
```

If you are using singularity:

``` bash
singularity run slidefactory.sqfs talk.md
```

### More information

Options for the helper script (`convert.py`) can be seen with
```bash
python convert.py --help
```

and more detailed information, such as configuration options and the exact
pandoc command, can be seen e.g. with
```bash
python convert.py --verbose talk.md
```

If needed, the URLs of the javascript libraries can also be changed. For more
info, see
```bash
python convert.py --debug talk.md
```

## Show the HTML slides

Using your favourite browser, open the output file (e.g. `talk.html`):

- `open talk.html` (Mac)
- `firefox talk.html` (Linux)

## Generate PDFs

1. Using Chromium (or Chrome), open the HTML slides as shown above.
2. Add `?print-pdf` to the end of the URL and reload. This will change the
   layout to be suitable for PDFs.
   ```
   file:///path/to/files/talk.html?print-pdf
   ```
3. Save the slides to PDF using the built-in print function of the browser.
   Remember to select "None" for margins and to include background graphics.

## Using the template on an existing course (in separate directory)

```bash
git clone https://github.com/csc-training/slide-template
git clone https://github.com/csc-training/advanced-parallel-prog
cd advanced-parallel-prog/docs
ln -s ../../slide-template/theme

# ready to convert slides
python ../../convert.py 04-Advanced-MPI-1.md
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

