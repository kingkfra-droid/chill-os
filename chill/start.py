#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import environment
from . import rootfs


VERSION = "0.1.0"

CHILLOS_HOME = Path.home() / ".chillos"
WORKSPACE = CHILLOS_HOME / "workspace"


def command_exists(command):
    return shutil.which(command) is not None


def initialize_environment():
    """Initialize the ChillOS userspace."""

    environment.initialize()

    CHILLOS_HOME.mkdir(
        parents=True,
        exist_ok=True,
    )

    WORKSPACE.mkdir(
        parents=True,
        exist_ok=True,
    )

    os.environ["CHILLOS_HOME"] = str(CHILLOS_HOME)
    os.environ["CHILLOS_ACTIVE"] = "1"


def check_environment():
    """Check whether the Android/Termux environment is suitable."""

    if not environment.is_termux():
        print("ERROR: ChillOS is designed to run inside Termux.")
        print()
        print("Start ChillOS from a Termux session.")
        return False

    if not command_exists("python"):
        print("ERROR: Python is not available.")
        print("Install it with: pkg install python")
        return False

    return True


def check_rootfs():
    """Check whether the Debian RootFS is ready."""

    if not rootfs.proot_distro_available():
        print("ERROR: proot-distro is not installed.")
        print()
        print("Install it with:")
        print("  pkg install proot-distro")
        return False

    if not rootfs.distro_installed():
        print("ChillOS Debian RootFS is not installed.")
        print()
        print("Build it with:")
        print("  chill rootfs build")
        return False

    if not rootfs.rootfs_ready():
        print("ERROR: Debian RootFS is installed but not ready.")
        print()
        print("Run:")
        print("  chill rootfs status")
        return False

    return True


def enter_rootfs():
    """Launch the ChillOS Debian environment."""

    print()
    print("Starting ChillOS...")
    print(f"Version    : {VERSION}")
    print(f"Workspace  : {WORKSPACE}")
    print()

    initialize_environment()

    os.environ["CHILLOS_ACTIVE"] = "1"

    command = [
        "proot-distro",
        "login",
        rootfs.DISTRO,
    ]

    try:
        result = subprocess.run(command)
        return result.returncode

    except KeyboardInterrupt:
        print()
        print("ChillOS session interrupted.")
        return 130

    except FileNotFoundError:
        print("ERROR: proot-distro could not be found.")
        return 1

    except Exception as exc:
        print(f"ERROR: failed to start ChillOS: {exc}")
        return 1


def start():
    """Initialize and start a ChillOS session."""

    print()
    print("╔════════════════════════════════════════╗")
    print("║             CHILLOS START              ║")
    print("╚════════════════════════════════════════╝")
    print()

    if not check_environment():
        return 1

    print("[1/3] Android/Termux environment: OK")

    initialize_environment()

    print("[2/3] ChillOS workspace: OK")

    if not check_rootfs():
        return 1

    print("[3/3] Debian RootFS: READY")
    print()

    return enter_rootfs()


def usage():
    print("""
ChillOS Start

Usage:

  chill start
      Initialize ChillOS and enter the Debian environment.

  chill start --check
      Check the environment without starting a session.

  chill start --help
      Show this help message.
""")


def check_only():
    """Run startup checks without launching the RootFS."""

    print()
    print("╔════════════════════════════════════════╗")
    print("║          CHILLOS START CHECK           ║")
    print("╚════════════════════════════════════════╝")
    print()

    if not check_environment():
        return 1

    print("[ OK ] Android/Termux environment")

    initialize_environment()

    print("[ OK ] ChillOS workspace")

    if not check_rootfs():
        return 1

    print("[ OK ] Debian RootFS")
    print()
    print("ChillOS is ready to start.")
    print()

    return 0


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    if not args:
        return start()

    command = args[0].lower()

    if command in ("--check", "check"):
        return check_only()

    if command in ("--help", "-h", "help"):
        usage()
        return 0

    return start()


if __name__ == "__main__":
    raise SystemExit(main())
