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


VERSION = "3.0.0-beta.11"
SLIDEFACTORY_ROOT = Path(__file__).absolute().parent
IN_CONTAINER = SLIDEFACTORY_ROOT == Path('/slidefactory')

# Modify version string if this file has been edited
with open(__file__, 'rb') as f:
    CHECKSUM = hashlib.sha256(f.read()).hexdigest()


def __read_checksum_reference():
    checksum_fpath = SLIDEFACTORY_ROOT / f'sha256sums_{VERSION}'
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


URL_KEYS = (
    'defaults_fpath',
    'template_fpath',
    'theme_url',
    'revealjs_url',
    'mathjax_url',
    'fonts_url',
    )

Theme = namedtuple('Theme', ['name', 'dpath', 'is_custom'])


def get_default_url(key: str, format: str, theme: Theme):
    assert key in URL_KEYS
    use_local_resources = format in ['pdf', 'html-local', 'html-embedded']
    root_url = f'file://{urlquote(str(SLIDEFACTORY_ROOT))}'
    if key == 'theme_url':
        if theme.is_custom or not IN_CONTAINER or use_local_resources:
            return f'file://{urlquote(str(theme.dpath.absolute()))}/csc.css'  # noqa: E501
        else:
            return f'https://cdn.jsdelivr.net/gh/csc-training/slidefactory@3.0.0-beta.10/theme/{theme.name}/csc.css'  # noqa: E501

    elif key == 'defaults_fpath':
        return theme.dpath / "defaults.yaml"

    elif key == 'template_fpath':
        return theme.dpath / "template.html"

    elif key == 'revealjs_url':
        if use_local_resources:
            return f'{root_url}/reveal.js-4.4.0'
        else:
            return 'https://cdn.jsdelivr.net/npm/reveal.js@4.4.0'  # noqa: E501

    elif key == 'mathjax_url':
        if use_local_resources:
            return f'{root_url}/MathJax-3.2.2/es5/tex-chtml-full.js'  # noqa: E501
        else:
            return 'https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-chtml-full.js'  # noqa: E501

    elif key == 'fonts_url':
        if use_local_resources:
            return f'{root_url}/fonts/fonts.css'
        else:
            return 'https://fonts.googleapis.com/css2?family=Noto+Sans:ital,wdth,wght@0,100,400;0,100,700;1,100,400;1,100,700&family=Inconsolata:wght@400;700'  # noqa: E501


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


def find_theme(name):
    is_custom = False
    if os.sep in str(name):
        is_custom = True
        p = Path(name)
        name = p.name
        if not p.is_dir():
            error(f'Nonexistent theme directory {p.absolute()}')
    else:
        theme_root = SLIDEFACTORY_ROOT / 'theme'
        p = theme_root / name
        if not p.is_dir():
            available_themes = get_available_themes(theme_root)
            error(f'Invalid theme {name}.'
                  f' Available themes: {", ".join(available_themes)}.')
    for fname in ['defaults.yaml', 'template.html', 'csc.css']:
        if not (p / fname).is_file():
            error(f'File {fname} missing from the theme directory'
                  f' {p.absolute()}')
    return Theme(name, p, is_custom)


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


