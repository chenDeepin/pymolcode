"""pymolcode CLI – launches PyMOL with the pymolcode LLM panel.

Usage:
    pymolcode                       # launch PyMOL GUI + chat panel
    pymolcode --headless            # headless bridge server (no GUI)
    pymolcode serve --rest          # start REST API server
    pymolcode auth login <provider> # authenticate with a provider
    pymolcode auth list             # list stored credentials
    pymolcode auth logout <provider># remove credentials
    pymolcode ultrawork "..."       # run full agentic workflow
    pymolcode [pymol args]          # pass extra args to PyMOL
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
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


# ---------------------------------------------------------------------------
# Auth subcommands
# ---------------------------------------------------------------------------


def _cmd_auth_login(args: argparse.Namespace) -> int:
    """Authenticate with a provider (OAuth or API key)."""
    from python.auth.oauth import OAuthManager
    from python.auth.providers import OAUTH_PROVIDERS, register_all_providers

    provider_id: str = args.provider

    if provider_id not in OAUTH_PROVIDERS:
        print(f"Unknown provider: {provider_id}")
        print(f"Available: {', '.join(sorted(OAUTH_PROVIDERS))}")
        return 1

    config = OAUTH_PROVIDERS[provider_id]
    print(f"\n  {config['name']} Authentication")
    print(f"  {config.get('instructions', '')}\n")

    flow = config.get("flow", "api_key")

    if flow == "api_key":
        api_key = getpass.getpass("API key: ").strip()
        if not api_key:
            print("Cancelled.")
            return 1
        manager = OAuthManager()
        manager.set_api_key(provider_id, api_key)
        print(f"Saved API key for {config['name']}.")
        return 0

    manager = OAuthManager()
    register_all_providers(manager)
    result = asyncio.run(manager.authorize(provider_id))
    if result.success:
        print(f"\nLogin successful for {config['name']}.")
        return 0
    else:
        print(f"\nLogin failed: {result.error}")
        return 1


def _cmd_auth_list(args: argparse.Namespace) -> int:
    """List stored credentials."""
    from python.auth.providers import OAUTH_PROVIDERS
    from python.auth.token_store import TokenStore

    store = TokenStore()
    providers = store.list_providers()

    if not providers:
        print("No stored credentials.")
        print("Run: pymolcode auth login <provider>")
        print(f"Available: {', '.join(sorted(OAUTH_PROVIDERS))}")
        return 0

    print(f"\nStored credentials ({len(providers)}):\n")
    for info in providers:
        label = OAUTH_PROVIDERS.get(info.provider_id, {}).get("name", info.provider_id)
        status = "api_key" if info.is_api_key else "oauth"
        expired = " (expired)" if info.is_expired else ""
        masked = info.access_token[:8] + "..." if len(info.access_token) > 8 else "***"
        print(f"  {label:<20} {status:<10} {masked}{expired}")
    print()
    return 0


def _cmd_auth_logout(args: argparse.Namespace) -> int:
    """Remove stored credentials."""
    from python.auth.providers import OAUTH_PROVIDERS
    from python.auth.token_store import TokenStore

    store = TokenStore()
    provider_id: str = args.provider
    label = OAUTH_PROVIDERS.get(provider_id, {}).get("name", provider_id)

    if store.remove(provider_id):
        print(f"Removed credentials for {label}.")
    else:
        print(f"No credentials found for {label}.")
    return 0


# ---------------------------------------------------------------------------
# Serve subcommand
# ---------------------------------------------------------------------------


def _cmd_serve(args: argparse.Namespace) -> int:
    """Start the REST API server."""
    import logging

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    )

    if not args.rest:
        print("Error: Must specify --rest for REST server mode")
        print("Usage: pymolcode serve --rest [--host HOST] [--port PORT] [--token TOKEN]")
        return 1

    from python.bridge.rest_adapter import run_rest_server_with_runtime

    headless = not args.gui

    try:
        asyncio.run(
            run_rest_server_with_runtime(
                headless=headless,
                host=args.host,
                port=args.port,
                token=args.token,
                workspace=args.workspace,
            )
        )
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as exc:
        print(f"Error: {exc}")
        return 1

    return 0


# ---------------------------------------------------------------------------
# Ultrawork subcommand
# ---------------------------------------------------------------------------


def _cmd_ultrawork(args: argparse.Namespace) -> int:
    """Run an ultrawork agentic workflow."""
    prompt: str = args.prompt
    if not prompt:
        print('Usage: pymolcode ultrawork "<prompt>"')
        return 1

    from python.workflow.ultrawork import run_ultrawork

    return asyncio.run(run_ultrawork(prompt))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _get_version() -> str:
    try:
        from importlib.metadata import version

        return version("pymolcode")
    except Exception:
        return "0.2.0"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pymolcode",
        description="Launch PyMOL with the pymolcode LLM assistant panel.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"pymolcode {_get_version()}",
    )
    subparsers = parser.add_subparsers(dest="command")

    # -- auth ---------------------------------------------------------------
    auth_parser = subparsers.add_parser("auth", help="Manage credentials")
    auth_sub = auth_parser.add_subparsers(dest="auth_command")

    login_p = auth_sub.add_parser("login", help="Log in to a provider")
    login_p.add_argument("provider", help="Provider ID (e.g. anthropic, openai, google)")
    login_p.set_defaults(func=_cmd_auth_login)

    list_p = auth_sub.add_parser("list", help="List stored credentials")
    list_p.set_defaults(func=_cmd_auth_list)

    logout_p = auth_sub.add_parser("logout", help="Remove credentials")
    logout_p.add_argument("provider", help="Provider ID")
    logout_p.set_defaults(func=_cmd_auth_logout)

    # -- serve --------------------------------------------------------------
    serve_parser = subparsers.add_parser("serve", help="Start API server")
    serve_parser.add_argument(
        "--rest",
        action="store_true",
        help="Start REST API server",
    )
    serve_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address to bind to (default: 127.0.0.1)",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=9124,
        help="Port to listen on (default: 9124)",
    )
    serve_parser.add_argument(
        "--token",
        default=None,
        help="Bearer token for authentication (optional)",
    )
    serve_parser.add_argument(
        "--workspace",
        default=None,
        help="Workspace directory for memory and sessions (optional)",
    )
    serve_parser.add_argument(
        "--gui",
        action="store_true",
        help="Start PyMOL with GUI (default: headless)",
    )
    serve_parser.set_defaults(func=_cmd_serve)

    # -- ultrawork ----------------------------------------------------------
    uw_parser = subparsers.add_parser("ultrawork", help="Run agentic workflow")
    uw_parser.add_argument("prompt", nargs="?", default="", help="Task description")
    uw_parser.set_defaults(func=_cmd_ultrawork)

    # -- legacy flags -------------------------------------------------------
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run the JSON-RPC bridge server without PyMOL GUI.",
    )
    parser.add_argument(
        "--with-rest",
        action="store_true",
        help="Start REST API server alongside GUI (port 9124).",
    )

    # Use parse_known_args to handle pymol_args flexibly
    args, pymol_args = parser.parse_known_args(argv if argv is not None else sys.argv[1:])
    args.pymol_args = pymol_args  # Attach unknown args as pymol_args

    # Dispatch subcommand
    if hasattr(args, "func"):
        return args.func(args)

    if args.command == "auth":
        auth_parser.print_help()
        return 1

    if args.command == "serve":
        serve_parser.print_help()
        return 1

    if args.headless:
        from python.bridge.server import main as bridge_main

        bridge_main()
        return 0

    # Default: launch PyMOL
    root = str(_project_root())
    pypath = os.environ.get("PYTHONPATH", "")
    if root not in pypath.split(os.pathsep):
        os.environ["PYTHONPATH"] = root + (os.pathsep + pypath if pypath else "")

    import tempfile

    splash_png = str(Path(root) / "python" / "pymol" / "assets" / "splash.png")
    rest_code = ""
    if args.with_rest:
        rest_code = (
            "# Start REST server\n"
            "import logging\n"
            "logging.basicConfig(level=logging.INFO)\n"
            "from python.bridge.gui_rest_adapter import start_rest_thread\n"
            "start_rest_thread(port=9124, host='127.0.0.1')\n"
            "import time\n"
            "time.sleep(0.5)\n"
        )
    startup_code = (
        "import sys, os\n"
        f"sys.path.insert(0, {root!r})\n"
        f"{rest_code}"
        "from python.pymol.panel import init_plugin\n"
        "from pymol import cmd\n"
        "cmd.set('internal_gui_width', 255)\n"
        "init_plugin()\n"
        f"if os.path.exists({splash_png!r}):\n"
        f"    cmd.load_png({splash_png!r}, 0, quiet=1)\n"
        "print()\n"
        "print(' PymolCode \\u2014 LLM-Enhanced Molecular Visualization')\n"
        "print(' Built using PyMOL\\u2122 technology.')\n"
        "print(' PyMOL is a trademark of Schr\\u00f6dinger, LLC.')\n"
        "print()\n"
    )
    fd, startup_path = tempfile.mkstemp(suffix=".py", prefix="pymolcode_startup_")
    try:
        os.write(fd, startup_code.encode())
        os.close(fd)

        pymol_argv = [
            sys.executable,
            "-m",
            "pymol",
            "-q",
            "-W",
            "1400",
            "-H",
            "900",
            "-r",
            startup_path,
        ]
        pymol_argv.extend(args.pymol_args or [])

        os.execvpe(sys.executable, pymol_argv, os.environ)
    finally:
        try:
            os.unlink(startup_path)
        except OSError:
            pass

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
