#!/usr/bin/python
#---------------------------------------------------------------------------#
# Function: Convert a presentation from Markdown (or reStructuredText) to   #
#           reveal.js powered HTML5 using pandoc.                           #
# Usage: python slidefactory.py talk.md                                     #
# Help:  python slidefactory.py --help                                      #
#---------------------------------------------------------------------------#
import argparse
import functools
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


def run_template(run_args, *, verbose, dry_run):
    run_args = [str(a) for a in run_args]

    if verbose or dry_run:
        info(shlex.join(run_args))

    if not dry_run:
        p = subprocess.run(run_args,
                           check=False, shell=False,
                           capture_output=True)
        if p.returncode != 0:
            error(f'error: {repr(run_args[0])} failed '
                   f'with exit code {p.returncode}:\n'
                   f'{p.stderr.decode()}')


def info_template(msg, *, quiet):
    if not quiet:
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


def create_html(input_fpath, html_fpath, *,
                defaults_fpath,
                template_fpath,
                pandoc_vars,
                filters=[],
                pandoc_args=[]):
    run_args = [
        'pandoc',
        f'--defaults={defaults_fpath}',
        f'--template={template_fpath}',
        ]
    for key, value in pandoc_vars.items():
        run_args += [f'--variable={key}:{value}']
    run_args += pandoc_args
    run_args += [f'--filter={f}' for f in filters]
    run_args += [
        f'--output={html_fpath}',
        input_fpath,
        ]
    run(run_args)


def create_pdf(html_fpath, pdf_fpath):
    run_args = [
        'chromium-browser',
        '--no-sandbox',
        '--headless',
        '--disable-gpu',
        '--disable-software-rasterizer',
        '--hide-scrollbars',
        '--virtual-time-budget=2147483647',
        '--run-all-compositor-stages-before-draw',
        f'--print-to-pdf={pdf_fpath}',
        f'file://{html_fpath.absolute()}?print-pdf'
        ]
    run(run_args)


def install(path):
    if path.exists():
        error(f'Installation path {path} exists. Exiting.')

    path = path.absolute()

    # Copy slidefactory files
    info(f'Copy {slidefactory_root} to {path}')
    shutil.copytree(slidefactory_root, path)

    py_fpath = path / Path(__file__).name

    info(f'\nTo use the local installation, run \'{py_fpath}\' with the container.\n'
         f'In singularity:\n'
         f'    singularity exec slidefactory_VERSION.sif \'{py_fpath}\' --format html-local slides.md' '\n'
         f'In docker:\n'
         f'    docker run -it --rm -v "$(pwd)":"$(pwd)":Z -w "$(pwd)" --entrypoint \'{py_fpath}\' ghcr.io/csc-training/slidefactory:VERSION --format html-local slides.md\n'
         )


