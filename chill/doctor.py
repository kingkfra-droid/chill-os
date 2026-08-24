#!/usr/bin/env python3

import os
import platform
import shutil
import subprocess
from pathlib import Path

from .architecture import detect


VERSION = "0.1.0"

CHILLOS_HOME = Path.home() / ".chillos"
WORKSPACE = CHILLOS_HOME / "workspace"


def command_exists(command):
    return shutil.which(command) is not None


def run(command, timeout=5):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def check_termux():
    prefix = os.environ.get("PREFIX", "")
    termux_version = os.environ.get("TERMUX_VERSION", "")

    return (
        "com.termux" in prefix
        or "termux" in prefix.lower()
        or bool(termux_version)
    )


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
    if command_exists("ip"):
        return "available"

    if command_exists("ifconfig"):
        return "available"

    return "limited"


def check_root():
    su = shutil.which("su")

    if not su:
        return False

    try:
        result = subprocess.run(
            [su, "-c", "id"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3,
        )

        return result.returncode == 0

    except Exception:
        return False


def check_proot():
    return (
        command_exists("proot")
        or command_exists("proot-distro")
    )


def check_rootfs():
    if not command_exists("proot-distro"):
        return False

    try:
        result = subprocess.run(
            [
                "proot-distro",
                "login",
                "debian",
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


def check_chillos_directories():
    required = [
        CHILLOS_HOME,
        WORKSPACE,
    ]

    return all(path.exists() for path in required)


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


def result_line(name, state, detail=""):
    label = {
        "OK": "[ OK ]",
        "WARN": "[WARN]",
        "ERROR": "[ ERR]",
    }.get(state, "[ ? ]")

    if detail:
        print(f"{label:<8} {name:<18} {detail}")
    else:
        print(f"{label:<8} {name}")


def main():
    print()
    print("╔════════════════════════════════════════╗")
    print("║            CHILLOS DOCTOR              ║")
    print("╚════════════════════════════════════════╝")
    print()

    problems = []
    warnings = []

    try:
        arch = detect()
    except Exception as exc:
        arch = {
            "machine": platform.machine(),
            "cpu_capability": "unknown",
            "android_abi": "unknown",
            "android_abi64": False,
            "userspace": platform.architecture()[0],
            "target": "unknown",
        }

        problems.append(
            f"Architecture detection failed: {exc}"
        )

    print("[ SYSTEM ]")
    print(f"Architecture  : {arch.get('machine', 'unknown')}")
    print(
        f"CPU capability: "
        f"{arch.get('cpu_capability', 'unknown')}"
    )
    print(
        f"Android ABI   : "
        f"{arch.get('android_abi', 'unknown')}"
    )
    print(
        f"64-bit ABI    : "
        f"{arch.get('android_abi64', 'unknown')}"
    )
    print(
        f"Userspace     : "
        f"{arch.get('userspace', 'unknown')}"
    )
    print(
        f"ChillOS target: "
        f"{arch.get('target', 'unknown')}"
    )
    print(f"Python        : {platform.python_version()}")
    print(f"Kernel        : {platform.release()}")
    print()

    print("[ ENVIRONMENT ]")

    termux = check_termux()

    if termux:
        result_line("Termux", "OK", "detected")
    else:
        result_line(
            "Termux",
            "ERROR",
            "not detected",
        )
        problems.append("Termux was not detected.")

    if check_chillos_directories():
        result_line(
            "ChillOS directories",
            "OK",
            str(CHILLOS_HOME),
        )
    else:
        result_line(
            "ChillOS directories",
            "WARN",
            "missing",
        )
        warnings.append(
            "ChillOS directories are missing."
        )

    print()

    print("[ STORAGE ]")
    print(f"Storage       : {check_storage()}")
    print()

    print("[ NETWORK ]")

    network = check_network()

    if network == "available":
        result_line("Network tools", "OK", network)
    else:
        result_line("Network tools", "WARN", network)
        warnings.append(
            "No ip or ifconfig command was found."
        )

    print()

    print("[ PRIVILEGES ]")

    if check_root():
        result_line(
            "Android root",
            "OK",
            "available",
        )
    else:
        result_line(
            "Android root",
            "WARN",
            "not available",
        )
        warnings.append(
            "Android root access is not available."
        )

    print()

    print("[ PROOT / ROOTFS ]")

    if check_proot():
        result_line(
            "PRoot",
            "OK",
            "available",
        )
    else:
        result_line(
            "PRoot",
            "ERROR",
            "missing",
        )
        problems.append(
            "PRoot/proot-distro is missing."
        )

    rootfs = check_rootfs()

    if rootfs:
        result_line(
            "Debian RootFS",
            "OK",
            "ready",
        )
    elif command_exists("proot-distro"):
        result_line(
            "Debian RootFS",
            "WARN",
            "not ready",
        )
        warnings.append(
            "Debian RootFS is not ready."
        )
    else:
        result_line(
            "Debian RootFS",
            "WARN",
            "cannot check",
        )

    print()

    print("[ COMPONENTS ]")

    packages = check_packages()

    for name, available in packages.items():
        if available:
            result_line(name, "OK", "installed")
        else:
            result_line(name, "WARN", "missing")
            warnings.append(
                f"Required command missing: {name}"
            )

    print()

    print("[ RESULT ]")

    target = arch.get("target", "unknown")

    if target == "unknown":
        result_line(
            "Architecture",
            "ERROR",
            "unsupported/unknown",
        )
        problems.append(
            "No supported ChillOS architecture target was detected."
        )
    else:
        result_line(
            "Architecture",
            "OK",
            target,
        )

    if not termux:
        result_line(
            "Environment",
            "ERROR",
            "Termux required",
        )
    elif problems:
        result_line(
            "Environment",
            "ERROR",
            "problems detected",
        )
    elif warnings:
        result_line(
            "Environment",
            "WARN",
            "usable with warnings",
        )
    else:
        result_line(
            "Environment",
            "OK",
            "healthy",
        )

    if problems:
        print()
        print("Errors:")
        for problem in problems:
            print(f"  - {problem}")

    if warnings:
        print()
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if problems:
        print()
        print("Suggested actions:")
        print("  1. Run: chill doctor")
        print("  2. Check your Termux installation.")
        print("  3. Install missing dependencies.")
        print("  4. Run: chill rootfs status")

    elif warnings:
        print()
        print("Suggested actions:")
        print("  1. Review the warnings above.")
        print("  2. Run: chill rootfs status")
        print("  3. Run: chill system")

    else:
        print()
        print("ChillOS environment looks healthy.")

    print()
    print("Doctor scan complete.")
    print()

    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
