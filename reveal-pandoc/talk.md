
# Slides for the comparison of different markdown presentation engines { .title-en }

CSC Training, 2017-08

---

# Slides for the comparison of different markdown presentation engines with some extra words to make it wrap { .title-fi }

CSC Training, 2017-08

---

# Example text slide

- some relevant fact
    - sub-point that includes also funky equations like $e = mc^2$ and
      $\frac{\delta^2 u}{\delta t^2} = c^2 \nabla^2 u$
- another point to make

---

# Example picture

![](img/nuuksio-lake.jpg)

Explanation of the pretty picture.

---

# Two columns

<div class="column">
* my point
    - more detailed info
* some longer line of text to see where it wraps and anything else funky
</div>

<div class="column">
- other point
- some longer line of text to see where it wraps and anything else funky
</div>

---

# Two columns with a picture

<div class="column">
- my point
- some longer line of text to see where it wraps and anything else funky
</div>

<div class="column">
![](img/koulutusaula.jpg){width=50%}
</div>

---

# Code snippets

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

In-line code looks like this: ```count = x + y```. So this means that for
example calling function ```foobar(args, x)``` would end up so.

---

# Tables and text

|            |           | 1     | 2     | 4     | 8     |
| ---------- | --------- | ----: | ----: | ----: | ----: |
| **Case 1** | vanilla   | 0.757 | 0.719 | 0.574 | 0.547 |
|            | optimised | 0.899 | 0.838 | 0.658 | 0.607 |
| **Case 2** | vanilla   | 1.252 | 1.111 | 0.684 | 0.756 |
|            | optimised | 1.443 | 1.277 | 0.748 | 0.818 |

Default style (up) and alternative style (down).

<div class="show-cells">

|            |           | 1     | 2     | 4     | 8     |
| ---------- | --------- | ----: | ----: | ----: | ----: |
| **Case 1** | vanilla   | 0.757 | 0.719 | 0.574 | 0.547 |
|            | optimised | 0.899 | 0.838 | 0.658 | 0.607 |

</div>

---

# Firstname Lastname { .author }

Groupname, title, or something   
CSC – IT Center for Science Ltd.

firstname.lastname@csc.fi

![](img/csc-identicon.png)

