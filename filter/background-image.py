from pandocfilters import toJSONFilter, Header, attributes

template=u'img/%s.png'

def cscify(key, value, format, meta):
    # markdown: special class names trigger loading of a data background image
    #           and replacement with a corresponding generic class name
    if key == 'Header' and value[0] == 1:
        if 'data-background' not in [x[0] for x in value[1][2]]:
            for key in ['title-en', 'title-fi', 'author']:
                if key in value[1][1]:
                    value[1][1].remove(key)
                    value[1][2].append([u'data-background', template % key])
                    if key == 'author':
                        value[1][1].append(u'author-slide')
                    else:
                        value[1][1].append(u'title-slide')
        return Header(value[0], value[1], value[2])
    # reST: special class name in a container Div triggers the same as above,
    #       but only the modified Header is returned
    elif key == 'Div' and value[1][0]['t'] == 'Header':
        for key in ['title-en', 'title-fi', 'author']:
            if key in value[0][1]:
                header = value[1][0]['c']
                header[1][2].append([u'data-background', template % key])
                if key == 'author':
                    header[1][1].append(u'author-slide')
                else:
                    header[1][1].append(u'title-slide')
                return Header(header[0], header[1], header[2])

if __name__ == '__main__':
    toJSONFilter(cscify)
