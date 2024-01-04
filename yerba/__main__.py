import sys
import os
from .main_rutine import MainRutine
from manim import logger


def main():
    if len(sys.argv) == 1:
        logger.error("You should specify an input filename")
        quit()
    elif len(sys.argv) == 2:
        filename = sys.argv[1]
        if os.path.exists(filename):
            pass
        elif os.path.exists(filename+".md"):
            filename = filename+".md"
        else:
            logger.error(f"File '{filename}' not found")
            quit()
    else:
        logger.error("Too many args")
        quit()

    main_rutine = MainRutine(filename)
    main_rutine.run()


if __name__ == "__main__":
    main()
