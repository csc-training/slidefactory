#!/usr/bin/env python3
# ------------------------------------------------------------------------- #
# Function: Convert a presentation from Markdown (or reStructuredText) to   #
#           reveal.js powered HTML5 using pandoc.                           #
# Usage: python slidefactory.py talk.md                                     #
# Help:  python slidefactory.py --help                                      #
# ------------------------------------------------------------------------- #
import argparse
import copy
import functools
import hashlib
import html.parser
import inspect
import os
import re
import shlex
import shutil
import sys
import subprocess
import tempfile
import yaml
from collections import namedtuple
from contextlib import contextmanager
from urllib.parse import quote as urlquote, urlparse
from pathlib import Path


VERSION = "3.4.0"
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
            return f'https://cdn.jsdelivr.net/gh/csc-training/slidefactory@3.4.0/theme/{theme.name}/csc.css'  # noqa: E501

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
                dry_run=False,
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

    if not dry_run:
        copy_html_externals(input_fpath, html_fpath)


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


def create_pdf(html_fpath, pdf_fpath, *,
               meta={},
               dry_run=False,
               ):
    with tempfile.NamedTemporaryFile(
             dir=pdf_fpath.parent,
             prefix=f'{pdf_fpath.stem}-',
             suffix='.pdf') \
         as tmpfile:
        tmp_pdf_fpath = Path(tmpfile.name)
        run_args = [
            'chromium',
            '--no-sandbox',
            '--headless',
            '--disable-gpu',
            '--disable-software-rasterizer',
            '--hide-scrollbars',
            '--virtual-time-budget=2147483647',
            '--run-all-compositor-stages-before-draw',
            f'--print-to-pdf={tmp_pdf_fpath}',
            f'file://{html_fpath.absolute()}?print-pdf'
            ]
        run(run_args)

        with tempfile.NamedTemporaryFile(
                 dir=pdf_fpath.parent,
                 prefix=f'{pdf_fpath.stem}-',
                 suffix='.txt') \
             as tmpfile:
            pdfmark_fpath = Path(tmpfile.name)

            pdfmark = '[ '
            for key in ["Title", "Author", "Subject"]:
                value = meta.get(key.lower())
                if value is not None:
                    pdfmark += f'/{key} ({value}) '
            pdfmark += f'/Creator (Slidefactory {VERSION}) /DOCINFO pdfmark'

            verbose_info(f'write {pdfmark_fpath}')
            verbose_info(f'{pdfmark}\n')
            if not dry_run:
                with open(pdfmark_fpath, 'w') as f:
                    f.write(pdfmark)

            run_args = [
                'gs',
                '-q',
                '-dNOPAUSE',
                '-dBATCH',
                '-dSAFER',
                '-sDEVICE=pdfwrite',
                '-dCompatibilityLevel=1.4',
                '-dPDFSETTINGS=/printer',
                '-dDownsampleColorImages=true',
                '-dColorImageResolution=300',
                '-dDownsampleGrayImages=true',
                '-dGrayImageResolution=300',
                '-dDownsampleMonoImages=true',
                '-dMonoImageResolution=300',
                '-dColorConversionStrategy=/LeaveColorUnchanged',
                '-dPreserveAnnots=true',
                '-dDetectDuplicateImages=true',
                f'-sOutputFile={pdf_fpath}',
                f'{tmp_pdf_fpath}',
                f'{pdfmark_fpath}',
                ]
            run(run_args)


