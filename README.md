<p align="center">
    <a href="https://github.com/bersp/yerba">
        <img src="https://raw.githubusercontent.com/bersp/yerba/main/logo/Yerba.png">
    </a>
</p>
<br />

Yerba is a Python CLI application that facilitates creating presentations by writing files in markdown format. The goal is to build an application that allows for creating aesthetically pleasing presentations in a short amount of time, while also being highly customizable and versatile.

**Note:** The application is currently in progress and is highly unstable. If you stumbled upon this page by chance, feel free to experiment with the application. However, you may prefer to return in the near future when the application is more stable and thoroughly documented.


## Installation

Yerba is currently only available for Linux, but the plan is to make it accessible for Mac and Windows in the near future.

### Manim
Yerba is built on top of [Manim](https://github.com/ManimCommunity/manim), so it's essential for the program to have access to this library. If you don't have Manim installed, refer to its [Linux installation guide](https://docs.manim.community/en/stable/installation/linux.html). If the following command runs without errors, everything should be set up correctly:
```bash
python -m manim --version
```

### LaTex
Currently, the only available backend for text processing is [XeTeX](https://en.wikipedia.org/wiki/XeTeX), an implementation of LaTeX with better font support. In most distributions, installing `texlive-xetex` should be sufficient. For example:
```bash
# Ubuntu (Debian)
apt install texlive-xetex

# Arch
pacman -S texlive-xetex
```

You can confirm a successful installation by running the following command:
```bash
xetex --version
```

### Yerba

The only additional requirement for Yerba is `rsvg-convert`. It is typically included by default in most Linux distributions. If not, it is usually part of the `librsvg2` package. For Ubuntu:
```bash
apt install librsvg2-bin
```

You can check if you have it installed by running the following command:
```bash
rsvg-convert --version
```

Finally, you can install Yerba from PyPI:
```bash
python -m pip install yerba
```

## Usage

This section is a work in progress. For now, check [usage_example.md](examples/usage_example.md) (use "code" view mode) and [usage_example.pdf](examples/usage_example.pdf) to give you and idea on how to use Yerba. You can render this presentation using:
```
yerba usage_example.md
# or
python -m yerba usage_example.md
```
---
