#!/usr/bin/python
# ------------------------------------------------------------------------- #
# Function: Convert a presentation from Markdown (or reStructuredText) to   #
#           reveal.js powered HTML5 using pandoc.                           #
# Usage: python slidefactory.py talk.md                                     #
# Help:  python slidefactory.py --help                                      #
# ------------------------------------------------------------------------- #
import argparse
import functools
import hashlib
import html.parser
import inspect
import os
import shlex
import shutil
import sys
import subprocess
import tempfile
from collections import namedtuple
from contextlib import contextmanager
from urllib.parse import quote as urlquote, urlparse
from pathlib import Path


VERSION = "3.0.0-beta.8"
slidefactory_root = Path(__file__).absolute().parent

# Modify version string if this file has been edited
with open(__file__, 'rb') as f:
    CHECKSUM = hashlib.sha256(f.read()).hexdigest()


def __read_checksum_reference():
    checksum_fpath = slidefactory_root / f'sha256sums_{VERSION}'
    if not checksum_fpath.exists():
        return None
    with open(checksum_fpath, 'r') as f:
        for line in f:
            chk, fpath = line.strip().split('  ', 1)
            if fpath == f'./{Path(__file__).name}':
                return chk
    return None


REF_CHECKSUM = __read_checksum_reference()
if CHECKSUM != REF_CHECKSUM:
    VERSION += '-edited'


@contextmanager
def named_ctx(name):
    """Context manager that returns an object
       with object.name being the given name."""
    yield namedtuple('Named', ['name'])(name)


class HTMLParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources = set()

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            for key, value in attrs:
                if key == 'data-src':
                    if urlparse(value).scheme == '':
                        self.sources.add(value)


def run_template(run_args, *, dry_run):
    run_args = [str(a) for a in run_args]

    if dry_run:
        info(shlex.join(run_args))
        return

    verbose_info(shlex.join(run_args))
    p = subprocess.run(run_args,
                       check=False, shell=False,
                       capture_output=True)

    verbose_info(p.stdout.decode())

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
    available_themes = sorted([str(x.name) for x in theme_root.iterdir()
                               if x.is_dir()])
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
                pandoc_args=[],
                ):
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


