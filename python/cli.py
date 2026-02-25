"""pymolcode CLI – launches PyMOL with the pymolcode LLM panel.

Usage:
    pymolcode                # launch PyMOL GUI + chat panel
    pymolcode --headless     # headless bridge server (no GUI)
    pymolcode [pymol args]   # pass extra args to PyMOL
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _pymolcode_startup_script() -> str:
    """Return a tiny Python snippet that PyMOL will ``-r`` to load our panel."""
    return (
        "import sys, os; "
        f"sys.path.insert(0, {str(_project_root())!r}); "
        "from python.pymol.panel import init_plugin; "
        "init_plugin()"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pymolcode",
        description="Launch PyMOL with the pymolcode LLM assistant panel.",
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Run the JSON-RPC bridge server without PyMOL GUI.",
    )
    parser.add_argument(
        "pymol_args", nargs="*",
        help="Extra arguments forwarded to PyMOL (e.g. structure files).",
    )

    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if args.headless:
        from python.bridge.server import main as bridge_main
        bridge_main()
        return 0

    # Ensure our project root is on PYTHONPATH so the -r script can import
    root = str(_project_root())
    pypath = os.environ.get("PYTHONPATH", "")
    if root not in pypath.split(os.pathsep):
        os.environ["PYTHONPATH"] = root + (os.pathsep + pypath if pypath else "")

    # Write a tiny startup script to a temp file (PyMOL -r needs a real path)
    import tempfile
    startup_code = (
        "import sys, os\n"
        f"sys.path.insert(0, {root!r})\n"
        "from python.pymol.panel import init_plugin\n"
        "from pymol import cmd\n"
        "cmd.set('internal_gui_width', 350)\n"
        "init_plugin()\n"
    )
    fd, startup_path = tempfile.mkstemp(suffix=".py", prefix="pymolcode_startup_")
    try:
        os.write(fd, startup_code.encode())
        os.close(fd)

        # Build pymol launch command
        pymol_argv = [sys.executable, "-m", "pymol", "-r", startup_path]
        pymol_argv.extend(args.pymol_args)

        os.execvpe(sys.executable, pymol_argv, os.environ)
    finally:
        # execvpe replaces the process, so this only runs on failure
        try:
            os.unlink(startup_path)
        except OSError:
            pass

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
