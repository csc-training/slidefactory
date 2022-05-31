#!/usr/bin/env python3
from pandocfilters import toJSONFilter, Header, attributes
import base64

def _encode(filename):
    with open(filename, 'rb') as fp:
        data = base64.b64encode(fp.read())
        return 'data:image/png;base64,' + data.decode()

def urlencode(key, value, format, meta):
    # urlencode title background
    if 'title_bg' in meta and 'title_bg_encoded' not in meta:
        meta['title_bg'] = {
                't': 'MetaString',
                'c': _encode(meta['title_bg']['c'])
                }
        meta['title_bg_encoded'] = {'t': 'MetaString', 'c': 'yes'}
    # markdown: urlencode images
    if key == 'Header' and value[0] == 1:
        for attribute in value[1][2]:
            if attribute[0] == 'data-background-image':
                attribute[1] = _encode(attribute[1])
        return Header(value[0], value[1], value[2])
    # reST: urlencode images
    elif key == 'Div' and value[1][0]['t'] == 'Header':
        header = value[1][0]['c']
        for attribute in header[1][2]:
            if attribute[0] == 'data-background-image':
                attribute[1] = _encode(attribute[1])
        return Header(header[0], header[1], header[2])

if __name__ == '__main__':
    toJSONFilter(urlencode)
