#!/usr/bin/python
# -*- coding: ISO-8859-1 -*-
#---------------------------------------------------------------------------#
# Function: Convert a presentation from Markdown (or reStructuredText) to   #
#           reveal.js powered HTML5 using pandoc.                           #
# Usage: python convert.py talk.md                                          #
# Help:  python convert.py --help                                           #
#---------------------------------------------------------------------------#
import argparse
import os

# reveal.js configuration
config = [
        'theme=csc',
        'width=1920',
        'height=1080',
        'history=true',
        'center=false',
        'controls=false',
        'transition=none',
        'backgroundTransition=none'
        ]

# pandoc filters
filters = ['contain-slide.py', 'csc-specials.py']


def remove_duplicates(config):
    """Remove duplicate entries from a list of config options."""
    tmp = {}
    order = []
    for item in config:
        try:
            key, value = item.split('=', 1)
        except ValueError:
            raise ValueError, 'Malformed config option: %s' % item
        tmp[key] = value
        if key not in order:
            order.append(key)
    return [key + '=' + tmp[key] for key in order]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="""Convert a presentation
    from Markdown (or reStructuredText) to reveal.js powered HTML5 using
    pandoc.""")
    parser.add_argument('input', metavar='input.md',
            help='filename for presentation source (e.g. in Markdown)')
    parser.add_argument('output', metavar='output.html', nargs='?',
            help='filename for HTML5 presentation (optional; by default '
            + 'uses the basename of input, i.e. talk.md -> talk.html)')
    parser.add_argument('-l', '--local', action='store_true', default=False,
            help='use local copy of reveal.js (in sub-directory reveal.js/)')
    parser.add_argument('--config', action='append', default=config,
            metavar='name=value',
            help='reveal.js config option (multiple allowed)')
    parser.add_argument('--filter', action='append', default=filters,
            metavar='filter.py',
            help='pandoc filter script (multiple allowed)')
    parser.add_argument('--reveal', help=argparse.SUPPRESS,
            default='http://rawgit.com/mlouhivu/reveal.js/csc')
    parser.add_argument('--mathjax', help=argparse.SUPPRESS,
            default='http://rawgit.com/mathjax/MathJax/2.7.1/MathJax.js?config=TeX-AMS_HTML-full')
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

    # if output is not defined, construct it based on input filename
    if not args.output:
        base, ext = os.path.splitext(args.input)
        args.output = base + '.html'
    # if using a remote reveal.js, add the URL to config options
    if not args.local:
        args.config.insert(0, 'revealjs-url=' + args.reveal)
    # check config options and remove duplicates (if any)
    config = remove_duplicates(args.config)

    # prepare command-line arguments
    flags = {
            'input':   args.input,
            'output':  args.output,
            'config':  ' '.join('-V ' + x for x in config),
            'filter':  ' '.join('--filter ' + x for x in args.filter),
            'mathjax': args.mathjax
            }
    # construct the pandoc command
    cmd = ('pandoc {input} -s -t revealjs {config} --mathjax={mathjax} ' \
            + '{filter} -o {output}').format(**flags)

    # display extra info?
    if args.verbose or args.dry_run:
        print('\nReveal.js configuration:')
        for x in config:
            print('  {0}'.format(x))
        print('\nPandoc filters:')
        if filters:
            for x in filters:
                print('  {0}'.format(x))
        else:
            print('  (none)')
        print('\nPandoc command:')
        print('  {0}\n'.format(cmd))

    # execute pandoc
    if not args.dry_run:
        os.system(cmd)
