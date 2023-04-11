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
import shlex
import sys
import subprocess

from pathlib import Path


def run(run_args, *, verbose=False, dry_run=False):
    run_args = [str(a) for a in run_args]

    if verbose or dry_run:
        print(shlex.join(run_args), flush=True)

    if not dry_run:
        p = subprocess.run(run_args,
                           check=False, shell=False,
                           capture_output=True)
        if p.returncode != 0:
            print(f'error: {repr(run_args[0])} failed '
                  f'with exit code {p.returncode}',
                  file=sys.stderr, flush=True)
            print(p.stderr.decode(),
                  file=sys.stderr, flush=True)
            sys.exit(1)


def error(msg, code=1):
    """Custom error messages"""
    print('')
    print(inspect.cleandoc(msg))
    print('')
    if code == 1: # setup error (invalid path etc.)
        print('Please see README.md for installation instructions.')
    sys.exit(code)


def get_themes(path_themes):
    """Find existing presentation themes."""
    try:
        themes = [x for x in os.listdir(path_themes)
                  if os.path.isdir(os.path.join(path_themes, x))]
    except OSError:
        error('Invalid theme path: {0}'.format(path_themes))
    return themes


def main():
    root = Path(os.environ['SLIDEFACTORY_ROOT'])
    theme_root = Path(os.environ['SLIDEFACTORY_THEME_ROOT'])
    available_themes = get_themes(theme_root)
    default_theme = 'csc-2016'

    parser = argparse.ArgumentParser(description="""Convert a presentation
    from Markdown (or reStructuredText) to reveal.js powered HTML5 using
    pandoc.""")
    parser.add_argument('input', metavar='input.md', nargs='+', type=Path,
            help='filename for presentation source (e.g. in Markdown)')
    parser.add_argument('--output', metavar='prefix',
            help='prefix for output filenames (by default uses the '
            'basename of the input file, i.e. talk.md -> talk.html)')
    parser.add_argument('-t', '--theme', default=default_theme,
            choices=available_themes, metavar='THEME',
            help=(f'presentation theme: {", ".join(available_themes)}'
                  f' (default: {default_theme})'))
    parser.add_argument('-p', '--pdf', action='store_true', default=False,
            help='convert HTMLs to PDFs')
    parser.add_argument('-c', '--self-contained',
            action='store_true', default=False,
            help='produce as self-contained HTMLs as possible')
    parser.add_argument('-b', '--browser', default='chromium-browser',
            help='browser to use for converting PDFs (default: %(default)s)')
    parser.add_argument('--filter', action='append', default=[],
            metavar='filter.py',
            help='pandoc filter script (multiple allowed)')
    parser.add_argument('--dry-run', '--show-command',
            action='store_true', default=False,
            help='do nothing, only show the full commands to be run')
    parser.add_argument('--verbose', action='store_true', default=False,
            help='be loud and noisy')
    args = parser.parse_args()

    # self contained HTML
    if args.self_contained:
        urlencode = os.path.join(path['filters'], 'url-encode.py')
        if urlencode not in args.filter:
            args.filter.append(urlencode)
        contained = '--self-contained'
    else:
        contained = ''

    # convert files
    theme_dpath = theme_root / args.theme

    for filename in args.input:
        html = filename.with_suffix('.html')
        if args.output:
            html = Path(args.output + str(html))

        run_args = [
            'pandoc',
            f'--defaults={theme_dpath / "defaults.yaml"}',
            f'--template={theme_dpath / "template.html"}',
            f'--metadata-file={root / "urls.yaml"}',
            f'--metadata=theme-url:https://cdn.jsdelivr.net/gh/csc-training/slidefactory/theme/{args.theme}/csc.css',
            f'--output={html}',
            filename,
            ]
        run_args += [f'--filter={f}' for f in args.filter]
        run(run_args, verbose=args.verbose, dry_run=args.dry_run)


        if args.pdf:
            pdf = html.with_suffix('.pdf')
            run_args = [
                args.browser,
                '--headless',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--hide-scrollbars',
                '--virtual-time-budget=10000000',
                '--run-all-compositor-stages-before-draw',
                f'--print-to-pdf={pdf}',
                f'file://{html.absolute()}?print-pdf'
                ]
            run(run_args, verbose=args.verbose, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
