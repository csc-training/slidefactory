#!/usr/bin/env python3
# ------------------------------------------------------------------------- #
# Function: Pandoc JSON filter that gives each slide heading its own `id`   #
#           attribute, matching the identifier pandoc's reveal.js writer   #
#           already puts on the wrapping <section>.                        #
# ------------------------------------------------------------------------- #
#
# Pandoc's reveal.js writer moves a Header's identifier onto the wrapping
# <section> and omits it from the <hN> tag itself. Pagefind's automatic
# per-slide search anchors only recognize (non-empty) heading elements that
# carry their own id, so without this every search hit would link to the
# deck's first slide instead of the one that actually matched.
#
# Any other key-value attribute on a Header (unlike the identifier) is
# passed straight through onto both the <section> and the <hN> tag, so
# adding a plain "id" key-value pair here - separate from the special
# identifier field - is enough to make pandoc's own writer put a real `id`
# directly on the heading tag, with no HTML post-processing required.
from pandocfilters import toJSONFilter, Header


def duplicate_heading_id(key, value, format, meta):
    if key != 'Header':
        return None
    level, attr, inlines = value
    identifier, classes, keyvals = attr
    if identifier and not any(k == 'id' for k, v in keyvals):
        keyvals = keyvals + [['id', identifier]]
        return Header(level, [identifier, classes, keyvals], inlines)


if __name__ == '__main__':
    toJSONFilter(duplicate_heading_id)
