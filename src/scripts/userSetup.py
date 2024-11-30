import os
import sys
import inspect

from maya import cmds


def msg():
    return "Loading script editor highlighter"


# the script doesn't appear to work in Maya 2025 yet
if cmds.about(version=True).startswith("2025"):
    pass
else:
    print(msg())

    file_path = os.path.abspath(inspect.getfile(msg))
    source_path = os.path.dirname(os.path.dirname(file_path))
    sys.path.append(source_path)
    from highlighter import setup_highlighter
    setup_highlighter()