def main():
    theme_root = slidefactory_root / 'theme'

    resources = {
            'defaults_fpath': None,
            'template_fpath': None,
            'theme_url': None,
            'revealjs_url': None,
            'mathjax_url': None,
            'fonts_url': None,
        }

    parser = argparse.ArgumentParser(description="""Convert a presentation
    from Markdown (or reStructuredText) to reveal.js powered HTML5 using
    pandoc.""")
    parser.add_argument('input', metavar='input.md', nargs='*', type=Path,
            help='filename for presentation source (e.g. in Markdown)')
    parser.add_argument('--output', metavar='prefix',
            help='prefix for output filenames (by default uses the '
            'basename of the input file, i.e. talk.md -> talk.html)')
    parser.add_argument('-t', '--theme', metavar='THEME', default='csc-plain',
            help=('presentation theme name or path (default: %(default)s, '
                  f'available: {", ".join(get_available_themes(theme_root))})'))
    parser.add_argument('-f', '--format', metavar='FORMAT', default='pdf',
            choices=['pdf', 'html', 'html-local', 'html-standalone'],
            help='output format (default: %(default)s; available: %(choices)s)')
    parser.add_argument('--filters', action='append', default=[],
            metavar='filter.py',
            help='pandoc filter scripts (multiple allowed)')
    parser.add_argument('-n', '--dry-run', '--show-command',
            action='store_true', default=False,
            help='do nothing, only show the full commands to be run')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
            help='be loud and noisy')
    parser.add_argument('-q', '--quiet', action='store_true', default=False,
            help='suppress all output except errors')
    parser.add_argument('--no-math', action='store_true',
            help='disable math rendering')
    parser.add_argument('--install', metavar='PATH', type=Path,
            help='install local slidefactory to %(metavar)s (ignores all other arguments)')
    for key in resources:
        parser.add_argument(f'--{key}',
                help=f'override {key}')
    args = parser.parse_args()

    global info
    info = functools.partial(info_template, quiet=args.quiet)

    global run
    run = functools.partial(run_template, verbose=args.verbose, dry_run=args.dry_run)


    if args.install:
        install(args.install)
        sys.exit(0)

    include_math = not args.no_math

    in_container = slidefactory_root == Path('/slidefactory')

    if args.format == 'html-local' and in_container:
        error('Install and use local slidefactory in order to create local offline htmls.\n\n'
              'In short, run slidefactory container with `--install PATH` '
              'and follow the instructions (see README for details).'
              )

    if not slidefactory_root.is_dir():
        error(f'Slidefactory directory {slidefactory_root} does not exist.')

    # Choose theme url
    theme_dpath, is_custom_theme = find_theme(args.theme, theme_root)
    if (is_custom_theme
            or not in_container
            or args.format in ['pdf', 'html-local', 'html-standalone']):
        resources['theme_url'] = f'file://{url_quote(str(theme_dpath.absolute()))}/csc.css'
    else:
        resources['theme_url'] = f'https://cdn.jsdelivr.net/gh/csc-training/slidefactory/theme/{args.theme}/csc.css'

    resources['defaults_fpath'] = theme_dpath / "defaults.yaml"
    resources['template_fpath'] = theme_dpath / "template.html"

    # Choose other urls
    if args.format in ['pdf', 'html-local', 'html-standalone']:
        root = f'file://{url_quote(str(slidefactory_root))}'
        resources['revealjs_url'] = f'{root}/reveal.js-4.4.0'
        resources['mathjax_url'] = f'{root}/MathJax-3.2.2/es5/tex-chtml-full.js'
        resources['fonts_url'] = f'{root}/fonts/fonts.css'
    else:
        resources['revealjs_url'] = 'https://cdn.jsdelivr.net/npm/reveal.js@4.4.0'
        resources['mathjax_url'] = 'https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-chtml-full.js'
        resources['fonts_url'] = 'https://fonts.googleapis.com/css?family=Noto+Sans:400,400i,700,700i|Inconsolata:400,700&subset=greek,latin-ext'

    # Update urls from args
    for key in resources:
        new_value = getattr(args, key)
        if new_value is not None:
            resources[key] = new_value

    info("Using following resources (override with the given argument):")
    for key, val in resources.items():
        info(f"  --{key:16} {val}")

    pandoc_vars = {
        'theme-url': resources['theme_url'],
        'revealjs-url': resources['revealjs_url'],
        'mathjaxurl': resources['mathjax_url'],
        'css': resources['fonts_url'],
        }

    if args.format in ['html-standalone'] and include_math:
        url = resources['mathjax_url']
        pandoc_vars.update({
            'mathjaxurl': '',
            'header-includes': f'<script src="{url}"></script>',
            })

    # Suffix
    if args.format == 'pdf':
        suffix = '.pdf'
    elif args.format == 'html-local':
        suffix = '.local.html'
    elif args.format == 'html-standalone':
        suffix = '.standalone.html'
    else:
        suffix = '.html'

    # Extra pandoc args
    pandoc_args = []
    if include_math:
        pandoc_args += ['--mathjax']
    if args.format in ['html-standalone']:
        pandoc_args += ['--embed-resources']

    # Convert files
    for filename in args.input:
        out_fpath = Path(filename)
        out_fpath = out_fpath.with_suffix(suffix)

        if args.output:
            out_fpath = out_fpath.with_name(args.output)

        info(f'Convert {filename} to {out_fpath}')

        # Use temporary html output for pdf
        with tempfile.NamedTemporaryFile(
                 dir=filename.parent,
                 prefix=f'{filename.stem}-',
                 suffix='.html') \
             if args.format == 'pdf' \
             else open(out_fpath, 'w') \
             as outfile:

            html_fpath = Path(outfile.name)
            create_html(filename, html_fpath,
                        defaults_fpath=resources['defaults_fpath'],
                        template_fpath=resources['template_fpath'],
                        pandoc_vars=pandoc_vars,
                        pandoc_args=pandoc_args,
                        filters=args.filters,
                        )

            if args.format == 'pdf':
                create_pdf(html_fpath, out_fpath)


if __name__ == '__main__':
    main()
