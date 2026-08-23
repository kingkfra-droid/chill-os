#!/usr/bin/env python3

import shutil
import subprocess
import sys

from .architecture import detect

DISTRO = "debian"


def check_proot_distro():
    return shutil.which("proot-distro") is not None


def container_exists():
    """
    Verify the container by asking proot-distro to enter it.
    We do NOT parse `proot-distro list`.
    """

    try:
        result = subprocess.run(
            [
                "proot-distro",
                "login",
                DISTRO,
                "--",
                "true",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
        )

        return result.returncode == 0

    except Exception:
        return False


def target_arch():
    return detect()["target"]


def build():
    target = target_arch()

    print()
    print("CHILLOS ROOTFS")
    print("=" * 40)
    print(f"Distribution : Debian 13")
    print(f"Target       : {target}")
    print(f"Backend      : PRoot")
    print()

    if not check_proot_distro():
        print("ERROR: proot-distro is not installed.")
        print()
        print("Install with:")
        print("  pkg install proot-distro")
        return 1

    if target == "unknown":
        print("ERROR: Unsupported ChillOS architecture.")
        return 1

    print("Checking existing Debian container...")

    if container_exists():
        print()
        print("Debian container: FOUND")
        print("No installation required.")
        print()
        print("ChillOS rootfs: READY")
        print(f"Architecture: {target}")
        return 0

    print()
    print("Debian container: NOT FOUND")
    print("Installing Debian...")
    print()

    result = subprocess.run(
        ["proot-distro", "install", DISTRO]
    )

    if result.returncode != 0:
        print()
        print("ERROR: Debian installation failed.")
        return result.returncode

    print()
    print("Debian installation complete.")
    print(f"ChillOS architecture: {target}")

    return 0


def status():
    info = detect()

    print()
    print("CHILLOS ROOTFS")
    print("=" * 40)
    print(f"CPU capability : {info['cpu_capability']}")
    print(f"Android ABI    : {info['android_abi']}")
    print(f"Userspace      : {info['userspace']}")
    print(f"ChillOS target : {info['target']}")
    print(f"Distribution   : Debian 13")
    print(f"Backend        : PRoot")

    if not check_proot_distro():
        print("Installed      : NO")
        return 1

    installed = container_exists()

    print(f"Installed      : {'YES' if installed else 'NO'}")
    print()


def usage():
    print("""
Usage:
  chill rootfs status
  chill rootfs build
""")


def main():
    # Works both through:
    #
    #   chill rootfs build
    #
    # and directly:
    #
    #   python -m chill.rootfs build

    if len(sys.argv) >= 3 and sys.argv[1] == "rootfs":
        command = sys.argv[2]

    elif len(sys.argv) >= 2:
        command = sys.argv[1]

    else:
        usage()
        return 1

    if command == "build":
        return build()

    if command == "status":
        return status()

    print(f"Unknown rootfs command: {command}")
    usage()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
