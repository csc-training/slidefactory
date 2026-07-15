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
import html
import html.parser
import inspect
import os
import re
import shlex
import shutil
import signal
import sys
import subprocess
import tempfile
import pypdf
import pypdf.annotations
import yaml
from collections import namedtuple
from contextlib import contextmanager
from urllib.parse import quote as urlquote, urlparse
from pathlib import Path


VERSION = "3.4.3"
SLIDEFACTORY_ROOT = Path(__file__).absolute().parent
IN_CONTAINER = SLIDEFACTORY_ROOT == Path('/slidefactory')

# Chromium can occasionally deadlock during startup/rendering; bound how
# long we wait so that failure mode is a clear error, not an indefinite hang.
CHROMIUM_TIMEOUT = 120

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


def run_template(run_args, *, dry_run, timeout=None):
    run_args = [str(a) for a in run_args]

    if dry_run:
        info(shlex.join(run_args))
        return

    verbose_info(shlex.join(run_args))
    p = subprocess.Popen(run_args,
                        shell=False,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        start_new_session=True)
    try:
        stdout, stderr = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass  # process already exited on its own
        p.communicate()
        error(f'error: {repr(run_args[0])} timed out after {timeout}s '
              f'and was killed.\n\n'
              f'This has been observed as an intermittent Chromium '
              f'startup/rendering issue, independent of slide content. '
              f'It can also happen when a slide references a '
              f'slow-loading or unresponsive external resource.')

    verbose_info(stdout.decode())

    if p.returncode != 0:
        error(f'error: {repr(run_args[0])} failed '
              f'with exit code {p.returncode}:\n'
              f'{stderr.decode()}')


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
        run(run_args, timeout=CHROMIUM_TIMEOUT)

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


def create_index_page(fpath, title, info_content, html_content, pdf_content,
                      merged_pdf_content=''):
    info(f'Create {fpath}')
    with fpath.open("w") as fd:
        csc_ui_version = '2.1.11'
        pdf_title_extra = ''
        if merged_pdf_content:
            pdf_title_extra = (
                '<span style="float: right; font-size: 0.8rem; '
                f'font-weight: normal;">{merged_pdf_content}</span>'
            )
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
      <c-card-title>Slides (PDF){pdf_title_extra}</c-card-title>
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


# TOC layout, in the theme's own CSS pixel coordinate system (see
# _theme_slide_size), so the generated TOC slide(s) go through the same
# pandoc+Chromium rendering as real content and pick up the theme's
# background/logo/colors/font automatically. Rows use normal document flow
# (not absolute positioning) so they start right after the heading exactly
# like any other slide's content -- we don't need to predict positions here
# since click-through link rectangles are measured from the rendered PDF
# afterwards (see _measure_toc_links), not calculated analytically.
# HEADING_ALLOWANCE and LINE_HEIGHT are a capacity estimate for pagination
# (how many entries fit per TOC page) -- unlike a positioning value, this
# still needs to be reasonably accurate: overestimating it under-fills each
# page (rows stop well before the slide's bottom margin, since rows flow
# normally and simply stop once the chunk's entry count is reached), rather
# than just wasting margin. Calibrated against csc-plain by measuring actual
# rendered row spacing.
TOC_HEADING_ALLOWANCE = 150
TOC_BOTTOM_MARGIN = 140
TOC_ROW_GAP = 10
TOC_LINE_HEIGHT = 44
TOC_INDENT_PER_LEVEL = 40
# Continuation pages have no heading (see _render_toc_markdown), so unlike
# the first page their rows aren't pushed down by the heading's own
# padding-bottom -- without this they start right at the slide's top
# margin and collide with the logo in the top-right corner. One line
# height of clearance is enough and comes out of the same slack that
# TOC_HEADING_ALLOWANCE already reserves for pagination on every page
# (continuation pages need less than a full heading's worth of allowance,
# so this doesn't risk overflowing the per-page capacity estimate).
TOC_CONTINUATION_TOP_MARGIN = TOC_LINE_HEIGHT
TOC_ENTRY_FONT_SIZE = 28
TOC_SUBENTRY_FONT_SIZE = 24

# Name of the optional file used as the merged PDF's title slide, looked up
# next to the top-level about.yml given to `pages`. Falls back to the
# placeholder of the same name shipped with slidefactory (see
# SLIDEFACTORY_ROOT / GLOBAL_TITLE_FILENAME), which explains on-slide how to
# provide a real one.
GLOBAL_TITLE_FILENAME = 'global_title.md'

