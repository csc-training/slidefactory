---
title:  Example slides for layout testing
author: CSC Training
date:   2019-02
lang:   en
---


# Font size and weight

- Lorem ipsum dolor sit amet, *consectetuer* adipiscing elit. Sed posuere
  ***interdum sem***.
- Quisque ligula eros ullamcorper quis,
  <small>lacinia quis ***facilisis*** sed sapien</small>.
- **Mauris varius** diam vitae arcu.


# Math formulas

- Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Sed posuere
  interdum sem.
- Quisque ligula eros ullamcorper quis ($e = mc^2$), lacinia quis facilisis
  sed sapien.
- Mauris varius diam vitae arcu:
  $\frac{\partial^2 u}{\partial t^2} = c^2 \nabla^2 v$
    - Sed arcu lectus auctor vitae, consectetuer et venenatis eget velit.

$$\oint_{\partial \Sigma} E \cdot dl
    = - \int_\Sigma \frac{\partial B}{\partial t} \cdot d A$$


# Nesting lists 1

- Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Sed posuere
  interdum sem.
    - Quisque ligula eros ullamcorper quis, lacinia quis facilisis sed sapien.
      Mauris varius diam vitae arcu.
    - Sed arcu lectus auctor vitae, consectetuer et venenatis eget velit.
        - sed augue orci
        - lacinia eu tincidunt et eleifend nec lacus
- Donec ultricies nisl ut felis, suspendisse potenti.
    - Lorem ipsum ligula ut hendrerit mollis, ipsum erat vehicula risus, eu
      suscipit sem libero nec erat.


# Nesting lists 2

1. Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Sed posuere
   interdum sem.
    - Quisque ligula eros ullamcorper quis, lacinia quis facilisis sed sapien.
      Mauris varius diam vitae arcu.
    - Sed arcu lectus auctor vitae, consectetuer et venenatis eget velit.
        - sed augue orci
        - lacinia eu tincidunt et eleifend nec lacus
2. Donec ultricies nisl ut felis, suspendisse potenti.
    - Lorem ipsum ligula ut hendrerit mollis, ipsum erat vehicula risus, eu
      suscipit sem libero nec erat.


# Nesting lists 3

1. Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Sed posuere
   interdum sem.
    - Quisque ligula eros ullamcorper quis, lacinia quis facilisis sed sapien.
      Mauris varius diam vitae arcu.
    - Sed arcu lectus auctor vitae, consectetuer et venenatis eget velit.
        1. sed augue orci
        2. lacinia eu tincidunt et eleifend nec lacus
2. Donec ultricies nisl ut felis, suspendisse potenti.
    - Lorem ipsum ligula ut hendrerit mollis, ipsum erat vehicula risus, eu
      suscipit sem libero nec erat.


# Nesting lists 4

- Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Sed posuere
  interdum sem.
    1. Quisque ligula eros ullamcorper quis, lacinia quis facilisis sed sapien.
       Mauris varius diam vitae arcu.
    2. Sed arcu lectus auctor vitae, consectetuer et venenatis eget velit.
        * sed augue orci
        * lacinia eu tincidunt et eleifend nec lacus
- Donec ultricies nisl ut felis, suspendisse potenti.
    - Lorem ipsum ligula ut hendrerit mollis, ipsum erat vehicula risus, eu
      suscipit sem libero nec erat.


# Nesting lists 5

- Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Sed posuere
  interdum sem.
    1. Quisque ligula eros ullamcorper quis, lacinia quis facilisis sed sapien.
       Mauris varius diam vitae arcu.
    2. Sed arcu lectus auctor vitae, consectetuer et venenatis eget velit.
        1. sed augue orci
        2. lacinia eu tincidunt et eleifend nec lacus
- Donec ultricies nisl ut felis, suspendisse potenti.
    - Lorem ipsum ligula ut hendrerit mollis, ipsum erat vehicula risus, eu
      suscipit sem libero nec erat.


# Definition list

Lorem
  : ipsum dolor sit amet

Consectetuer adipiscing elit
  : Sed posuere interdum sem.
  : Quisque ligula eros ullamcorper quis, lacinia quis facilisis sed sapien.

Mauris
  : varius diam vitae arcu

    Sed arcu lectus auctor vitae, consectetuer et venenatis eget velit.


# Images 1

![](img/nuuksio-lake.jpg)

Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Sed posuere
interdum sem.


# Images 2

