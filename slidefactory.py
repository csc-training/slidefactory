#!/usr/bin/python
#---------------------------------------------------------------------------#
# Function: Convert a presentation from Markdown (or reStructuredText) to   #
#           reveal.js powered HTML5 using pandoc.                           #
# Usage: python slidefactory.py talk.md                                     #
# Help:  python slidefactory.py --help                                      #
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


slidefactory_root = Path(__file__).absolute().parent


def run(run_args, *, verbose=False, dry_run=False):
    run_args = [str(a) for a in run_args]

    if verbose or dry_run:
        info(shlex.join(run_args))

    if not dry_run:
        p = subprocess.run(run_args,
                           check=False, shell=False,
                           capture_output=True)
        if p.returncode != 0:
            error(f'error: {repr(run_args[0])} failed '
                  f'with exit code {p.returncode}')

def info(msg):
    print(msg, flush=True)


def error(msg, code=1):
    """Custom error messages"""
    print('')
    print(inspect.cleandoc(msg),
          file=sys.stderr, flush=True)
    print('')
    sys.exit(code)


def get_available_themes(theme_root):
    available_themes = sorted([str(x.name) for x in theme_root.iterdir() if x.is_dir()])
    return available_themes


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
            available_themes = get_available_themes(theme_root)
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

    path = path.absolute()

    # Copy slidefactory files
    info(f'Copy {slidefactory_root} to {path}')
    shutil.copytree(slidefactory_root, path)

    # Update paths in local urls
    fpath = path / 'urls_local.yaml'
    info(f'Update {fpath}')
    with open(fpath, 'r+') as f:
        s = f.read().replace(url_quote(str(slidefactory_root)),
                             url_quote(str(path.absolute())))
        f.seek(0)
        f.write(s)

    # Copy singularity image
    sif = Path(os.environ['SINGULARITY_CONTAINER'])
    local_sif = path / sif.name
    info(f'Copy {sif} to {local_sif}')
    shutil.copy2(sif, local_sif)

    info('\nTo activate the local installation, run:\n\n'
         f'  alias slidefactory="singularity exec \'{local_sif}\' \'{path}/{Path(__file__).name}\'"' '\n'
         '\nAfter that, use `slidefactory` command, for example:\n\n'
         f'  slidefactory --format html-local slides.md\n')


def main():
    theme_root = slidefactory_root / 'theme'

    parser = argparse.ArgumentParser(description="""Convert a presentation
    from Markdown (or reStructuredText) to reveal.js powered HTML5 using
    pandoc.""")
    parser.add_argument('input', metavar='input.md', nargs='*', type=Path,
            help='filename for presentation source (e.g. in Markdown)')
    parser.add_argument('--output', metavar='prefix',
            help='prefix for output filenames (by default uses the '
            'basename of the input file, i.e. talk.md -> talk.html)')
    parser.add_argument('-t', '--theme', metavar='THEME', default='csc-2016',
            help=('presentation theme name or path (default: %(default)s, '
                  f'available: {", ".join(get_available_themes(theme_root))})'))
    parser.add_argument('-f', '--format', metavar='FORMAT', default='pdf',
            choices=['pdf', 'html', 'html-local', 'html-standalone'],
            help='output format (default: %(default)s; available: %(choices)s)')
    parser.add_argument('-b', '--browser', default='chromium-browser',
            help='browser to use for converting PDFs (default: %(default)s)')
    parser.add_argument('--filter', action='append', default=[],
            metavar='filter.py',
            help='pandoc filter script (multiple allowed)')
    parser.add_argument('-n', '--dry-run', '--show-command',
            action='store_true', default=False,
            help='do nothing, only show the full commands to be run')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
            help='be loud and noisy')
    parser.add_argument('-q', '--quiet', action='store_true', default=False,
            help='suppress all output except errors')
    parser.add_argument('--install', metavar='PATH', type=Path,
            help='install local slidefactory to %(metavar)s (ignores all other arguments)')
    args = parser.parse_args()

    if args.quiet:
        global info

        def info(*args, **kwargs):
            pass


    if args.install:
        install(args.install)
        sys.exit(0)

    in_container = slidefactory_root == Path('/slidefactory')

    if args.format == 'html-local' and in_container:
        sif = Path(os.environ['SINGULARITY_CONTAINER'])
        error('Install and use local slidefactory in order to create local offline htmls.'
              '\n\nIn short, run:\n\n'
              f'  {sif} --install ~/slidefactory\n'
              '\nand follow the instructions (see README for details).'
              )

    if not slidefactory_root.is_dir():
        error(f'Slidefactory directory {slidefactory_root} does not exist.')

    # Choose theme url
    theme_dpath, is_custom_theme = find_theme(args.theme, theme_root)
    if (is_custom_theme
            or not in_container
            or args.format in ['pdf', 'html-local', 'html-standalone']):
        theme_url = f'file://{url_quote(str(theme_dpath.absolute()))}/csc.css'
    else:
        theme_url = f'https://cdn.jsdelivr.net/gh/csc-training/slidefactory/theme/{args.theme}/csc.css'

    # Choose other urls
    if args.format in ['pdf', 'html-local', 'html-standalone']:
        urls_fpath = slidefactory_root / 'urls_local.yaml'
    else:
        urls_fpath = slidefactory_root / 'urls.yaml'

    # Suffix
    if args.format == 'pdf':
        suffix = '.pdf'
    else:
        suffix = '.html'

    # Extra pandoc args
    pandoc_args = []
    if args.format == 'html-standalone':
        pandoc_args += ['--embed-resources']

    # Convert files
    for filename in args.input:
        output = filename
        if args.output:
            output = Path(args.output + str(output))

        outfilename = output.with_suffix(suffix)

        info(f'Convert {filename} to {outfilename}')

        if args.format == 'pdf':
            # Use temporary html output for pdf
            with tempfile.NamedTemporaryFile(dir=filename.parent,
                                             prefix=f'{filename.stem}-',
                                             suffix='.html') as tmpfile:
                html = Path(tmpfile.name)
                create_html(filename, html, args,
                            theme_dpath=theme_dpath, urls_fpath=urls_fpath,
                            theme_url=theme_url)
                create_pdf(html, outfilename, args)
        else:
            create_html(filename, outfilename, args,
                        theme_dpath=theme_dpath, urls_fpath=urls_fpath,
                        theme_url=theme_url, pandoc_args=pandoc_args)


if __name__ == '__main__':
    main()