# Hides the theme's reveal.js slide-number badge (visible in print-pdf
# output, see csc.css) on the title/TOC pages generated by merge_pdfs --
# it's meaningless there (not a real numbered slide in a real deck), and
# on the TOC specifically its extracted text is an extra, unaccounted-for
# run that breaks _measure_toc_links' chapter/run pairing. Injected via
# 'header-includes' rather than reveal.js's own `slideNumber` config
# variable, since the CSS approach can't be defeated by reveal.js's own
# number-formatting fallbacks.
HIDE_SLIDE_NUMBER_CSS = (
    '<style>.reveal .slide-number { display: none !important; }</style>')


def _md_has_body(fpath):
    """Whether a markdown file has any content beyond its YAML front
    matter, used to tell a body-less global title file (see merge_pdfs)
    apart from one a user has extended with real slide content. Scans
    for the front matter's `---` delimiters the same lenient way
    read_slides_metadata does (skipping any leading comment/blank lines
    rather than requiring the first delimiter on line 1), since project
    files commonly start with a license header comment."""
    lines = fpath.read_text().splitlines(keepends=True)
    i = 0
    while i < len(lines) and lines[i].strip() != '---':
        i += 1
    if i >= len(lines):
        return bool(''.join(lines).strip())  # no front matter found at all
    start = i + 1
    i = start
    while i < len(lines) and lines[i].strip() != '---':
        i += 1
    if i >= len(lines):
        return bool(''.join(lines[start:]).strip())  # front matter never closes
    return bool(''.join(lines[i + 1:]).strip())


def _theme_slide_size(defaults_fpath):
    """Return the theme's configured (width, height) in CSS pixels, from its
    defaults.yaml, falling back to reveal.js's own default of 960x700."""
    try:
        with open(defaults_fpath) as fd:
            defaults = next(iter(yaml.safe_load_all(fd.read())))
        variables = defaults['variables']
        return float(variables['width']), float(variables['height'])
    except (OSError, KeyError, TypeError, ValueError, StopIteration,
            yaml.YAMLError):
        return 960.0, 700.0


