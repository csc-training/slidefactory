#!/usr/bin/python
#---------------------------------------------------------------------------#
# Function: Convert a presentation from Markdown (or reStructuredText) to   #
#           reveal.js powered HTML5 using pandoc.                           #
# Usage: python convert.py talk.md                                          #
# Help:  python convert.py --help                                           #
#---------------------------------------------------------------------------#
import argparse
import inspect
import os
import sys
import subprocess

def error(msg, code=1):
    print(inspect.cleandoc(msg))
    print('')
    if code == 1: # setup error (invalid path etc.)
        print('Please see README.md for installation instructions.')
    sys.exit(code)

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

# check environment variables
for env in ['SLIDEFACTORY', 'SLIDEFACTORY_CONTAINER']:
    path = os.environ.get(env, False)
    if path and not os.path.isdir(path):
        error('Invalid path in environment variable {env}: {path}'.format(
            env=env, path=os.environ[env]))

# figure out the paths to files
#   order of preference: current working directory, environment variable,
#                        default installation path, location of this script
no_local_theme = False
_not_installed = False
_default_path = os.path.join(
        os.environ.get('HOME', os.path.expanduser('~')), 'lib/slidefactory')
cwd = os.getcwd()
# .. base path
for path in [os.environ.get('SLIDEFACTORY', False),
             _default_path,
             os.environ.get('SLIDEFACTORY_CONTAINER', False)]:
    if path and os.path.isdir(path):
        break
else:
    path = os.path.dirname(
            os.path.abspath(inspect.getsourcefile(lambda: None)))
    _not_installed = True
# .. path to themes
path_themes = os.path.join(cwd, 'theme')
if not os.path.isdir(path_themes):
    path_themes = os.path.join(path, 'theme')
    if _not_installed:
        no_local_theme = True
    if not os.path.isdir(path_themes):
        error('Invalid theme path: {0}'.format(
            os.path.join('.', os.path.relpath(path_themes, start=cwd))))
# .. path to filters
for path_filters in [os.path.join(cwd, 'filter'),
                    os.path.join(path, 'filter')]:
    if os.path.isdir(path_filters):
        break
else:
    error('Invalid filter path: {0}'.format(
            os.path.join('.', os.path.relpath(path_filters, start=cwd))))

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
            error('Malformed config option: %s' % item, code=2)
        tmp[key] = value
        if key not in order:
            order.append(key)
    return [key + '=' + tmp[key] for key in order]

# highlight styles in pandoc
highlight_styles = subprocess.check_output(
        'pandoc --list-highlight-styles', shell=True).decode().split()

# find existing presentation themes
try:
    themes = [x for x in os.listdir(path_themes)
              if os.path.isdir(os.path.join('theme', x))]
except OSError:
    error('Invalid theme path: {0}'.format(path_themes))


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
    parser.set_defaults(html=True)
    parser.add_argument('-p', '--pdf', action='store_true', default=False,
            help='convert HTMLs to PDFs')
    parser.add_argument('-c', '--self-contained',
            action='store_true', default=False,
            help='produce as self-contained HTMLs as possible')
    parser.add_argument('-b', '--browser', default='chromium-browser',
            help='browser to use for converting PDFs (default: %(default)s)')
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
    parser.add_argument('--as-container', help=argparse.SUPPRESS,
            action='store_true', default=False)
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

    if args.as_container and no_local_theme:
        args.pdf = True
        args.html = False
        if args.verbose:
            print('Could not find a local installation of slidefactory. '
                    + 'Converting to PDFs only.')
            print('If you want HTMLs, please set correct path to the '
                    + 'environment variable SLIDEFACTORY or install '
                    + 'slidefactory with:')
            print('  slidefactory.sif --install')
            print('')

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

    # self contained HTML
    if args.self_contained:
        urlencode = os.path.join(path_filters, 'url-encode.py')
        if urlencode not in args.filter:
            args.filter.append(urlencode)
        meta.append('revealjs-css-url=' + os.path.join(path, 'reveal.js'))
        contained = '--self-contained'
    else:
        meta.append('revealjs-css-url=' + args.reveal)
        contained = ''

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
            'template': os.path.join(path_themes, args.theme, 'template.html'),
            'contained': contained,
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
        if args.output:
            base = args.output + base
        html = base + '.html'
        # add filenames to the command-line arguments
        flags['input'] = filename
        flags['output'] = html

        # construct the pandoc command
        cmd = ('pandoc {input} -s -t revealjs --template={template} '
                + '{meta} {vars} {config} {contained} '
                + '--mathjax={mathjax} --highlight-style={style} '
                + '{filter} -o {output}').format(**flags)

        # display pandoc command?
        if args.verbose or args.dry_run:
            print('\nPandoc command:')
            print('  {0}\n'.format(cmd))

        # execute pandoc
        if not args.dry_run:
            os.system(cmd)

        # convert to pdfs?
        if args.pdf:
            pdf = base + '.pdf'
            flags = [
                    '--headless',
                    '--virtual-time-budget=10000',
                    '--run-all-compositor-stages-before-draw',
                    ]
            cmd = ('{browser} {flags} --print-to-pdf={pdf} '
                    + 'file://{path}/{html}?print-pdf').format(
                            browser=args.browser,
                            flags=' '.join(flags),
                            pdf=pdf,
                            path=os.path.abspath(cwd),
                            html=html)
            if args.verbose or args.dry_run:
                print('')
                print('Command to convert to PDF:')
                print('  {0}'.format(cmd))
                print('')
            if not args.dry_run:
                subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)
