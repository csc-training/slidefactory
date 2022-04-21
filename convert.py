#!/usr/bin/python
#---------------------------------------------------------------------------#
# Function: Convert a presentation from Markdown (or reStructuredText) to   #
#           reveal.js powered HTML5 using pandoc.                           #
# Usage: python convert.py talk.md                                          #
# Help:  python convert.py --help                                           #
#---------------------------------------------------------------------------#
import argparse
import os
import sys

# reveal.js configuration
config = [
        'width=1920',
        'height=1080',
        'history=true',
        'center=false',
        'controls=false',
        'transition=none',
        'backgroundTransition=none'
        ]

# figure out the paths to files
#   order of preference: current working directory, environment variable,
#                        default installation path, location of this script
_default_path = os.path.join(
        os.environ.get('HOME', os.path.expanduser('~')), 'lib/slidefactory')
cwd = os.getcwd()
try:
    path = os.environ['SLIDEFACTORY']
    if not os.path.isdir(path):
        raise FileNotFoundError('Invalid root path: {0}'.format(path))
except KeyError:
    if os.path.isdir(_default_path):
        path = _default_path
    else:
        path = os.path.abspath('.')
for path_themes in [os.path.join(cwd, 'theme'),
                   os.path.join(path, 'theme')]:
    if os.path.isdir(path_themes):
        break
else:
    raise FileNotFoundError('Invalid theme path: {0}'.format(path_themes))
for path_filters in [os.path.join(cwd, 'filter'),
                    os.path.join(path, 'filter')]:
    if os.path.isdir(path_filters):
        break
else:
    raise FileNotFoundError('Invalid filter path: {0}'.format(path_filters))

# pandoc filters
filters = [os.path.join(path_filters, x) for x in [
           'contain-slide.py', 'background-image.py']]
if os.path.exists('/usr/local/bin/pandoc-emphasize-code'):
    filters.append('/usr/local/bin/pandoc-emphasize-code')

def remove_duplicates(config):
    """Remove duplicate entries from a list of config options."""
    tmp = {}
    order = []
    for item in config:
        try:
            key, value = item.split('=', 1)
        except ValueError:
            raise ValueError('Malformed config option: %s' % item)
        tmp[key] = value
        if key not in order:
            order.append(key)
    return [key + '=' + tmp[key] for key in order]

# highlight styles in pandoc
highlight_styles = ['pygments', 'tango', 'espresso', 'zenburn', 'kate', \
        'monochrome', 'breezedark', 'haddock']

# find existing presentation themes
try:
    themes = [x for x in os.listdir(path_themes)
              if os.path.isdir(os.path.join('theme', x))]
except OSError:
    raise FileNotFoundError('Invalid theme path: {0}'.format(path_themes))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="""Convert a presentation
    from Markdown (or reStructuredText) to reveal.js powered HTML5 using
    pandoc.""")
    parser.add_argument('input', metavar='input.md', nargs='+',
            help='filename for presentation source (e.g. in Markdown)')
    parser.add_argument('--output', metavar='prefix',
            help='prefix for output filenames (by default uses the '
            'basename of the input file, i.e. talk.md -> talk.html)')
    parser.add_argument('-t', '--theme', default='csc-2016',
            choices=themes, metavar='THEME',
            help='presentation theme: ' + ', '.join(themes) \
                    + ' (default: csc-2016)')
    parser.add_argument('-s', '--style', default='pygments',
           choices=highlight_styles, metavar='name',
           help='code highlight style: ' + ', '.join(highlight_styles) \
                   + ' (default: pygments)')
    parser.add_argument('--config', action='append', default=config,
            metavar='key=value',
            help='reveal.js config option (multiple allowed)')
    parser.add_argument('--filter', action='append', default=filters,
            metavar='filter.py',
            help='pandoc filter script (multiple allowed)')
    parser.add_argument('--reveal', help=argparse.SUPPRESS,
            default='https://mlouhivu.github.io/static-engine/reveal/3.5.0')
    parser.add_argument('--mathjax', help=argparse.SUPPRESS,
            default='https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js?config=TeX-AMS_HTML-full')
    parser.add_argument('--dry-run', '--show-command',
            action='store_true', default=False,
            help='do nothing, only show the full pandoc command'
            + ' (together with config options and filters used)')
    parser.add_argument('--verbose', action='store_true', default=False,
            help='be loud and noisy')
    parser.add_argument('--debug', action='store_true', default=False,
            help='show debug options')
    args = parser.parse_args()

    # show hidden debug options and exit?
    if args.debug:
        parser.print_help()
        print('\ndebug options:')
        print('  --reveal              URL of the reveal.js to use')
        print('    : ' + args.reveal)
        print('  --mathjax             URL of the MathJax.js to use')
        print('    : ' + args.mathjax)
        parser.exit()

    # check config options and remove duplicates (if any)
    config = remove_duplicates(args.config)

    # meta variables to pandoc
    meta = [
            'theme=' + args.theme,
            'themepath=' + os.path.join(path_themes, args.theme),
            'revealjs-url=' + args.reveal,
            ]
    # extra template variables to pandoc
    variables = [
            ]

    # prepare command-line arguments
    flags = {
            'style':   args.style,
            'input':   args.input,
            'output':  args.output,
            'meta':    ' '.join('-M ' + x for x in meta),
            'vars':    ' '.join('-V ' + x for x in variables),
            'config':  ' '.join('-V ' + x for x in config),
            'filter':  ' '.join('--filter ' + x for x in args.filter),
            'mathjax': args.mathjax,
            'template': os.path.join(path_themes, args.theme, 'template.html')
            }

    # display extra info?
    if args.verbose or args.dry_run:
        print('Using theme from: ' + os.path.join(path_themes, args.theme))
        print('\nReveal.js configuration:')
        for x in config:
            print('  {0}'.format(x))
        print('\nPandoc filters:')
        if filters:
            for x in filters:
                print('  {0}'.format(x))
        else:
            print('  (none)')
        print('\nPandoc variables:')
        if meta or variables:
            for x in meta:
                print('  -M {0}'.format(x))
            for x in variables:
                print('  -V {0}'.format(x))
        else:
            print('  (none)')

    # convert files
    for filename in args.input:
        # figure out the output filename
        base, ext = os.path.splitext(filename)
        if not args.output:
            output = base
        else:
            output = args.output + base
        if not output.endswith('.html'):
            output += '.html'
        # add filenames to the command-line arguments
        flags['input'] = filename
        flags['output'] = output

        # construct the pandoc command
        cmd = ('pandoc {input} -s -t revealjs --template={template} '
                + '{meta} {vars} {config} '
                + '--mathjax={mathjax} --highlight-style={style} '
                + '{filter} -o {output}').format(**flags)

        # display pandoc command?
        if args.verbose or args.dry_run:
            print('\nPandoc command:')
            print('  {0}\n'.format(cmd))

        # execute pandoc
        if not args.dry_run:
            os.system(cmd)