def copy_html_externals(input_fpath, html_fpath):
    # Find external file paths
    parser = HTMLParser()
    with open(html_fpath, 'r') as f:
        parser.feed(f.read())
    externals = parser.sources

    # Check that files exist
    for fname in externals:
        fpath = input_fpath.parent / fname
        if not fpath.exists():
            error(f'Linked file missing: {fpath}')

    # Copy files to output path
    if input_fpath.parent.resolve() != html_fpath.parent.resolve():
        for fname in externals:
            ext_fpath = input_fpath.parent / fname
            tgt_fpath = html_fpath.parent / fname
            verbose_info(f'cp {ext_fpath} {tgt_fpath}')
            tgt_fpath.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ext_fpath, tgt_fpath)


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

    py_fpath = shlex.quote(str(path / Path(__file__).name))

    info(f'\nTo use the local installation, run '
         f'{py_fpath} with the container.\n'
         f'In singularity:\n'
         f'    singularity exec slidefactory_VERSION.sif python3 {py_fpath} --format html-local slides.md'  # noqa: E501
         '\n'
         f'In docker:\n'
         f'    docker run -it --rm -v "$(pwd)":"$(pwd)":Z -w "$(pwd)" --entrypoint python3 ghcr.io/csc-training/slidefactory:VERSION {py_fpath} --format html-local slides.md'  # noqa: E501
         '\n'
         f'Hint: make an alias of this command.\n'
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

    parser = argparse.ArgumentParser(
        description="Convert a presentation from Markdown to "
                    "a reveal.js-powered HTML5 using pandoc."
                    )
    parser.add_argument(
        'input', metavar='input.md', nargs='*', type=Path,
        help='filename for presentation source (e.g. in Markdown)')
    parser.add_argument(
        '-o', '--output', metavar='DIR', type=Path,
        help=('output directory (by default uses '
              'the same directory as the input files)'))
    parser.add_argument(
        '-t', '--theme', metavar='THEME', default='csc-plain',
        help=('presentation theme name or path (default: %(default)s, '
              f'available: {", ".join(get_available_themes(theme_root))})'))
    parser.add_argument(
        '-f', '--format', metavar='FORMAT', default='pdf',
        choices=['pdf', 'html', 'html-local', 'html-embedded'],
        help='output format (default: %(default)s; available: %(choices)s)')
    parser.add_argument(
        '--filters', action='append', default=[],
        metavar='filter.py',
        help='pandoc filter scripts (multiple allowed)')
    parser.add_argument(
        '-n', '--dry-run', '--show-command',
        action='store_true', default=False,
        help='do nothing, only show the full commands to be run')
    parser.add_argument(
        '-v', '--verbose', action='store_true', default=False,
        help='be loud and noisy')
    parser.add_argument(
        '-q', '--quiet', action='store_true', default=False,
        help='suppress all output except errors')
    parser.add_argument(
        '--no-math', action='store_true',
        help='disable math rendering')
    parser.add_argument(
        '--install', metavar='PATH', type=Path,
        help=('install local slidefactory to %(metavar)s '
              '(ignores all other arguments)'))
    group = parser.add_argument_group(
        'advanced options for overriding paths and urls')
    for key in resources:
        group.add_argument(f'--{key}', help=f'override {key}')
    args, unknown_args = parser.parse_known_args()

    global info
    info = functools.partial(info_template, quiet=args.quiet)

    global verbose_info
    verbose_info = functools.partial(info_template, quiet=not args.verbose)

    global run
    run = functools.partial(run_template, dry_run=args.dry_run)

    info(f'Slidefactory {VERSION}')
    verbose_info(f'  checksum:  {CHECKSUM}')
    verbose_info(f'  reference: {REF_CHECKSUM}')

    if args.install:
        install(args.install)
        sys.exit(0)

    include_math = not args.no_math
    use_local_resources = args.format in ['pdf', 'html-local', 'html-embedded']

    in_container = slidefactory_root == Path('/slidefactory')

    if args.format == 'html-local' and in_container:
        error('Install and use local slidefactory in order to '
              'create local offline htmls.\n\n'
              'In short, run slidefactory container with `--install PATH` '
              'and follow the instructions (see README for details).'
              )

    if not slidefactory_root.is_dir():
        error(f'Slidefactory directory {slidefactory_root} does not exist.')

    # Choose theme url
    theme_dpath, is_custom_theme = find_theme(args.theme, theme_root)
    if is_custom_theme or not in_container or use_local_resources:
        resources['theme_url'] = f'file://{urlquote(str(theme_dpath.absolute()))}/csc.css'  # noqa: E501
    else:
        resources['theme_url'] = f'https://cdn.jsdelivr.net/gh/csc-training/slidefactory@3.0.0-beta.8/theme/{args.theme}/csc.css'  # noqa: E501

    resources['defaults_fpath'] = theme_dpath / "defaults.yaml"
    resources['template_fpath'] = theme_dpath / "template.html"

    # Choose other urls
    if use_local_resources:
        root = f'file://{urlquote(str(slidefactory_root))}'
        resources['revealjs_url'] = f'{root}/reveal.js-4.4.0'
        resources['mathjax_url'] = f'{root}/MathJax-3.2.2/es5/tex-chtml-full.js'  # noqa: E501
        resources['fonts_url'] = f'{root}/fonts/fonts.css'
    else:
        resources['revealjs_url'] = 'https://cdn.jsdelivr.net/npm/reveal.js@4.4.0'  # noqa: E501
        resources['mathjax_url'] = 'https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-chtml-full.js'  # noqa: E501
        resources['fonts_url'] = 'https://fonts.googleapis.com/css2?family=Noto+Sans:ital,wdth,wght@0,100,400;0,100,700;1,100,400;1,100,700&family=Inconsolata:wght@400;700'  # noqa: E501

    # Update urls from args
    for key in resources:
        new_value = getattr(args, key)
        if new_value is not None:
            resources[key] = new_value

    if args.verbose:
        info("Using following resources (override with the given argument):")
        for key, val in resources.items():
            info(f"  --{key:16} {val}")

    pandoc_vars = {
        'theme-url': resources['theme_url'],
        'revealjs-url': resources['revealjs_url'],
        'mathjaxurl': resources['mathjax_url'],
        'css': resources['fonts_url'],
        }

    if args.format in ['html-embedded'] and include_math:
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
    elif args.format == 'html-embedded':
        suffix = '.embedded.html'
    else:
        suffix = '.html'

    # Extra pandoc args
    pandoc_args = unknown_args
    if include_math:
        pandoc_args += ['--mathjax']
    if args.format in ['html-embedded']:
        pandoc_args += ['--embed-resources']

    # Convert files
    for in_fpath in args.input:
        if args.output:
            out_fpath = args.output / in_fpath.with_suffix(suffix).name
            if not args.dry_run:
                out_fpath.parent.mkdir(parents=True, exist_ok=True)
        else:
            out_fpath = in_fpath.with_suffix(suffix)

        info(f'Convert {in_fpath} to {out_fpath}')

        # Use temporary html output for pdf
        with tempfile.NamedTemporaryFile(
                 dir=in_fpath.parent,
                 prefix=f'{in_fpath.stem}-',
                 suffix='.html') \
             if args.format == 'pdf' \
             else named_ctx(out_fpath) \
             as outfile:

            html_fpath = Path(outfile.name)
            create_html(in_fpath, html_fpath,
                        defaults_fpath=resources['defaults_fpath'],
                        template_fpath=resources['template_fpath'],
                        pandoc_vars=pandoc_vars,
                        pandoc_args=pandoc_args,
                        filters=args.filters,
                        )

            if not args.dry_run:
                copy_html_externals(in_fpath, html_fpath)

            if args.format == 'pdf':
                create_pdf(html_fpath, out_fpath)


if __name__ == '__main__':
    main()
