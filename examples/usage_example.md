---
cover:
  title: Usege example
  subtitle: some example slides to see how [Yerba](color=GREEN) works
  author: Bernado L. Español
---

This is a title
======================================================================
And this is a subtitle
-------------------

Yo can write text, \textbf{in-line math} $f(x) = e^{x}$ and
$$
  \text{math} \quad [\int](var="v")_0^{x} f(x')~ [dx](var="v") = f(x)
$$
out of line.

>! vspace - 1
>! pause
>! mod - "v", color=RED

Additionally, you can write [colorful things](color=BLUE)

>! pause

```python mate
a1 = Arrow(start=LEFT+DOWN/3, end=2.5*LEFT+DOWN/3, color=GRAY)
t1 = (p.add_text(r"Also, this space here was added using a \texttt{vspace}")
       .next_to(a1, RIGHT))

p.add([a1, t1], box="floating")
p.pause()

a2 = Arrow(start=ORIGIN, end=1.2*UP, color=GRAY).next_to(t1, DOWN)
t2 = p.add_text(r"And this was written directly in Python").next_to(a2, DOWN)

p.add([a2, t2], box="floating")
p.pause()
p.remove([a1, a2, t1, t2])
```


# notitle

>! set box - 'full'

Even you can do [other things](fill_color=[WHITE,GREEN,WHITE]) with the text and math

$$
  [2](color=RED,var="v1") + [3](color=BLUE,var="v2")
  = [5](var="v3")
$$

>! pause
>! mod - "v1", rotate=-90
>! mod - "v2", font_size=60
>! bec - "v3", p.text("$\pi$")

Grids
======================================================================
A bit about grids and subgrids
---------------------------------

>! def grid - [['A', 'C'], ['B', 'C'], ['D', 'D']], height_ratios=[1, 1, 0.1]

>! set box - 'A', arrange='center'

This is one \textit{box}.
$$
    \int 2 ~d x = 2t
$$

>! set box - 'B'

>! add image - 'example.png', height='100%', draft_mode=True

>! set box - 'C'

Boxes can have different shapes
>! add image - 'example.png', width='100%', draft_mode=False, arrange='center'

>! pause
>! set box - 'D', arrange='center'
>! add - p.named_boxes.content.get_bbox_grid(), box="floating"

These are the defined boxes
