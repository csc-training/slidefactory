#!/usr/bin/env python3
from pandocfilters import toJSONFilter, Header, attributes

def background(key, value, format, meta):
    # language
    try:
        if meta['lang']['t'] == 'MetaInlines':
            lang = ' '.join([x['c'] for x in meta['lang']['c']])
        else:
            lang = meta['lang']['c']
    except:
        lang = 'en'
    # setup a template with correct path to the theme
    try:
        path = meta['themepath']['c']
    except:
        path = 'theme'
    template = u'{0}/img/%s.png'.format(path)

    # set background image for title slide
    if 'title_bg' not in meta:
        filename = template % 'title-{0}'.format(lang)
        meta['title_bg'] = {'t': 'MetaString', 'c': filename}

    # markdown: special class name triggers the setting of a data background
    #           image unless already present
    if key == 'Header' and value[0] == 1:
        if 'data-background-image' not in [x[0] for x in value[1][2]]:
            for key in ['title', 'author', 'section']:
                if key in value[1][1]:
                    if key == 'title':
                        key = key + '-' + lang
                    value[1][2].append(
                            [u'data-background-image', template % key])
                    break
        return Header(value[0], value[1], value[2])
    # reST: special class name in a container Div triggers the same as above,
    #       but only the modified Header is returned
    elif key == 'Div' and value[1][0]['t'] == 'Header':
        header = value[1][0]['c']
        if 'data-background-image' not in [x[0] for x in header[1][2]]:
            for key in ['title', 'author', 'section']:
                if key in value[0][1]:
                    header[1][1].append(key)
                    if key == 'title':
                        key = key + '-' + lang
                    header[1][2].append(
                            [u'data-background-image', template % key])
                    break
        return Header(header[0], header[1], header[2])

if __name__ == '__main__':
    toJSONFilter(background)