def create_index_page(fpath, title, info_content, html_content, pdf_content):
    info(f'Create {fpath}')
    with fpath.open("w") as fd:
        csc_ui_version = '2.1.11'
        fd.write(f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{title}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@cscfi/csc-ui@{csc_ui_version}/dist/styles/css/theme.css" />
</head>
<body>
<c-main>
  <c-toolbar>
    <c-csc-logo></c-csc-logo>
    {title}
  </c-toolbar>

  <c-page>

    <c-card>
      <c-card-title>About</c-card-title>
      <c-card-content>
        <div>
{info_content}
        </div>
      </c-card-content>
    </c-card>

    <br>

    <c-card>
      <c-card-title>Slides (HTML)</c-card-title>
      <c-card-content>
{html_content}
      </c-card-content>
    </c-card>

    <br>

    <c-card>
      <c-card-title>Slides (PDF)</c-card-title>
      <c-card-content>
{pdf_content}
      </c-card-content>
    </c-card>

  </c-page>
</c-main>
<script src="https://cdn.jsdelivr.net/npm/@cscfi/csc-ui@{csc_ui_version}/dist/csc-ui/csc-ui.esm.js" type="module"></script>
""".strip("\n"))  # noqa: E501
        fd.write("""
<script>
  const accordions = document.querySelectorAll("c-accordion");
  accordions.forEach((accordion) => {
    accordion.value = [];
    accordion.multiple = true;
  });
</script>
</body>
</html>
""".strip("\n"))  # noqa: E501


def build_content(fpath, page_theme_fpath, args, *, line_fmt='{}'):
    info(f'Process {fpath}')
    with fpath.open() as fd:
        metadata = yaml.safe_load(fd.read())

    title = metadata["title"]
    content = ""

    if "modules" in metadata:
        content += '<c-accordion>\n'
        for module in metadata["modules"]:
            mod_fpath = fpath.parent / module / fpath.name
            mod_title, mod_content = \
                build_content(mod_fpath, page_theme_fpath, args,
                              line_fmt='<p>{}</p>')
            content += f'<c-accordion-item heading="{mod_title}" value="{module}">\n'  # noqa: E501
            content += mod_content
            content += '</c-accordion-item>\n'
        content += '</c-accordion>\n'
    else:
        assert "slidesdir" in metadata
        slides_dpath = fpath.parent / metadata["slidesdir"]
        for md_fpath in sorted(slides_dpath.glob("*.md")):
            meta = read_slides_metadata(md_fpath)
            html_name = md_fpath.with_suffix(".html").name
            html_fpath = 'html' / fpath.parent / html_name
            slides_title = re.sub(r'<.*?>', '', meta["title"])
            m = re.search(r'^\d+', html_name)
            prefix = '' if m is None else f'{int(m.group())}.'
            content += line_fmt.format(f'<c-link href="{html_fpath}" target="_blank">{prefix} {slides_title}</c-link>')  # noqa: E501
            content += '\n'

            # Convert slides
            formats = ['html']
            if args.with_pdf:
                formats += ['pdf']
            for fmt in formats:
                args_slides = copy.copy(args)
                args_slides.input = [md_fpath]
                args_slides.output = args.output / fmt / fpath.parent
                args_slides.format = fmt
                if fmt == 'html':
                    theme_url = os.path.relpath(page_theme_fpath,
                                                html_fpath.parent)
                    args_slides.theme_url = theme_url
                main_slides(args_slides)

    return title, content


def read_slides_metadata(fpath):
    with fpath.open() as fd:
        for line in fd:
            if line.strip() == "---":
                break
        data = ""
        for line in fd:
            if line.strip() == "---":
                break
            data += line
        if data == "":
            raise RuntimeError(f"{fpath} missing metadata")
        try:
            return yaml.safe_load(data)
        except yaml.parser.ParserError as exc:
            raise RuntimeError(f"{fpath} yaml parsing failed") from exc


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

    # Main argparser - slides sub-command
    parser_slides = subparsers.add_parser(
        'slides',
        parents=[pparser_common, pparser_conversion],
        help='convert slides')
    parser_slides.set_defaults(main=main_slides)
    parser_slides.add_argument(
        'input', metavar='input.md', nargs='*', type=Path,
        help='presentation file(s)')
    parser_slides.add_argument(
        '-o', '--output', metavar='DIR', type=Path,
        help=('output directory (by default uses '
              'the same directory as the input files)'))
    parser_slides.add_argument(
        '-f', '--format', metavar='FORMAT', default='pdf',
        choices=['pdf', 'html', 'html-local', 'html-embedded'],
        help='output format (default: %(default)s; available: %(choices)s)')
    group = parser_slides.add_argument_group(
        'advanced options for overriding paths and urls')
    for key in URL_KEYS:
        group.add_argument(f'--{key}', help=f'override {key}')

    # Main argparser - pages sub-command
    parser_pages = subparsers.add_parser(
        'pages',
        parents=[pparser_common, pparser_conversion],
        help='build pages and convert slides')
    parser_pages.set_defaults(main=main_pages)
    parser_pages.add_argument(
        'input', metavar='about.yml', type=Path,
        help='metadata file')
    parser_pages.add_argument(
        'output', metavar='DIR', type=Path,
        help='output directory')
    parser_pages.add_argument(
        '--info_content',
        default='This page is generated with slidefactory.',
        help='information shown on the page')
    parser_pages.add_argument(
        '--with-pdf', action='store_true',
        help='include pdf')

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


def main_slides(args):
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
        html_kwargs = dict(
            defaults_fpath=args.defaults_fpath,
            template_fpath=args.template_fpath,
            pandoc_vars=pandoc_vars,
            pandoc_args=pandoc_args,
            filters=args.filters,
            dry_run=args.dry_run,
        )

        if args.format == 'pdf':
            # Use temporary html output for pdf
            with tempfile.NamedTemporaryFile(
                     dir=in_fpath.parent,
                     prefix=f'{in_fpath.stem}-',
                     suffix='.html',
                 ) as tmpfile:
                html_fpath = Path(tmpfile.name)
                create_html(in_fpath, html_fpath, **html_kwargs)
                meta = read_slides_metadata(in_fpath)

                # Use event name as subject if no separate subject defined
                if 'subject' not in meta and 'event' in meta:
                    meta['subject'] = meta['event']

                create_pdf(html_fpath, out_fpath, meta=meta, dry_run=args.dry_run)
        else:
            create_html(in_fpath, out_fpath, **html_kwargs)


def main_pages(args):
    if args.output.exists():
        error(f'Output path {args.output} exists. Exiting.')

    page_theme_fpath = Path('html') / 'theme' / args.theme.name / 'csc.css'
    output_theme_dpath = args.output / page_theme_fpath.parent
    info(f'Copy theme to {output_theme_dpath}')
    shutil.copytree(args.theme.dpath, output_theme_dpath)

    title, html_content = build_content(args.input, page_theme_fpath, args)

    if args.with_pdf:
        pdf_content = re.sub(r'href="html/(.*?).html"',
                             r'href="pdf/\1.pdf"',
                             html_content)
        pdf_content += '</c-card-content>\n'
        pdf_content += '<c-card-content>\n'

        zip_fpath = args.output / 'slides.zip'
        info(f'Create {zip_fpath}')
        shutil.make_archive(zip_fpath.with_suffix(''),
                            'zip',
                            args.output / 'pdf')
        pdf_content += f'<c-link href="{zip_fpath.name}">Download a zip file containing all slides.</c-link>\n'  # noqa: E501
    else:
        pdf_content = "Not generated."

    # Convert links to html
    info_content = re.sub(r'\[(.*?)\]\((.*?)\)',
                          r'<c-link href="\2">\1</c-link>',
                          args.info_content)

    index_fpath = args.output / 'index.html'
    create_index_page(index_fpath, title,
                      info_content, html_content, pdf_content)


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
         f'    singularity exec slidefactory_VERSION.sif python3 {py_fpath} slides --format html-local slides.md'  # noqa: E501
         '\n'
         f'In docker:\n'
         f'    docker run -it --rm -v "$PWD:$PWD:Z" -w "$PWD" --entrypoint python3 ghcr.io/csc-training/slidefactory:VERSION {py_fpath} slides --format html-local slides.md'  # noqa: E501
         '\n'
         f'Hint: make an alias of this command.\n'
         )


if __name__ == '__main__':
    main()
