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
import shutil
import sys
import subprocess
import tempfile
from urllib.parse import quote as url_quote

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
            error(f'error: {repr(run_args[0])} failed '
                  f'with exit code {p.returncode}')


def error(msg, code=1):
    """Custom error messages"""
    print('')
    print(inspect.cleandoc(msg),
          file=sys.stderr, flush=True)
    print('')
    sys.exit(code)


def find_theme(theme, theme_root):
    is_custom = False
    if os.sep in str(theme):
        is_custom = True
        p = Path(theme)
        if not p.is_dir():
            error(f'Nonexistent theme directory {p.absolute()}')
    else:
        p = theme_root / theme
        if not p.is_dir():
            available_themes = [str(x.name) for x in theme_root.iterdir() if x.is_dir()]
            error(f'Invalid theme {theme}.'
                  f' Available themes: {", ".join(available_themes)}.')
    for fname in ['defaults.yaml', 'template.html', 'csc.css']:
        if not (p / fname).is_file():
            error(f'File {fname} missing from the theme directory'
                  f' {p.absolute()}')
    return p, is_custom


def create_html(input_fpath, html_fpath, args, *,
                theme_dpath, urls_fpath, theme_url,
                pandoc_args=[]):
    run_args = [
        'pandoc',
        f'--defaults={theme_dpath / "defaults.yaml"}',
        f'--template={theme_dpath / "template.html"}',
        f'--metadata-file={urls_fpath}',
        f'--metadata=theme-url:{theme_url}',
        f'--output={html_fpath}',
        input_fpath,
        ]
    run_args += pandoc_args
    run_args += [f'--filter={f}' for f in args.filter]
    run(run_args, verbose=args.verbose, dry_run=args.dry_run)


def create_pdf(html_fpath, pdf_fpath, args):
    run_args = [
        args.browser,
        '--headless',
        '--disable-gpu',
        '--disable-software-rasterizer',
        '--hide-scrollbars',
        '--virtual-time-budget=10000000',
        '--run-all-compositor-stages-before-draw',
        f'--print-to-pdf={pdf_fpath}',
        f'file://{html_fpath.absolute()}?print-pdf'
        ]
    run(run_args, verbose=args.verbose, dry_run=args.dry_run)


def install(path):
    if path.exists():
        error(f'Installation path {path} exists. Exiting.')

    slidefactory_in_container = os.environ['SLIDEFACTORY_ROOT']
    shutil.copytree(slidefactory_in_container, path)

    # Update paths in local urls
    fpath = path / 'urls_local.yaml'
    with open(fpath, 'r+') as f:
        s = f.read().replace(slidefactory_in_container,
                             url_quote(str(path.absolute())))
        f.seek(0)
        f.write(s)


def main():
    parser = argparse.ArgumentParser(description="""Convert a presentation
    from Markdown (or reStructuredText) to reveal.js powered HTML5 using
    pandoc.""")
    parser.add_argument('input', metavar='input.md', nargs='*', type=Path,
            help='filename for presentation source (e.g. in Markdown)')
    parser.add_argument('--output', metavar='prefix',
            help='prefix for output filenames (by default uses the '
            'basename of the input file, i.e. talk.md -> talk.html)')
    parser.add_argument('-t', '--theme', metavar='THEME', default='csc-2016',
            help=(f'presentation theme (default: %(default)s)'))
    parser.add_argument('-f', '--format', metavar='FORMAT', default='pdf',
            choices=['pdf', 'html', 'html-offline', 'html-offline-complete'],
            help='output format (default: %(default)s; available: %(choices)s)')
    parser.add_argument('-b', '--browser', default='chromium-browser',
            help='browser to use for converting PDFs (default: %(default)s)')
    parser.add_argument('--filter', action='append', default=[],
            metavar='filter.py',
            help='pandoc filter script (multiple allowed)')
    parser.add_argument('-n', '--dry-run', '--show-command',
            action='store_true', default=False,
            help='do nothing, only show the full commands to be run')
    parser.add_argument('--verbose', action='store_true', default=False,
            help='be loud and noisy')
    parser.add_argument('--install', metavar='PATH', type=Path,
            help='install local slidefactory to %(metavar)s (ignores all other arguments)')
    parser.add_argument('--slidefactory', metavar='PATH', type=Path,
            help='use local slidefactory from %(metavar)s')
    args = parser.parse_args()

    if args.install:
        install(args.install)
        sys.exit(0)

    if args.format == 'html-offline' and not args.slidefactory:
        error('Install and use local slidefactory in order to create offline htmls.')

    if args.slidefactory:
        slidefactory_root = args.slidefactory
        if not slidefactory_root.is_dir():
            error(f'Slidefactory directory {slidefactory_root.absolute()} does not exist.')
    else:
        slidefactory_root = Path(os.environ['SLIDEFACTORY_ROOT'])

    # choose theme url
    theme_dpath, is_custom_theme = find_theme(args.theme, slidefactory_root / 'theme')
    if (is_custom_theme
            or args.slidefactory
            or args.format in ['pdf', 'html-offline', 'html-offline-complete']):
        theme_url = f'file://{url_quote(str(theme_dpath.absolute()))}/csc.css'
    else:
        theme_url = f'https://cdn.jsdelivr.net/gh/csc-training/slidefactory/theme/{args.theme}/csc.css'

    # choose other urls
    if args.format in ['pdf', 'html-offline', 'html-offline-complete']:
        urls_fpath = slidefactory_root / 'urls_local.yaml'
    else:
        urls_fpath = slidefactory_root / 'urls.yaml'

    pandoc_args = []
    if args.format == 'html-offline-complete':
        pandoc_args += ['--embed-resources']

    # convert files
    for filename in args.input:
        output = filename
        if args.output:
            output = Path(args.output + str(output))

        if args.format == 'pdf':
            # use temporary html output for pdf
            with tempfile.TemporaryDirectory() as tmpdir:
                html = Path(tmpdir) / 'tmp.html'
                pdf = output.with_suffix('.pdf')
                create_html(filename, html, args,
                            theme_dpath=theme_dpath, urls_fpath=urls_fpath,
                            theme_url=theme_url)
                create_pdf(html, pdf, args)
        else:
            html = output.with_suffix('.html')
            create_html(filename, html, args,
                        theme_dpath=theme_dpath, urls_fpath=urls_fpath,
                        theme_url=theme_url, pandoc_args=pandoc_args)


if __name__ == '__main__':
    main()
