# csc-2018-portrait

Theme for generating A4 handout title pages.

## Custom page geometry

One needs to set a custom page geometry to use the theme, e.g.:
`--config width=905 --config height=1280 -t csc-2018-portrait`

## Example markdown input

```
---
title:  CSC Summer School in High-Performance Computing 2022
date:   June 6 - July 5, 2022
author: CSC - IT Center for Science, Finland
lang:   en
---

# {.author}

All material (C) 2011–2022 by CSC – IT Center for Science Ltd.
This work is licensed under a **Creative Commons Attribution-ShareAlike 4.0**
International License, http://creativecommons.org/licenses/by-sa/4.0

# Message passing interface {.section}

# Hybrid programming {.section}
```
