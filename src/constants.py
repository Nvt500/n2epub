import os
import sys


def get_root_dir() -> str:
    """Get the root directory"""

    return os.path.dirname(sys.argv[0])


class ProgError(Exception):
    """Programmer Error

        Something that should only be raised when a programming
        mistake happened like calling a method that isn't implemented.
    """