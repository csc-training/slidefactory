# How-to: Import an existing Powerpoint presentation

Tips for converting powerpoint slides to Markdown.


## Extracting text

Textual content (bullet point lists, source code etc.) can be extracted from a
Powerpoint presentation quite easily in a semi-automated fashion.

Steps:

1. Open the Powerpoint presentation in Libreoffice

2. Export the presentation as a HTML document:
   File -> Export -> Change format to "HTML Document (Impress) (.html;.htm)"
   -> Save -> Next -> Select "Single-document HTML" as "Publication Type"
   -> Create
   (Note: if asked to "Name HTML Design" after "Create", you can just close
   the dialogue or press "Cancel")

3. Convert the HTML document (`talk.html`) into Markdown (`talk.md`) using
   Pandoc:
   ```
   pandoc -t commonmark --filter=fix-header.py talk.html -o talk.md
   ```
   (Note: the filter ([fix-header.py](../filter/fix-header.py)) used above is
   optional, but it's quite handy to automatically remove bold font from
   headers e.g. when converting from a CSC 2016 style presentation.)

4. Manually fix the syntax of the resulting Markdown file (see
   [example.md](../example.md) for a working example or the
   [Syntax Guide](syntax-guide.md) for some general pointers)

5. Add a presentation metadata block (title, author, language, date) into the
   beginning of the file as described in the [Syntax Guide](syntax-guide.md).

In practice, most slides will need at least minor tweaking in Step 4. Since
all text in the slides will be included, slides with floating text boxes or
other text objects in figures will typically need a bit more extra attention.


## Extracting figures

Bitmap images (jpeg, png, gif, etc.) can be exported one by one by clicking
the image in Powerpoint and then "Save as Picture".

It is also possible to extract all the figures from presentation by converting
the presentation into a "zipped" file folder. See
[office support site](https://support.office.com/en-us/article/extract-files-or-objects-from-a-powerpoint-file-85511e6f-9e76-41ad-8424-eab8a5bbc517)
for detailed instructions.

The recommended form for drawings with Powerpoint shapes is to convert them to
Scalable vector graphics (svg). One possible workflow (utilising Linux command
line, **pdfseparate** and **inkscape**) is as follows:

- In Powerpoint, create a new "Blank presentation"
- Copy all the drawings to this new presentation, one drawing per slide
- Export the presentation to pdf
- Finally, in Linux command line use the script [pdf2svg.sh](pdf2svg.sh) for
  converting each drawing into separate .svg file

```bash
$ pdf2svg.sh presentation.pdf
```
As a result one obtains a set of `presentation-01.svg`, `presentation-02.svg`,
`...` files which can be further cleaned-up and refined with a vector drawing
program such as Inkscape.


## Cleaning up the converted svg's with Inkscape

The svg figures converted from pdf provide a good starting point, however, in
most cases they benefit from some clean up. Here are some tips (keyboard
shortcuts refer to Linux version):

- There is usually a frame over the figure which should be removed. There are
  also several (unnecessary) nested groups which can removed at the same time
  - Select all objects (`Ctrl-a`)
  - Ungroup the selection several times (`Ctrl-Shift-g`) until you see "No
    groups to ungroup" in the bottom of Inkscape window
  - The outermost frame (Path object) can now be selected and deleted.
  - The page can now be resized to actual drawing by selecting all objects
    (Ctrl-a) and `Edit -> Resize page to selection` (`Ctrl-Shift-r`)
- In some cases, there are "masks" that can show up as black boxes when
  converting presenations to pdf. Masking iamges can be exposed by selecting
  all objects (`Ctrl-a`) and then `Object -> Mask -> "Release`.
  - If there are no other "Image" objects in the drawing, masking images can
    be deleted by selecting one of the images, then right clicking, and then
    `Select Same -> Object type`.
- Text appears often so that individual words and characters are their own
  objects. Also, position of individual letters may be hard-coded in the
  converted drawing, so that when changing font the letter spacing is not
  adjusted correctly
  - Generally, it is recommended to create new text objects and delete the
    ones from the conversion
- Filled rectangles, circles, ellipses etc. are normally converted so that
  outer shape and filling (also shades if present) are their own objects. In
  principle, these appear just fine in the html and pdf output, however, for
  easier future editing it is recommended to make them into single objects:
  - Select the filling and move it a bit away (a Path object with Fill: some
    color / Stroke: None in the lower left corner)
  - Select the outer shape (a Path object with Fill: None / Stroke: some
    color), press `F7` to get color picker and left click then within the
    "Filling" object.
  - Delete the "Filling" object
  - Delete possible shadow images
  - Add new Shadow (if needed) from `Filters -> Shadows and glows`.

Other useful Inscape features and shortcuts:

- Zoom to page `5`, Zoom in `+`, Zoom out `-`
- Revert to Select mode `F1`
- Group objects `Ctrl-g`
- Rubber band selection inside other objects / groups , keep `Shift` pressed
  and the click and draw
- Duplicate selection `Ctrl-d`, clone selection `Alt-d`
  - Both duplicate and clone are placed on the top of the original and
    selected, and thus can be immediately moved
  - For clones, changing the original (scaling, rotating, stroke, fill, etc.)
    affects also the clone(s)
- Creating a pattern (row, column, array) of objects: `Edit -> Clone -> Create
  Tiled Clones`
  - Note that there is a clone also on the top of the original (bug / feature)
    which you probably want to delete.