def main():
    # Common args
    pparser_common = argparse.ArgumentParser(add_help=False)
    pparser_common.add_argument(
        '-n', '--dry-run', '--show-command',
        action='store_true', default=False,
        help='do nothing, only show the full commands to be run')
    pparser_common.add_argument(
        '-v', '--verbose', action='store_true', default=False,
        help='be loud and noisy')
    pparser_common.add_argument(
        '-q', '--quiet', action='store_true', default=False,
        help='suppress all output except errors')

    # Common conversion args
    pparser_conversion = argparse.ArgumentParser(add_help=False)
    pparser_conversion.add_argument(
        '-t', '--theme', metavar='THEME', type=find_theme,
        default='csc-plain',
        help='presentation theme name or path (default: %(default)s)')
    pparser_conversion.add_argument(
        '--filters', action='append', default=[],
        metavar='filter.py',
        help='pandoc filter scripts (multiple allowed)')
    pparser_conversion.add_argument(
        '--no-math', action='store_true',
        help='disable math rendering')
    pparser_conversion.add_argument(
        '--pandoc-args', nargs='?',
        default='', const='',
        help='additional arguments passed to pandoc')


    # Main argparser
    parser = argparse.ArgumentParser(
        description="Convert a presentation from Markdown to "
                    "a reveal.js-powered HTML5 using pandoc."
                    )
    subparsers = parser.add_subparsers(help='sub-command', required=True)

    # Main argparser - convert sub-command
    parser_convert = subparsers.add_parser(
        'convert',
        parents=[pparser_common, pparser_conversion],
        help='convert slides')
    parser_convert.set_defaults(main=main_convert)
    parser_convert.add_argument(
        'input', metavar='input.md', nargs='*', type=Path,
        help='presentation file(s)')
    parser_convert.add_argument(
        '-o', '--output', metavar='DIR', type=Path,
        help=('output directory (by default uses '
              'the same directory as the input files)'))
    parser_convert.add_argument(
        '-f', '--format', metavar='FORMAT', default='pdf',
        choices=['pdf', 'html', 'html-local', 'html-embedded'],
        help='output format (default: %(default)s; available: %(choices)s)')
    group = parser_convert.add_argument_group(
        'advanced options for overriding paths and urls')
    for key in URL_KEYS:
        group.add_argument(f'--{key}', help=f'override {key}')

    # Main argparser - install sub-command
    parser_install = subparsers.add_parser(
        'install',
        parents=[pparser_common],
        help='install local slidefactory')
    parser_install.set_defaults(main=main_install)
    parser_install.add_argument(
        'path', metavar='path', type=Path,
        help='install path')

    args = parser.parse_args()

    global info
    info = functools.partial(info_template, quiet=args.quiet)

    global verbose_info
    verbose_info = functools.partial(info_template, quiet=not args.verbose)

    global run
    run = functools.partial(run_template, dry_run=args.dry_run)

    info(f'Slidefactory {VERSION}')
    verbose_info(f'  checksum:  {CHECKSUM}')
    verbose_info(f'  reference: {REF_CHECKSUM}')
    args.main(args)

    if args.dry_run:
        info("This was DRY RUN. No changes made.")


def main_convert(args):
    if args.format == 'html-local' and IN_CONTAINER:
        error('Install and use local slidefactory in order to '
              'create local offline htmls.\n\n'
              'In short, run slidefactory container with `--install PATH` '
              'and follow the instructions (see README for details).'
              )

    include_math = not args.no_math

    # Set resource url defaults if not set
    for key in URL_KEYS:
        if getattr(args, key, None) is None:
            default = get_default_url(key, args.format, args.theme)
            setattr(args, key, default)

    if args.verbose:
        info("Using following resources (override with the given argument):")
        for key in URL_KEYS:
            val = getattr(args, key)
            info(f"  --{key:16} {val}")

    pandoc_vars = {
        'theme-url': args.theme_url,
        'revealjs-url': args.revealjs_url,
        'mathjaxurl': args.mathjax_url,
        'css': args.fonts_url,
        }

    if args.format in ['html-embedded'] and include_math:
        url = args.mathjax_url
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
    pandoc_args = args.pandoc_args.split()
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
                        defaults_fpath=args.defaults_fpath,
                        template_fpath=args.template_fpath,
                        pandoc_vars=pandoc_vars,
                        pandoc_args=pandoc_args,
                        filters=args.filters,
                        )

            if not args.dry_run:
                copy_html_externals(in_fpath, html_fpath)

            if args.format == 'pdf':
                create_pdf(html_fpath, out_fpath)


def main_install(args):
    path = args.path
    if path.exists():
        error(f'Installation path {path} exists. Exiting.')

    path = path.absolute()

    # Copy slidefactory files
    info(f'Copy {SLIDEFACTORY_ROOT} to {path}')
    if not args.dry_run:
        shutil.copytree(SLIDEFACTORY_ROOT, path)

    py_fpath = shlex.quote(str(path / Path(__file__).name))

    info(f'\nTo use the local installation, run '
         f'{py_fpath} with the container.\n'
         f'In singularity:\n'
         f'    singularity exec slidefactory_VERSION.sif python3 {py_fpath} --format html-local slides.md'  # noqa: E501
         '\n'
         f'In docker:\n'
         f'    docker run -it --rm -v "$PWD:$PWD:Z" -w "$PWD" --entrypoint python3 ghcr.io/csc-training/slidefactory:VERSION {py_fpath} --format html-local slides.md'  # noqa: E501
         '\n'
         f'Hint: make an alias of this command.\n'
         )


if __name__ == '__main__':
    main()
