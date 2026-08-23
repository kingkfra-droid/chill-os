#!/usr/bin/env python3

import platform
import shutil
import subprocess


def getprop(name):
    if shutil.which("getprop") is None:
        return "unknown"

    try:
        value = subprocess.check_output(
            ["getprop", name],
            text=True
        ).strip()

        return value or "unknown"

    except Exception:
        return "unknown"


def kernel_version():
    try:
        import subprocess

        result = subprocess.run(
            ["uname", "-r"],
            capture_output=True,
            text=True,
            timeout=5
        )

        value = result.stdout.strip()

        if value:
            return value

    except Exception:
        pass

    return "unknown"


def system_info():
    return {
        "name": "ChillOS",
        "version": "0.2.0",

        "device":
            getprop("ro.product.model"),

        "manufacturer":
            getprop("ro.product.manufacturer"),

        "android":
            getprop("ro.build.version.release"),

        "architecture":
            platform.machine(),

        "abi":
            getprop("ro.product.cpu.abi"),

        "abis":
            getprop("ro.product.cpu.abilist"),

        "kernel":
            kernel_version(),

        "python":
            platform.python_version(),

        "proot":
            shutil.which("proot-distro") is not None
    }