def _toc_lines_per_page(theme_height):
    return max(1, int((theme_height - TOC_HEADING_ALLOWANCE - TOC_BOTTOM_MARGIN)
                       // TOC_LINE_HEIGHT))


def _toc_page_count(n_entries, theme_height):
    lines_per_page = _toc_lines_per_page(theme_height)
    return max(1, -(-n_entries // lines_per_page))


def _flatten_chapters(chapters, level=0):
    for chapter in chapters:
        yield level, chapter
        yield from _flatten_chapters(chapter['children'], level + 1)


def _assign_start_pages(chapters, offset):
    # Depth-first, matching the order pages are appended in _add_content_pages
    for chapter in chapters:
        if chapter['pdf_fpath'] is not None:
            chapter['start_page'] = offset + 1
            offset += len(chapter['reader'].pages)
        else:
            offset = _assign_start_pages(chapter['children'], offset)
            chapter['start_page'] = (chapter['children'][0]['start_page']
                                     if chapter['children'] else None)
    return offset


def _render_toc_markdown(entries, theme_width, theme_height,
                        title='Table of Contents'):
    """Build reveal.js slide markdown for the TOC. Rows use normal document
    flow (not absolute positioning), so they start right after the heading
    and stack with predictable spacing exactly like any other slide's
    content -- no need to predict where things land, since click-through
    link rectangles are measured from the rendered PDF afterwards (see
    _measure_toc_links). Returns (markdown_text, chunks), where chunks is
    the entries grouped by which generated TOC page they end up on."""
    lines_per_page = _toc_lines_per_page(theme_height)
    chunks = [entries[i:i + lines_per_page]
             for i in range(0, len(entries), lines_per_page)] or [[]]

    slides = []
    for chunk_index, chunk in enumerate(chunks):
        rows = []
        for level, chapter in chunk:
            indent = level * TOC_INDENT_PER_LEVEL
            bold = level == 0
            size = TOC_ENTRY_FONT_SIZE if bold else TOC_SUBENTRY_FONT_SIZE
            start_page = chapter['start_page']
            page_str = str(start_page) if start_page else ''
            leader = (
                f'<span style="flex: 1 1 auto; margin: 0 0.5em 0.2em 0.5em; '
                f'border-bottom: 2px dotted currentColor;"></span>'
                f'<span>{html.escape(page_str)}</span>'
                ) if page_str else ''
            rows.append(
                f'<div style="margin-left: {indent}px; '
                f'margin-bottom: {TOC_ROW_GAP}px; font-size: {size}px; '
                f'font-weight: {"bold" if bold else "normal"}; '
                f'display: flex; align-items: flex-end; '
                f'white-space: nowrap; overflow: hidden;">'
                f'<span>{html.escape(chapter["title"])}</span>'
                f'{leader}'
                f'</div>')
        # Only the first TOC slide shows the heading; continuation slides
        # start with a horizontal rule instead, which pandoc's reveal.js
        # writer treats as a slide break even without a heading. Give
        # those a spacer so the first row doesn't collide with the logo
        # (see TOC_CONTINUATION_TOP_MARGIN).
        if chunk_index == 0:
            header = f'# {title}\n\n'
        else:
            header = '-----\n\n'
            rows.insert(0, '<div style="height: '
                          f'{TOC_CONTINUATION_TOP_MARGIN}px;"></div>')
        slides.append(header + '\n'.join(rows))

    markdown = '---\nlang: en\n---\n\n' + '\n\n'.join(slides) + '\n'
    return markdown, chunks


def _measure_toc_links(toc_reader, chunks, page_width, right_margin_pt):
    """Find each chapter entry's actual rendered position by reading text
    positions back out of the generated TOC PDF, rather than computing them
    analytically -- the theme's CSS shifts absolutely-positioned content by
    an amount that isn't reliably predictable from the CSS alone (confirmed
    empirically: a fixed additive offset beyond the expected px-to-pt
    scale, presumably from the theme's own slide-container margins).
    Returns a list of (chapter, toc_page_index, rect) in PDF points."""
    link_boxes = []
    for toc_page_index, chunk in enumerate(chunks):
        page = toc_reader.pages[toc_page_index]
        runs = []

        def visitor(text, cm, tm, fontdict, fontsize, runs=runs):
            if text.strip():
                x = tm[4] * cm[0] + tm[5] * cm[2] + cm[4]
                y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
                runs.append((x, y, text.strip()))

        page.extract_text(visitor_text=visitor)
        if toc_page_index == 0:
            runs = runs[1:]  # first run is the title heading (page 1 only)

        # Each chapter contributes exactly one run for its title, plus one
        # more for its page number (if any). If the rendered page doesn't
        # have exactly that many measurable runs -- e.g. a title got split
        # into multiple text-showing operations by the PDF renderer -- we
        # can no longer trust which run belongs to which chapter, so fail
        # loudly rather than silently emit mispositioned/mismatched links.
        expected = sum(2 if chapter['start_page'] else 1
                       for _, chapter in chunk)
        if len(runs) != expected:
            run_lines = '\n'.join(
                f'  [{i}] x={x:.1f} y={y:.1f} text={text!r}'
                for i, (x, y, text) in enumerate(runs))
            error(f'TOC page {toc_page_index + 1} has {len(runs)} '
                  f'measurable text run(s), expected {expected}. Cannot '
                  f'reliably place chapter links/bookmarks on this page.\n\n'
                  f'Measured runs:\n{run_lines}')

        i = 0
        for level, chapter in chunk:
            x, y, _ = runs[i]
            i += 1
            if chapter['start_page']:
                # Generous fixed padding (in PDF points, the unit x/y are
                # already measured in) around the measured text baseline,
                # rather than deriving it from the CSS font-size in theme
                # px -- we don't have a reliable px-to-pt scale for that
                # (see the module docstring note in _measure_toc_links).
                rect = (x - 4, y - 6, page_width - right_margin_pt, y + 22)
                link_boxes.append((chapter, toc_page_index, rect))
                i += 1  # skip the page-number run
    return link_boxes


def _add_content_pages(writer, chapters):
    for _, chapter in _flatten_chapters(chapters):
        if chapter['pdf_fpath'] is not None:
            for page in chapter['reader'].pages:
                writer.add_page(page)


def _add_bookmarks(writer, chapters, parent=None):
    for chapter in chapters:
        if chapter['start_page'] is None:
            continue  # empty chapter (e.g. a module with no slides); no page to link to
        item = writer.add_outline_item(chapter['title'],
                                       chapter['start_page'] - 1,
                                       parent=parent)
        if chapter['children']:
            _add_bookmarks(writer, chapter['children'], parent=item)


def _add_toc_links(writer, link_boxes, page_offset=0):
    for chapter, toc_page_index, rect in link_boxes:
        link = pypdf.annotations.Link(
            rect=rect,
            target_page_index=chapter['start_page'] - 1,
            fit=pypdf.generic.Fit(fit_type='/FitH'),
            border=[0, 0, 0],
            )
        writer.add_annotation(toc_page_index + page_offset, link)


def merge_pdfs(chapters, output_fpath, args, *, dry_run=False):
    if dry_run:
        info(f'[dry-run] would create {output_fpath}')
        return

    flat = list(_flatten_chapters(chapters))
    if not flat:
        error('No chapters found to merge into a PDF')

    # Each chapter PDF is read once here and reused everywhere else
    # (start-page assignment, page copying, the page-size probe below)
    # instead of being re-parsed by pypdf on every pass.
    for _, chapter in flat:
        if chapter['pdf_fpath'] is not None:
            chapter['reader'] = pypdf.PdfReader(str(chapter['pdf_fpath']))

    page_size = None
    for _, chapter in flat:
        if chapter['pdf_fpath'] is not None:
            box = chapter['reader'].pages[0].mediabox
            page_size = (float(box.width), float(box.height))
            break
    if page_size is None:
        error('No slide PDFs found to merge')

    theme_width, theme_height = _theme_slide_size(
        args.theme.dpath / 'defaults.yaml')
    toc_page_count = _toc_page_count(len(flat), theme_height)

    title_md_fpath = args.input.parent / GLOBAL_TITLE_FILENAME
    if not title_md_fpath.exists():
        title_md_fpath = SLIDEFACTORY_ROOT / GLOBAL_TITLE_FILENAME

    writer = pypdf.PdfWriter()
    with tempfile.TemporaryDirectory() as tmp_dpath:
        tmp_dpath = Path(tmp_dpath)

        # Render the title slide in place if it's a project file (so any
        # relative asset paths, e.g. a logo image, keep resolving normally);
        # copy the bundled placeholder into the tmp dir instead, since
        # SLIDEFACTORY_ROOT isn't guaranteed to be writable at runtime.
        if title_md_fpath.parent == SLIDEFACTORY_ROOT:
            local_title_fpath = tmp_dpath / GLOBAL_TITLE_FILENAME
            local_title_fpath.write_text(title_md_fpath.read_text())
            title_md_fpath = local_title_fpath

        args_title = copy.copy(args)
        args_title.input = [title_md_fpath]
        args_title.output = tmp_dpath
        args_title.format = 'pdf'
        # This is slidefactory-authored content, not a user slide deck --
        # the user's own --filters/--pandoc-args may assume real slide
        # structure/front matter and shouldn't run against it.
        args_title.filters = []
        args_title.pandoc_args = ''
        args_title.extra_pandoc_vars = {'header-includes': HIDE_SLIDE_NUMBER_CSS}
        main_slides(args_title)
        title_reader = pypdf.PdfReader(
            str(tmp_dpath / title_md_fpath.with_suffix('.pdf').name))
        if not title_reader.pages:
            error(f'Generated title slide from {title_md_fpath} has no pages')

        if _md_has_body(title_md_fpath):
            # Real slide content beyond the front matter: headings split it
            # into their own real slides, so every rendered page is kept.
            title_page_count = len(title_reader.pages)
        else:
            # The title file is just YAML front matter with no body headings,
            # which makes pandoc's reveal.js writer append a second, empty
            # slide for the (nonexistent) headingless body -- confirmed against
            # pandoc directly, independent of our template. The title is always
            # exactly one slide in that case, so drop that trailing page rather
            # than trusting the renderer's page count.
            title_page_count = 1

        # Chapter start pages (used both for the TOC's own page numbers and
        # for bookmarks/links) depend on how many pages precede the content,
        # so they can only be assigned once the title slide has been
        # rendered and its page count is known.
        _assign_start_pages(chapters, title_page_count + toc_page_count)
        entries = [(level, chapter) for level, chapter in flat]
        markdown, chunks = _render_toc_markdown(
            entries, theme_width, theme_height)

        toc_md_fpath = tmp_dpath / 'toc.md'
        toc_md_fpath.write_text(markdown)

        args_toc = copy.copy(args)
        args_toc.input = [toc_md_fpath]
        args_toc.output = tmp_dpath
        args_toc.format = 'pdf'
        args_toc.filters = []
        args_toc.pandoc_args = ''
        args_toc.extra_pandoc_vars = {'header-includes': HIDE_SLIDE_NUMBER_CSS}
        main_slides(args_toc)

        toc_reader = pypdf.PdfReader(str(tmp_dpath / 'toc.pdf'))
        if len(toc_reader.pages) != toc_page_count:
            error(f'Generated TOC has {len(toc_reader.pages)} page(s), '
                  f'expected {toc_page_count}')
        link_boxes = _measure_toc_links(toc_reader, chunks, page_size[0],
                                        right_margin_pt=30)

        for page in title_reader.pages[:title_page_count]:
            writer.add_page(page)
        for page in toc_reader.pages:
            writer.add_page(page)

    _add_content_pages(writer, chapters)
    _add_bookmarks(writer, chapters)
    _add_toc_links(writer, link_boxes, page_offset=title_page_count)

    with output_fpath.open('wb') as f:
        writer.write(f)


def build_content(fpath, page_theme_fpath, args, *, line_fmt='{}'):
    info(f'Process {fpath}')
    with fpath.open() as fd:
        metadata = yaml.safe_load(fd.read())

    title = metadata["title"]
    content = ""
    chapters = []

    if "modules" in metadata:
        content += '<c-accordion>\n'
        for module in metadata["modules"]:
            mod_fpath = fpath.parent / module / fpath.name
            mod_title, mod_content, mod_chapters = \
                build_content(mod_fpath, page_theme_fpath, args,
                              line_fmt='<p>{}</p>')
            content += f'<c-accordion-item heading="{mod_title}" value="{module}">\n'  # noqa: E501
            content += mod_content
            content += '</c-accordion-item>\n'
            chapters.append({'title': mod_title, 'pdf_fpath': None,
                            'children': mod_chapters})
        content += '</c-accordion>\n'
    else:
        assert "slidesdir" in metadata
        slides_dpath = fpath.parent / metadata["slidesdir"]
        for md_fpath in sorted(slides_dpath.glob("*.md")):
            meta = read_slides_metadata(md_fpath)
            html_name = md_fpath.with_suffix(".html").name
            html_fpath = 'html' / fpath.parent / html_name
            slides_title = meta["title"]
            m = re.search(r'^\d+', html_name)
            prefix = '' if m is None else f'{int(m.group())}.'
            chapter_title = f'{prefix} {slides_title}'.strip()
            content += line_fmt.format(f'<c-link href="{html_fpath}" target="_blank">{prefix} {slides_title}</c-link>')  # noqa: E501
            content += '\n'

            # Convert slides
            formats = ['html']
            if args.with_pdf:
                formats += ['pdf']
            pdf_fpath = None
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
                if fmt == 'pdf':
                    pdf_fpath = (args_slides.output
                                / md_fpath.with_suffix('.pdf').name)

            chapters.append({'title': chapter_title, 'pdf_fpath': pdf_fpath,
                            'children': []})

    return title, content, chapters


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
            data = yaml.safe_load(data)
            for key, val in data.items():
                # Clean value
                if isinstance(val, str):
                    val = re.sub(r'<.*?>', ' ', val)
                    while '  ' in val:
                        val = val.replace('  ', ' ')
                    data[key] = val
            return data
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
    parser_pages.add_argument(
        '--merge-pdf', action='store_true',
        help=('also build a single merged PDF with a table of contents '
              'and chapter bookmarks (requires --with-pdf); '
              'slide pages are left untouched'))

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
    pandoc_vars.update(getattr(args, 'extra_pandoc_vars', {}))

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

    if args.merge_pdf and not args.with_pdf:
        error('--merge-pdf requires --with-pdf')

    page_theme_fpath = Path('html') / 'theme' / args.theme.name / 'csc.css'
    output_theme_dpath = args.output / page_theme_fpath.parent
    info(f'Copy theme to {output_theme_dpath}')
    shutil.copytree(args.theme.dpath, output_theme_dpath)

    title, html_content, chapters = \
        build_content(args.input, page_theme_fpath, args)

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

        merged_pdf_content = ''
        if args.merge_pdf:
            merged_fpath = args.output / 'slides-merged.pdf'
            info(f'Create {merged_fpath}')
            merge_pdfs(chapters, merged_fpath, args, dry_run=args.dry_run)
            merged_pdf_content = f'<c-link href="{merged_fpath.name}">Download a single merged PDF with a table of contents.</c-link>'  # noqa: E501
    else:
        pdf_content = "Not generated."
        merged_pdf_content = ''

    # Convert links to html
    info_content = re.sub(r'\[(.*?)\]\((.*?)\)',
                          r'<c-link href="\2">\1</c-link>',
                          args.info_content)

    index_fpath = args.output / 'index.html'
    create_index_page(index_fpath, title,
                      info_content, html_content, pdf_content,
                      merged_pdf_content)


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
