#!/usr/bin/env python3

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


DISTRO = "debian"
CHILLOS_HOME = Path.home() / ".chillos"
ROOTFS_DIR = CHILLOS_HOME / "rootfs"


def command_exists(command):
    return shutil.which(command) is not None


def run(command, timeout=30):
    try:
        return subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None


def architecture():
    machine = platform.machine().lower()

    mapping = {
        "aarch64": "arm64",
        "arm64": "arm64",
        "x86_64": "amd64",
        "amd64": "amd64",
        "armv8l": "arm64",
        "armv7l": "arm",
        "arm": "arm",
        "i386": "i386",
        "i686": "i386",
    }

    return mapping.get(machine, machine)


def proot_available():
    return (
        command_exists("proot")
        or command_exists("proot-distro")
    )


def proot_distro_available():
    return command_exists("proot-distro")


def ensure_directories():
    CHILLOS_HOME.mkdir(
        parents=True,
        exist_ok=True,
    )

    ROOTFS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def distro_list():
    if not proot_distro_available():
        return []

    result = run(
        ["proot-distro", "list"],
        timeout=10,
    )

    if result is None:
        return []

    return result.stdout.splitlines()


def distro_installed():
    lines = distro_list()

    for line in lines:
        normalized = line.lower()

        if DISTRO in normalized:
            if "installed" in normalized:
                return True

    try:
        result = run(
            [
                "proot-distro",
                "login",
                DISTRO,
                "--",
                "true",
            ],
            timeout=15,
        )

        return (
            result is not None
            and result.returncode == 0
        )

    except Exception:
        return False


def rootfs_ready():
    if not proot_distro_available():
        return False

    if not distro_installed():
        return False

    result = run(
        [
            "proot-distro",
            "login",
            DISTRO,
            "--",
            "sh",
            "-c",
            "test -f /etc/debian_version",
        ],
        timeout=15,
    )

    return (
        result is not None
        and result.returncode == 0
    )


def install():
    ensure_directories()

    if not proot_distro_available():
        print("ERROR: proot-distro is not installed.")
        print()
        print("Install it with:")
        print("  pkg install proot-distro")
        return False

    if distro_installed():
        print("ChillOS RootFS is already installed.")
        return True

    print()
    print("╔════════════════════════════════════════╗")
    print("║         CHILLOS ROOTFS INSTALL         ║")
    print("╚════════════════════════════════════════╝")
    print()

    print(f"Distribution : {DISTRO}")
    print(f"Architecture : {architecture()}")
    print()

    print("Installing Debian through proot-distro...")
    print()

    result = run(
        [
            "proot-distro",
            "install",
            DISTRO,
        ],
        timeout=1800,
    )

    if result is None:
        print("ERROR: RootFS installation timed out.")
        return False

    if result.returncode != 0:
        print("ERROR: RootFS installation failed.")

        if result.stderr:
            print()
            print(result.stderr.strip())

        return False

    print()
    print("Debian RootFS installed successfully.")
    return True


def build():
    return install()


def update():
    if not proot_distro_available():
        print("ERROR: proot-distro is not installed.")
        return False

    if not distro_installed():
        print("RootFS is not installed.")
        print("Run: chill rootfs build")
        return False

    print()
    print("Updating Debian package metadata...")
    print()

    result = run(
        [
            "proot-distro",
            "login",
            DISTRO,
            "--",
            "apt-get",
            "update",
        ],
        timeout=600,
    )

    if result is None:
        print("ERROR: RootFS update timed out.")
        return False

    if result.returncode != 0:
        print("ERROR: RootFS update failed.")

        if result.stderr:
            print(result.stderr.strip())

        return False

    print()
    print("RootFS package metadata updated.")
    return True


def login():
    if not proot_distro_available():
        print("ERROR: proot-distro is not installed.")
        return False

    if not distro_installed():
        print("RootFS is not installed.")
        print("Run: chill rootfs build")
        return False

    print("Starting ChillOS Debian environment...")

    result = subprocess.run(
        [
            "proot-distro",
            "login",
            DISTRO,
        ]
    )

    return result.returncode == 0


def status():
    ensure_directories()

    print()
    print("╔════════════════════════════════════════╗")
    print("║           CHILLOS ROOTFS STATUS        ║")
    print("╚════════════════════════════════════════╝")
    print()

    print(f"Distribution : {DISTRO}")
    print(f"Architecture : {architecture()}")
    print(f"RootFS home  : {ROOTFS_DIR}")
    print()

    if command_exists("proot"):
        print("PRoot         : AVAILABLE")
    else:
        print("PRoot         : MISSING")

    if proot_distro_available():
        print("proot-distro  : AVAILABLE")
    else:
        print("proot-distro  : MISSING")

    if distro_installed():
        print("Debian        : INSTALLED")
    else:
        print("Debian        : NOT INSTALLED")

    if rootfs_ready():
        print("RootFS        : READY")
    else:
        print("RootFS        : NOT READY")

    print()

    if rootfs_ready():
        print("Environment   : READY")
    elif not proot_distro_available():
        print("Environment   : MISSING DEPENDENCY")
    else:
        print("Environment   : NOT READY")

    print()


def remove():
    print()
    print("RootFS removal is intentionally disabled.")
    print()
    print("ChillOS will not automatically delete a Debian")
    print("environment because that could destroy user data.")
    print()
    print("Use proot-distro directly if you intentionally")
    print("want to remove the Debian environment.")
    print()


def usage():
    print("""
ChillOS RootFS

Usage:

  chill rootfs build
      Install the Debian RootFS.

  chill rootfs status
      Display RootFS and PRoot status.

  chill rootfs update
      Update Debian package metadata.

  chill rootfs login
      Enter the Debian environment.

  chill rootfs remove
      Display safe removal information.
""")


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    if not args:
        status()
        return 0

    command = args[0].lower()

    if command in ("build", "install"):
        return 0 if build() else 1

    if command == "status":
        status()
        return 0

    if command == "update":
        return 0 if update() else 1

    if command in ("login", "start"):
        return 0 if login() else 1

    if command == "remove":
        remove()
        return 0

    if command in ("help", "-h", "--help"):
        usage()
        return 0

    print(f"Unknown rootfs command: {command}")
    usage()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
