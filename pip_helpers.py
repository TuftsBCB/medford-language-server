"""pip_helpers.py

By: Liam Strand
On: June 2022

Provides an abstraction around running subprocesses that call pip
"""

import subprocess as sp
import sys


def pip_install() -> bool:
    """Runs pip install mfdls
    Parameters: None
       Returns: True if install succeeded, False otherwise
       Effects: Installs mfdls
    """
    try:
        sp.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-i",
                "https://test.pypi.org/simple/",
                "mfdls",
            ],
            check=True,
        )
    except sp.CalledProcessError:
        return False
    else:
        return True


def pip_upgrade() -> bool:
    """Runs pip install --upgrade mfdls
    Parameters: None
       Returns: True if upgraded succeeded, False otherwise
       Effects: Upgrades mfdls
    """
    try:
        sp.run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "-i",
                "https://test.pypi.org/simple/",
                "mfdls",
            ],
            check=True,
        )
    except sp.CalledProcessError:
        return False
    else:
        return True


def pip_uninstall() -> bool:
    """Runs pip uninstall mfdls
    Parameters: None
       Returns: True if uninstall succeeded, False otherwise
       Effects: Uninstalls mfdls
    """
    try:
        sp.run(
            [sys.executable, "-m", "pip", "uninstall", "mfdls"], input=b"Y", check=True
        )
    except sp.CalledProcessError:
        return False
    else:
        return True
