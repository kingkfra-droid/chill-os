#!/usr/bin/env python3

import os
import platform
import shutil
import subprocess

from .architecture import detect


def command_exists(command):
    return shutil.which(command) is not None


def run(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=3,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def check_termux():
    prefix = os.environ.get("PREFIX", "")
    return "com.termux" in prefix


def check_storage():
    try:
        stat = os.statvfs(os.path.expanduser("~"))
        total = stat.f_frsize * stat.f_blocks
        free = stat.f_frsize * stat.f_bavail

        return (
            f"{free / (1024**3):.2f} GB free / "
            f"{total / (1024**3):.2f} GB total"
        )
    except Exception:
        return "unknown"


def check_network():
    return "available" if command_exists("ip") else "limited"


def check_packages():
    packages = [
        "python",
        "git",
        "proot",
        "proot-distro",
        "curl",
        "wget",
        "tar",
        "xz",
    ]

    return {
        package: command_exists(package)
        for package in packages
    }


def main():
    arch = detect()

    print()
    print("CHILLOS DOCTOR")
    print("=" * 40)

    print()
    print("[ SYSTEM ]")
    print(f"Architecture  : {arch['machine']}")
    print(f"CPU capability: {arch['cpu_capability']}")
    print(f"Android ABI   : {arch['android_abi']}")
    print(f"64-bit ABI    : {arch['android_abi64']}")
    print(f"Userspace     : {arch['userspace']}")
    print(f"ChillOS target: {arch['target']}")
    print(f"Python        : {platform.python_version()}")
    print(f"Termux        : {'YES' if check_termux() else 'NO'}")
    print(f"Storage       : {check_storage()}")

    print()
    print("[ NETWORK ]")
    print(f"Network       : {check_network()}")

    print()
    print("[ COMPONENTS ]")

    packages = check_packages()

    for name, available in packages.items():
        print(f"{name:<14} {'OK' if available else 'MISSING'}")

    print()
    print("[ RESULT ]")

    if not check_termux():
        print("Environment   : Termux not detected")
    elif arch["target"] == "unknown":
        print("Environment   : architecture unsupported")
    else:
        print("Environment   : compatible")
        print(f"Rootfs target : Debian {arch['target']}")

    missing = [
        name for name, available in packages.items()
        if not available
    ]

    if missing:
        print()
        print("Missing:")
        for item in missing:
            print(f"  - {item}")

    print()
    print("Doctor scan complete.")
    print()


if __name__ == "__main__":
    main()
