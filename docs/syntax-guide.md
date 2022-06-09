# Syntax Guide for Markdown

Brief overview of correct syntax (or at least syntax that works) for the
Markdown files used to generate the reveal.js slides using Pandoc.

## Metadata

Every slide set should start with a YAML metadata block that defines e.g. the
title and language of the title set. The metadata block is used to
automatically generate a title slide for the presentation.

The following metadata will be used to generate the title slide:
- title: title of the presentation
- lang: language of the presentation (en/fi)
- (optional) subtitle: subtitle of the presentation
- (optional) event: name of the course/meeting
- (optional) author: author(s) of the presentation
- (optional) date: date of the presentation

The language is mandatory, since it influences the choice of background image
for the slide. Currently valid values are: `en` or `fi`.

For example:
```
---
title:  HIP and GPU kernels
event:  GPU programming with HIP
date:   2021-11
lang:   en
---
```

## Slide separation

Slides are separated by simply using first-level headers. Each first-level
header will be used as the title for the slide and anything that follows it
(until the next first-level header) as the content.

If you want, you can also separate slides explicitly by using a triple dash
'---' surrounded by empty lines.

## Example

As a guide for correct syntax (or at least syntax that works), you can refer
to the [example markdown presentation](../example.md). It should have examples
of most common slide layouts etc.
