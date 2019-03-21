from pandocfilters import toJSONFilter, Header, attributes

def fix_head(key, value, format, meta):
    if key == 'Header' and value[0] == 1:
        if value[2][0]['t'] == 'Strong' and type(value[2][0]['c']) is list:
            value[2] = value[2][0]['c']
        return Header(value[0], value[1], value[2])

if __name__ == '__main__':
    toJSONFilter(fix_head)
