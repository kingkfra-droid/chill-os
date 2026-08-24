#!/usr/bin/env python3

import os
import platform
import shutil


VERSION = "0.1.0"

CHILLOS_HOME = os.path.expanduser("~/.chillos")
WORKSPACE = os.path.join(CHILLOS_HOME, "workspace")


def initialize():
    """Create the basic ChillOS filesystem structure."""

    os.makedirs(WORKSPACE, exist_ok=True)

    for directory in (
        "home",
        "etc",
        "var",
        "tmp",
        "packages",
        "logs",
        "cache",
    ):
        os.makedirs(
            os.path.join(WORKSPACE, directory),
            exist_ok=True,
        )

    return WORKSPACE


def is_termux():
    """Detect whether ChillOS is running inside Termux."""

    prefix = os.environ.get("PREFIX", "")
    termux_version = os.environ.get("TERMUX_VERSION", "")

    return (
        "com.termux" in prefix
        or "termux" in prefix.lower()
        or bool(termux_version)
    )


def android_abi():
    """Return the Android CPU ABI when available."""

    abi = os.environ.get("ANDROID_ABI")

    if abi:
        return abi

    getprop = shutil.which("getprop")

    if getprop:
        try:
            import subprocess

            value = subprocess.check_output(
                [getprop, "ro.product.cpu.abi"],
                text=True,
                stderr=subprocess.DEVNULL,
                timeout=3,
            ).strip()

            if value:
                return value

        except Exception:
            pass

    return "unknown"


def root_access():
    """Check whether usable Android root access is available."""

    su = shutil.which("su")

    if not su:
        return False

    try:
        import subprocess

        result = subprocess.run(
            [su, "-c", "id"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=3,
        )

        return result.returncode == 0

    except Exception:
        return False


def proot_available():
    """Check whether PRoot or proot-distro is installed."""

    return bool(
        shutil.which("proot")
        or shutil.which("proot-distro")
    )


def rootfs_status():
    """Check whether the ChillOS Debian rootfs is available."""

    proot_distro = shutil.which("proot-distro")

    if not proot_distro:
        return "UNAVAILABLE"

    try:
        import subprocess

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

        if result.returncode == 0:
            return "READY"

    except Exception:
        pass

    return "NOT INSTALLED"


def storage_info():
    """Return available and total storage."""

    try:
        usage = shutil.disk_usage(CHILLOS_HOME)

        total = usage.total // (1024 ** 3)
        free = usage.free // (1024 ** 3)

        return f"{free} GB free / {total} GB total"

    except Exception:
        return "unknown"


def environment_state():
    """Collect current ChillOS environment information."""

    initialize()

    return {
        "version": VERSION,
        "home": CHILLOS_HOME,
        "workspace": WORKSPACE,
        "termux": is_termux(),
        "architecture": platform.machine(),
        "kernel": platform.release(),
        "python": platform.python_version(),
        "android_abi": android_abi(),
        "proot": proot_available(),
        "root": root_access(),
        "rootfs": rootfs_status(),
        "storage": storage_info(),
    }


def status():
    """Display the ChillOS environment dashboard."""

    info = environment_state()

    print()
    print("╔════════════════════════════════════════╗")
    print("║           CHILLOS STATUS               ║")
    print("╚════════════════════════════════════════╝")
    print()

    print(f"ChillOS       : {info['version']}")
    print(f"Architecture  : {info['architecture']}")
    print(f"Android ABI   : {info['android_abi']}")
    print(f"Kernel        : {info['kernel']}")
    print(f"Python        : {info['python']}")
    print()

    print(
        "Termux        : "
        f"{'YES' if info['termux'] else 'NO'}"
    )

    print(
        "Root access   : "
        f"{'YES' if info['root'] else 'NO'}"
    )

    print(
        "PRoot          : "
        f"{'AVAILABLE' if info['proot'] else 'MISSING'}"
    )

    print(f"RootFS        : {info['rootfs']}")
    print()

    print(f"ChillOS home  : {info['home']}")
    print(f"Workspace     : {info['workspace']}")
    print(f"Storage       : {info['storage']}")
    print()

    if (
        info["termux"]
        and info["proot"]
        and info["rootfs"] == "READY"
    ):
        print("Environment   : READY")

    elif not info["termux"]:
        print("Environment   : ANDROID/TERMUX NOT DETECTED")

    elif not info["proot"]:
        print("Environment   : PRoot NOT AVAILABLE")

    elif info["rootfs"] != "READY":
        print("Environment   : ROOTFS NOT READY")

    else:
        print("Environment   : PARTIALLY READY")

    print()


def reset_workspace():
    """Remove and recreate the ChillOS workspace."""

    import shutil as _shutil

    if os.path.exists(WORKSPACE):
        _shutil.rmtree(WORKSPACE)

    return initialize()


if __name__ == "__main__":
    status()