![](img/nuuksio-lake.jpg){width=50%}

Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Sed posuere
interdum sem.


# Columns 1

<div class="column">
- Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Sed posuere
  interdum sem.
    - quisque ligula eros ullamcorper quis
    - lacinia quis facilisis sed sapien
- Mauris varius diam vitae arcu.
</div>

<div class="column">
- Sed arcu lectus auctor vitae, consectetuer et venenatis eget velit.
- Sed augue orci, lacinia eu tincidunt et eleifend nec lacus.
</div>


# Columns 2

<div class="column">
- Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Sed posuere
  interdum sem.
    - quisque ligula eros ullamcorper quis
    - lacinia quis facilisis sed sapien
- Mauris varius diam vitae arcu.
</div>

<div class="column">
![](img/koulutusaula.jpg){width=50%}
</div>


# Code high-lighting

```python
import os

if os.path.isfile('foobar'):
    with open('foobar') as fp:
        txt = fp.read()
    print('File contents:')
    print(txt)
```

```c
#include <stdio.h>

int square(x) {
    printf("Going to square value %d.", x);
    return x*x;
}
```

Lorem ipsum dolor sit amet, consectetuer adipiscing elit: ```count = x + y```.
Sed posuere interdum ```foobar(args, x)``` sem.


# Tables 1 (default)

|            |             | 1     | 2     | 4     | 8     |
| ---------- | ----------- | ----: | ----: | ----: | ----: |
| **Case 1** | vanilla     | 0.757 | 0.719 | 0.574 | 0.547 |
|            | *optimised* | 0.899 | 0.838 | 0.658 | 0.607 |
| **Case 2** | vanilla     | 1.252 | 1.111 | 0.684 | 0.756 |
|            | *optimised* | 1.443 | 1.277 | 0.748 | 0.818 |

Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Sed posuere interdum
sem.


# Tables 2 (default + highlighted cells)

|            |             | 1     | 2           | 4           | 8     |
| ---------- | ----------- | ----: | ----------: | ----------: | ----: |
| **Case 1** | vanilla     | 0.757 | 0.719       | 0.574       | 0.547 |
|            | *optimised* | 0.899 | 0.838       | 0.658       | 0.607 |
| **Case 2** | vanilla     | 1.252 | ***1.111*** | 0.684       | 0.756 |
|            | *optimised* | 1.443 | 1.277       | ***0.748*** | 0.818 |

Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Sed posuere interdum
sem.


# Tables 3 (colour) {.table-colour}

|            |             | 1     | 2           | 4           | 8     |
| ---------- | ----------- | ----: | ----------: | ----------: | ----: |
| **Case 1** | vanilla     | 0.757 | 0.719       | 0.574       | 0.547 |
|            | *optimised* | 0.899 | 0.838       | 0.658       | 0.607 |
| **Case 2** | vanilla     | 1.252 | ***1.111*** | 0.684       | 0.756 |
|            | *optimised* | 1.443 | 1.277       | ***0.748*** | 0.818 |

Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Sed posuere interdum
sem.


# Tables 4 (grid) {.table-grid}

|            |             | 1     | 2           | 4           | 8     |
| ---------- | ----------- | ----: | ----------: | ----------: | ----: |
| **Case 1** | vanilla     | 0.757 | 0.719       | 0.574       | 0.547 |
|            | *optimised* | 0.899 | 0.838       | 0.658       | 0.607 |
| **Case 2** | vanilla     | 1.252 | ***1.111*** | 0.684       | 0.756 |
|            | *optimised* | 1.443 | 1.277       | ***0.748*** | 0.818 |

Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Sed posuere interdum
sem.


# Tables 5 (none) {.table-none}

|            |             | 1     | 2           | 4           | 8     |
| ---------- | ----------- | ----: | ----------: | ----------: | ----: |
| **Case 1** | vanilla     | 0.757 | 0.719       | 0.574       | 0.547 |
|            | *optimised* | 0.899 | 0.838       | 0.658       | 0.607 |
| **Case 2** | vanilla     | 1.252 | ***1.111*** | 0.684       | 0.756 |
|            | *optimised* | 1.443 | 1.277       | ***0.748*** | 0.818 |

Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Sed posuere interdum
sem.


# Firstname Lastname { .author }

| Groupname, title, or something
| CSC – IT Center for Science Ltd.

firstname.lastname@csc.fi

![](theme/csc-2016/img/csc-identicon.png)

