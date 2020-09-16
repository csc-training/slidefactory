from pandocfilters import toJSONFilter, Header, attributes

def contain(key, value, format, meta):
#    raise ValueError, 'key=%s, value=%s, format=%s, meta=%s' % \
#            (repr(key), repr(value), repr(format), repr(meta))
    if key == 'Header' and value[0] == 1:
        if 'data-background-size' not in [x[0] for x in value[1][2]]:
            value[1][2].append([u'data-background-size', u'contain'])
        return Header(value[0], value[1], value[2])
    elif key == 'HorizontalRule':
        name = "section"
        attr = [[u'data-background', u'empty-slide'],
                [u'data-background-size', u'contain']]
        return Header(1, (name, [], attr), [])

if __name__ == '__main__':
    toJSONFilter(contain)
