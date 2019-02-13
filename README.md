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
